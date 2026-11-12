CREATE TABLE IF NOT EXISTS public.research_faculty (
    faculty_id UUID PRIMARY KEY,
    faculty_name TEXT NOT NULL,
    department TEXT NOT NULL,
    designation TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT research_faculty_name_nonempty CHECK (length(trim(faculty_name)) > 0),
    CONSTRAINT research_faculty_department_nonempty CHECK (length(trim(department)) > 0),
    CONSTRAINT research_faculty_designation_nonempty CHECK (length(trim(designation)) > 0)
);

CREATE TABLE IF NOT EXISTS public.faculty_research_records (
    id UUID PRIMARY KEY,
    faculty_id UUID NOT NULL REFERENCES public.research_faculty(faculty_id) ON DELETE CASCADE,
    academic_year TEXT NOT NULL,
    publications INTEGER NOT NULL DEFAULT 0 CHECK (publications >= 0),
    citations INTEGER NOT NULL DEFAULT 0 CHECK (citations >= 0),
    research_grants NUMERIC(14, 2) NOT NULL DEFAULT 0 CHECK (research_grants >= 0),
    mentorship_score NUMERIC(4, 2),
    faculty_rating NUMERIC(4, 2),
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT faculty_research_academic_year_format
        CHECK (academic_year ~ '^[0-9]{4}-[0-9]{2}$'),
    CONSTRAINT faculty_research_mentorship_range
        CHECK (mentorship_score IS NULL OR mentorship_score BETWEEN 1 AND 5),
    CONSTRAINT faculty_research_rating_range
        CHECK (faculty_rating IS NULL OR faculty_rating BETWEEN 1 AND 5),
    CONSTRAINT faculty_research_one_record_per_year UNIQUE (faculty_id, academic_year)
);

CREATE INDEX IF NOT EXISTS research_faculty_department_active_idx
    ON public.research_faculty (department, is_active);
CREATE INDEX IF NOT EXISTS faculty_research_records_faculty_idx
    ON public.faculty_research_records (faculty_id);
CREATE INDEX IF NOT EXISTS faculty_research_records_year_idx
    ON public.faculty_research_records (academic_year);

CREATE OR REPLACE FUNCTION public.can_read_research_department(target_department TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public
AS $$
    WITH jwt_identity AS (
        SELECT
            lower(coalesce(auth.jwt() ->> 'email', '')) AS email,
            upper(coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '')) AS app_role,
            upper(coalesce(auth.jwt() -> 'app_metadata' ->> 'department_id', '')) AS app_department
    ),
    resolved AS (
        SELECT
            email,
            app_role,
            CASE
                WHEN app_department <> '' THEN app_department
                WHEN email LIKE 'hod.bt@%' THEN 'BT'
                WHEN email LIKE 'hod.%@%' THEN upper(split_part(split_part(email, '@', 1), '.', 2))
                WHEN email LIKE 'hod-%@%' THEN upper(split_part(split_part(email, '@', 1), '-', 2))
                ELSE ''
            END AS department
        FROM jwt_identity
    )
    SELECT CASE
        WHEN app_role IN ('ADMIN', 'ADMINISTRATOR')
            OR email IN ('admin@institution.edu', 'administrator@institution.edu')
            THEN TRUE
        WHEN app_role = 'HOD' OR email LIKE 'hod.%@%' OR email LIKE 'hod-%@%'
            THEN CASE
                WHEN department = 'BT' THEN lower(target_department) = 'biotech'
                ELSE upper(target_department) = department
            END
        ELSE FALSE
    END
    FROM resolved
$$;

REVOKE ALL ON FUNCTION public.can_read_research_department(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.can_read_research_department(TEXT) TO authenticated;

ALTER TABLE public.research_faculty ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faculty_research_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS research_faculty_scoped_read ON public.research_faculty;
CREATE POLICY research_faculty_scoped_read
    ON public.research_faculty
    FOR SELECT
    TO authenticated
    USING (public.can_read_research_department(department));

DROP POLICY IF EXISTS faculty_research_records_scoped_read ON public.faculty_research_records;
CREATE POLICY faculty_research_records_scoped_read
    ON public.faculty_research_records
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.research_faculty AS faculty
            WHERE faculty.faculty_id = faculty_research_records.faculty_id
              AND public.can_read_research_department(faculty.department)
        )
    );

GRANT SELECT ON public.research_faculty, public.faculty_research_records TO authenticated;
