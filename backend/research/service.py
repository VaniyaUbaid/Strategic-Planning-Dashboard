from pathlib import Path
import logging
import math
import re
from threading import Lock
from typing import Optional

import pandas as pd

from backend.common.supabase_client import (
    SupabaseConfigurationError,
    get_supabase_client_for_access_token,
)
from backend.research.schemas import (
    DepartmentResearch,
    FacultyPublicationTrend,
    FacultyDepartmentPublicationTrend,
    FacultyResearchAnalyticsResponse,
    FacultyResearchDepartment,
    FacultyResearchOverview,
    FacultyResearcher,
    ProgramResearch,
    PublicationDistribution,
    ResearchDepartmentResponse,
    ResearchFilterOptionsResponse,
    ResearchOverviewResponse,
    ResearchParticipationDistribution,
    ResearchParticipationResponse,
    ResearchProgramResponse,
    ResearchPublicationResponse,
    ResearchStatusResponse,
)

logger = logging.getLogger(__name__)
_ACADEMIC_YEAR_PATTERN = re.compile(r"^\d{4}-\d{2}$")
_SAFE_ERROR_CODE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_API_KEY_PATTERN = re.compile(r"\bsb_(?:secret|publishable)_[A-Za-z0-9_-]+\b")
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+\S+")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _safe_database_error(exc: Exception) -> tuple[Optional[int], str, str]:
    status_code = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    if not isinstance(status_code, int):
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
    if not isinstance(status_code, int):
        try:
            status_code = int(status_code)
        except (TypeError, ValueError):
            status_code = None

    code = getattr(exc, "code", None)
    if not isinstance(code, str) or not _SAFE_ERROR_CODE.fullmatch(code):
        code = "unknown"

    message = getattr(exc, "message", None) or str(exc)
    message = _BEARER_PATTERN.sub("Bearer [REDACTED]", str(message))
    message = _TOKEN_PATTERN.sub("[REDACTED_TOKEN]", message)
    message = _API_KEY_PATTERN.sub("[REDACTED_API_KEY]", message)
    message = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", message)
    return status_code, code, " ".join(message.split())[:400]


class ResearchDataError(Exception):
    """Raised when the Research dataset cannot be loaded or validated."""


class ResearchAccessError(ResearchDataError):
    """Raised when Supabase RLS denies faculty research access."""


class ResearchService:
    REQUIRED_COLUMNS = {
        "Department",
        "Program",
        "Research_Participation",
        "Publications",
        "Faculty_Rating",
        "Mentorship_Score",
        "Infrastructure_Rating",
        "Admission_Year",
    }
    POSITIVE_PARTICIPATION = {
        "1", "true", "yes", "y", "participant", "participating", "active",
    }
    NEGATIVE_PARTICIPATION = {
        "0", "false", "no", "n", "non-participant", "nonparticipant",
        "not participating", "inactive",
    }

    def __init__(self, data_path: Optional[Path] = None):
        self.project_root = Path(__file__).resolve().parents[2]
        self.data_path = Path(data_path) if data_path else None
        self._dataframe = None
        self._load_lock = Lock()

    def _resolve_data_path(self) -> Path:
        if self.data_path is not None:
            return self.data_path

        candidates = (
            self.project_root / "data" / "research" / "preprocessed_strategic_planning.csv",
            # Keep compatibility with the dataset's current repository location.
            self.project_root / "data" / "student" / "research" / "preprocessed_strategic_planning.csv",
        )
        return next((path for path in candidates if path.is_file()), candidates[0])

    def _get_dataframe(self) -> pd.DataFrame:
        if self._dataframe is not None:
            return self._dataframe

        with self._load_lock:
            if self._dataframe is not None:
                return self._dataframe

            path = self._resolve_data_path()
            if not path.is_file():
                raise ResearchDataError("Research dataset is not available.")
            try:
                dataframe = pd.read_csv(path)
            except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
                raise ResearchDataError("Research dataset could not be read.") from exc

            missing_columns = self.REQUIRED_COLUMNS.difference(dataframe.columns)
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ResearchDataError(f"Research dataset is missing required columns: {missing}.")

            dataframe = dataframe.copy()
            for column in (
                "Publications", "Faculty_Rating", "Mentorship_Score",
                "Infrastructure_Rating", "Admission_Year",
            ):
                dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
            dataframe["_participation"] = dataframe["Research_Participation"].map(
                self._normalize_participation
            )
            self._dataframe = dataframe
            return dataframe

    @classmethod
    def _normalize_participation(cls, value) -> str:
        if pd.isna(value) or not str(value).strip():
            return "Unknown"
        clean = " ".join(str(value).strip().lower().replace("_", " ").split())
        if clean in cls.POSITIVE_PARTICIPATION:
            return "Participating"
        if clean in cls.NEGATIVE_PARTICIPATION:
            return "Not participating"
        # Preserve unrecognized source categories rather than forcing them into yes/no.
        return str(value).strip()

    def _filtered_dataframe(
        self,
        department: Optional[str] = None,
        program: Optional[str] = None,
        admission_year: Optional[int] = None,
    ) -> pd.DataFrame:
        filtered = self._get_dataframe()
        if department and department.strip():
            filtered = filtered[filtered["Department"].astype(str).str.casefold() == department.strip().casefold()]
        if program and program.strip():
            filtered = filtered[filtered["Program"].astype(str).str.casefold() == program.strip().casefold()]
        if admission_year is not None:
            filtered = filtered[filtered["Admission_Year"] == admission_year]
        return filtered

    @staticmethod
    def _mean(dataframe: pd.DataFrame, column: str) -> Optional[float]:
        values = dataframe[column].dropna()
        if values.empty:
            return None
        return round(float(values.mean()), 2)

    @classmethod
    def _metrics(cls, dataframe: pd.DataFrame) -> dict:
        total_students = len(dataframe)
        publications = dataframe["Publications"].dropna()
        participants = int((dataframe["_participation"] == "Participating").sum())
        return {
            "total_students": total_students,
            "research_participants": participants,
            "research_participation_rate": round(participants / total_students * 100, 2) if total_students else 0.0,
            "total_publications": int(publications.sum()),
            "average_publications": round(float(publications.mean()), 2) if not publications.empty else 0.0,
            "students_with_publications": int((publications > 0).sum()),
            "average_faculty_rating": cls._mean(dataframe, "Faculty_Rating"),
            "average_mentorship_score": cls._mean(dataframe, "Mentorship_Score"),
            "average_infrastructure_rating": cls._mean(dataframe, "Infrastructure_Rating"),
        }

    def get_status(self) -> ResearchStatusResponse:
        """Report whether a valid local Research dataset is available."""
        try:
            self._get_dataframe()
        except ResearchDataError:
            return ResearchStatusResponse(module="research", status="not_ready")
        return ResearchStatusResponse(module="research", status="ready")

    def get_overview(self, department=None, program=None, admission_year=None) -> ResearchOverviewResponse:
        return ResearchOverviewResponse(**self._metrics(self._filtered_dataframe(department, program, admission_year)))

    def get_departments(self, department=None, program=None, admission_year=None) -> ResearchDepartmentResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        rows = []
        for name, group in dataframe.groupby("Department", dropna=True, sort=True):
            metrics = self._metrics(group)
            rows.append(DepartmentResearch(
                department=str(name),
                total_students=metrics["total_students"],
                research_participants=metrics["research_participants"],
                participation_rate=metrics["research_participation_rate"],
                total_publications=metrics["total_publications"],
                average_publications=metrics["average_publications"],
                average_faculty_rating=metrics["average_faculty_rating"],
                average_mentorship_score=metrics["average_mentorship_score"],
                average_infrastructure_rating=metrics["average_infrastructure_rating"],
            ))
        return ResearchDepartmentResponse(departments=rows)

    def get_programs(self, department=None, program=None, admission_year=None) -> ResearchProgramResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        rows = []
        for name, group in dataframe.groupby("Program", dropna=True, sort=True):
            metrics = self._metrics(group)
            rows.append(ProgramResearch(
                program=str(name),
                total_students=metrics["total_students"],
                research_participants=metrics["research_participants"],
                participation_rate=metrics["research_participation_rate"],
                total_publications=metrics["total_publications"],
                average_publications=metrics["average_publications"],
            ))
        return ResearchProgramResponse(programs=rows)

    def get_publications(self, department=None, program=None, admission_year=None) -> ResearchPublicationResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        values = dataframe["Publications"].dropna()
        if values.empty:
            return ResearchPublicationResponse(distribution=[])

        maximum = int(values.max())
        if maximum <= 5:
            buckets = [(value, f"{value} publication{'s' if value != 1 else ''}") for value in range(maximum + 1)]
        else:
            buckets = [(value, f"{value} publication{'s' if value != 1 else ''}") for value in range(5)]
            buckets.append((5, "5+ publications"))

        distribution = []
        for lower_bound, label in buckets:
            if label == "5+ publications":
                count = int((values >= lower_bound).sum())
            else:
                count = int((values == lower_bound).sum())
            distribution.append(PublicationDistribution(bucket=label, count=count))
        if dataframe["Publications"].isna().any():
            distribution.append(PublicationDistribution(bucket="Missing", count=int(dataframe["Publications"].isna().sum())))
        return ResearchPublicationResponse(distribution=distribution)

    def get_participation(self, department=None, program=None, admission_year=None) -> ResearchParticipationResponse:
        dataframe = self._filtered_dataframe(department, program, admission_year)
        counts = dataframe["_participation"].value_counts(dropna=False, sort=False)
        distribution = [
            ResearchParticipationDistribution(category=str(category), count=int(count))
            for category, count in counts.items()
        ]
        return ResearchParticipationResponse(distribution=distribution)

    def get_filter_options(self) -> ResearchFilterOptionsResponse:
        dataframe = self._get_dataframe()
        years = dataframe["Admission_Year"].dropna().astype(int).unique().tolist()
        return ResearchFilterOptionsResponse(
            departments=sorted(dataframe["Department"].dropna().astype(str).unique().tolist()),
            programs=sorted(dataframe["Program"].dropna().astype(str).unique().tolist()),
            admission_years=sorted(years),
        )

    @staticmethod
    def _query_all_rows(client, table_name, columns, department=None, faculty_ids=None):
        rows = []
        start = 0
        page_size = 1000
        while True:
            query = client.table(table_name).select(columns)
            if department and table_name == "research_faculty":
                query = query.ilike("department", department)
            if faculty_ids and table_name == "faculty_research_records":
                query = query.in_("faculty_id", faculty_ids)
            response = query.range(start, start + page_size - 1).execute()
            page = response.data or []
            rows.extend(page)
            if len(page) < page_size:
                return rows
            start += page_size

    @staticmethod
    def _canonical_department(department):
        if not department:
            return None
        clean = str(department).strip()
        if clean.upper() == "BT":
            return "Biotech"
        return clean

    @staticmethod
    def _required_integer(row, field):
        value = row.get(field)
        try:
            number = int(value)
            if isinstance(value, bool) or float(value) != number:
                raise ValueError
            return number
        except (TypeError, ValueError, OverflowError):
            raise ResearchDataError(
                f"Faculty research data contains an invalid {field} value."
            ) from None

    @staticmethod
    def _required_amount(row, field):
        value = row.get(field)
        try:
            amount = float(value)
            if not math.isfinite(amount):
                raise ValueError
            return amount
        except (TypeError, ValueError, OverflowError):
            raise ResearchDataError(
                f"Faculty research data contains an invalid {field} value."
            ) from None

    def get_faculty_analytics(
        self,
        department: Optional[str] = None,
        academic_year: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> FacultyResearchAnalyticsResponse:
        """Return faculty analytics while retaining active zero-output faculty in denominators."""
        selected_department = self._canonical_department(department)
        if academic_year and not _ACADEMIC_YEAR_PATTERN.fullmatch(academic_year):
            raise ResearchDataError("Academic year must use the YYYY-YY format.")

        try:
            client = get_supabase_client_for_access_token(access_token)
            faculty_rows = self._query_all_rows(
                client,
                "research_faculty",
                "faculty_id,faculty_name,department,designation,is_active,is_synthetic",
                department=selected_department,
            )
            active_faculty = [
                row for row in faculty_rows
                if row.get("is_active") is True
                and (
                    not selected_department
                    or str(row.get("department", "")).casefold()
                    == selected_department.casefold()
                )
            ]
            active_ids = {str(row["faculty_id"]) for row in active_faculty}
            record_rows = (
                self._query_all_rows(
                    client,
                    "faculty_research_records",
                    "id,faculty_id,academic_year,publications,citations,research_grants,"
                    "mentorship_score,faculty_rating,is_synthetic",
                    faculty_ids=sorted(active_ids),
                )
                if active_ids
                else []
            )
        except SupabaseConfigurationError as exc:
            logger.error(
                "Faculty research Supabase client is unavailable (error_type=%s, message=%s)",
                type(exc).__name__,
                str(exc),
            )
            raise ResearchDataError(
                f"Faculty research database client is unavailable: {exc}"
            ) from None
        except Exception as exc:
            response_status, error_code, safe_message = _safe_database_error(exc)
            if response_status in (401, 403) or error_code in {
                "42501",
                "PGRST301",
                "PGRST302",
            }:
                logger.warning(
                    "Faculty research access denied (error_type=%s, code=%s, status=%s, message=%s)",
                    type(exc).__name__,
                    error_code,
                    response_status if response_status is not None else "unknown",
                    safe_message,
                )
                raise ResearchAccessError(
                    "Faculty research access is denied by the current Supabase authorization policies."
                ) from None
            logger.error(
                "Faculty research read failed (error_type=%s, code=%s, status=%s, message=%s)",
                type(exc).__name__,
                error_code,
                response_status if response_status is not None else "unknown",
                safe_message,
            )
            raise ResearchDataError(
                "Faculty research data could not be read "
                f"(status={response_status or 'unknown'}, code={error_code}): {safe_message}"
            ) from None

        record_rows = [
            row for row in record_rows
            if str(row.get("faculty_id")) in active_ids
        ]
        available_years = sorted({
            str(row["academic_year"])
            for row in record_rows
            if row.get("academic_year")
        })
        scoped_records = [
            row for row in record_rows
            if not academic_year or row.get("academic_year") == academic_year
        ]

        publications_by_faculty = {}
        citations_by_faculty = {}
        for row in scoped_records:
            faculty_id = str(row["faculty_id"])
            publications_by_faculty[faculty_id] = (
                publications_by_faculty.get(faculty_id, 0)
                + self._required_integer(row, "publications")
            )
            citations_by_faculty[faculty_id] = (
                citations_by_faculty.get(faculty_id, 0)
                + self._required_integer(row, "citations")
            )

        total_faculty = len(active_faculty)
        total_publications = sum(publications_by_faculty.values())
        total_citations = sum(citations_by_faculty.values())
        researchers = sum(value > 0 for value in publications_by_faculty.values())
        average_publications = (
            round(total_publications / total_faculty, 2) if total_faculty else 0.0
        )
        rating_values = [
            float(row["faculty_rating"])
            for row in scoped_records
            if row.get("faculty_rating") is not None
        ]
        mentorship_values = [
            float(row["mentorship_score"])
            for row in scoped_records
            if row.get("mentorship_score") is not None
        ]
        publishing_faculty = sum(
            value > 0 for value in publications_by_faculty.values()
        )
        overview = FacultyResearchOverview(
            selected_department=selected_department,
            selected_academic_year=academic_year,
            total_faculty=total_faculty,
            faculty_researchers=researchers,
            publishing_faculty_count=publishing_faculty,
            total_publications=total_publications,
            average_publications_per_faculty=average_publications,
            faculty_participation_rate=(
                round(researchers / total_faculty * 100, 2)
                if total_faculty else 0.0
            ),
            total_citations=total_citations,
            average_citations_per_faculty=(
                round(total_citations / total_faculty, 2)
                if total_faculty else 0.0
            ),
            average_citations_per_publishing_faculty=(
                round(total_citations / publishing_faculty, 2)
                if publishing_faculty else None
            ),
            total_research_grants=round(
                sum(self._required_amount(row, "research_grants") for row in scoped_records),
                2,
            ),
            average_faculty_rating=(
                round(sum(rating_values) / len(rating_values), 2)
                if rating_values else None
            ),
            faculty_rating_count=len(rating_values),
            average_mentorship_score=(
                round(sum(mentorship_values) / len(mentorship_values), 2)
                if mentorship_values else None
            ),
            mentorship_score_count=len(mentorship_values),
            is_synthetic=any(
                row.get("is_synthetic") is True
                for row in [*active_faculty, *scoped_records]
            ),
        )

        department_rows = []
        departments = sorted({
            str(row["department"])
            for row in active_faculty
            if row.get("department")
        })
        for department_name in departments:
            department_faculty = [
                row for row in active_faculty
                if row.get("department") == department_name
            ]
            department_ids = {str(row["faculty_id"]) for row in department_faculty}
            department_records = [
                row for row in scoped_records
                if str(row.get("faculty_id")) in department_ids
            ]
            per_faculty = {}
            for row in department_records:
                faculty_id = str(row["faculty_id"])
                per_faculty[faculty_id] = (
                    per_faculty.get(faculty_id, 0)
                    + self._required_integer(row, "publications")
                )
            dept_rating = [
                float(row["faculty_rating"])
                for row in department_records
                if row.get("faculty_rating") is not None
            ]
            dept_mentorship = [
                float(row["mentorship_score"])
                for row in department_records
                if row.get("mentorship_score") is not None
            ]
            count = len(department_faculty)
            active_researchers = sum(value > 0 for value in per_faculty.values())
            department_rows.append(FacultyResearchDepartment(
                department=department_name,
                total_faculty=count,
                faculty_researchers=active_researchers,
                publications=sum(per_faculty.values()),
                average_publications_per_faculty=(
                    round(sum(per_faculty.values()) / count, 2) if count else 0.0
                ),
                participation_rate=(
                    round(active_researchers / count * 100, 2) if count else 0.0
                ),
                total_citations=sum(
                    self._required_integer(row, "citations") for row in department_records
                ),
                research_grants=round(
                    sum(self._required_amount(row, "research_grants") for row in department_records),
                    2,
                ),
                average_faculty_rating=(
                    round(sum(dept_rating) / len(dept_rating), 2)
                    if dept_rating else None
                ),
                faculty_rating_count=len(dept_rating),
                average_mentorship_score=(
                    round(sum(dept_mentorship) / len(dept_mentorship), 2)
                    if dept_mentorship else None
                ),
                mentorship_score_count=len(dept_mentorship),
            ))

        trend_map = {}
        for row in scoped_records:
            year = str(row.get("academic_year") or "")
            if not year:
                continue
            stats = trend_map.setdefault(year, {"publications": 0, "citations": 0})
            stats["publications"] += self._required_integer(row, "publications")
            stats["citations"] += self._required_integer(row, "citations")
        publication_trends = [
            FacultyPublicationTrend(academic_year=year, **trend_map[year])
            for year in sorted(trend_map)
        ]

        faculty_by_id = {
            str(row["faculty_id"]): row for row in active_faculty
        }
        department_trend_map = {}
        for row in scoped_records:
            member = faculty_by_id.get(str(row.get("faculty_id")))
            year = str(row.get("academic_year") or "")
            department_name = str(member.get("department") or "") if member else ""
            if not year or not department_name:
                continue
            key = (department_name, year)
            department_trend_map[key] = (
                department_trend_map.get(key, 0)
                + self._required_integer(row, "publications")
            )
        department_publication_trends = [
            FacultyDepartmentPublicationTrend(
                department=department_name,
                academic_year=year,
                publications=publications,
            )
            for (department_name, year), publications in sorted(department_trend_map.items())
        ]
        top_researchers = []
        for faculty_id, count in sorted(
            publications_by_faculty.items(),
            key=lambda item: (-item[1], faculty_by_id[item[0]].get("faculty_name", "")),
        )[:10]:
            member = faculty_by_id[faculty_id]
            top_researchers.append(FacultyResearcher(
                faculty_id=faculty_id,
                faculty_name=str(member.get("faculty_name") or "Unnamed faculty"),
                department=str(member.get("department") or ""),
                publications=count,
                citations=citations_by_faculty.get(faculty_id, 0),
            ))

        return FacultyResearchAnalyticsResponse(
            overview=overview,
            departments=department_rows,
            publication_trends=publication_trends,
            department_publication_trends=department_publication_trends,
            top_researchers=top_researchers,
            available_departments=departments,
            academic_years=available_years,
            is_synthetic=overview.is_synthetic,
        )


research_service = ResearchService()
