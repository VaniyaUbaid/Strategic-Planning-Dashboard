import csv
import random
import uuid
from pathlib import Path


SEED = 41729
NAMESPACE = uuid.UUID("994d3f0b-9cdf-4f20-9257-9e8801f3a90c")
DEPARTMENTS = ("BBA", "Biotech", "CE", "CSE", "ECE", "EEE", "IT", "MBA", "ME")
ACADEMIC_YEARS = (
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26",
)
FIRST_NAMES = (
    "Aarav", "Aditi", "Akash", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya",
    "Meera", "Neel", "Nisha", "Priya", "Rahul", "Riya", "Sanjay", "Tara",
    "Vikram", "Zoya", "Dev", "Ira", "Kabir", "Maya", "Nikhil", "Sana",
)
LAST_NAMES = (
    "Agarwal", "Banerjee", "Bose", "Chandra", "Das", "Desai", "Gupta",
    "Iyer", "Jain", "Kapoor", "Khan", "Kulkarni", "Menon", "Nair",
    "Patel", "Rao", "Reddy", "Shah", "Sharma", "Singh", "Srinivasan",
    "Verma", "Joshi", "Mukherjee",
)
DESIGNATIONS = (
    "Assistant Professor",
    "Associate Professor",
    "Professor",
    "Senior Lecturer",
)
FACULTY_FIELDS = (
    "faculty_id",
    "faculty_name",
    "department",
    "designation",
    "is_active",
    "is_synthetic",
)
RECORD_FIELDS = (
    "id",
    "faculty_id",
    "academic_year",
    "publications",
    "citations",
    "research_grants",
    "mentorship_score",
    "faculty_rating",
    "is_synthetic",
)


def build_data():
    rng = random.Random(SEED)
    faculty = []
    records = []
    used_names = set()

    for index in range(100):
        faculty_id = str(uuid.uuid5(NAMESPACE, f"faculty-{index + 1:03d}"))
        first = FIRST_NAMES[index % len(FIRST_NAMES)]
        last = LAST_NAMES[(index * 7) % len(LAST_NAMES)]
        name = f"{first} {last}"
        if name in used_names:
            name = f"{name} {index + 1:03d}"
        used_names.add(name)

        faculty.append({
            "faculty_id": faculty_id,
            "faculty_name": name,
            "department": DEPARTMENTS[index % len(DEPARTMENTS)],
            "designation": DESIGNATIONS[(index * 3) % len(DESIGNATIONS)],
            "is_active": index < 96,
            "is_synthetic": True,
        })

        if index >= 96:
            continue

        zero_output_faculty = index in {5, 22, 47, 83}
        for academic_year in ACADEMIC_YEARS:
            if rng.random() > 0.76:
                continue

            publications = (
                0
                if zero_output_faculty
                else min(int(rng.expovariate(0.58)), 9)
            )
            citations = (
                rng.randint(publications, publications * 24)
                if publications > 0
                else 0
            )
            grant = round(rng.uniform(10000, 900000), 2) if rng.random() < 0.24 else 0
            mentorship = round(rng.uniform(2.4, 5.0), 2) if rng.random() < 0.9 else None
            rating = round(rng.uniform(2.5, 5.0), 2) if rng.random() < 0.88 else None
            record_id = str(uuid.uuid5(
                NAMESPACE,
                f"activity-{faculty_id}-{academic_year}",
            ))
            records.append({
                "id": record_id,
                "faculty_id": faculty_id,
                "academic_year": academic_year,
                "publications": publications,
                "citations": citations,
                "research_grants": f"{grant:.2f}",
                "mentorship_score": f"{mentorship:.2f}" if mentorship is not None else "",
                "faculty_rating": f"{rating:.2f}" if rating is not None else "",
                "is_synthetic": True,
            })

    return faculty, records


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sql_value(value):
    if value is None or value == "":
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def write_seed_sql(path: Path, faculty, records):
    lines = [
        "-- Synthetic research analytics demo data; not actual institutional records.",
        "BEGIN;",
        "INSERT INTO public.research_faculty "
        "(faculty_id, faculty_name, department, designation, is_active, is_synthetic)",
        "VALUES",
    ]
    lines.append(",\n".join(
        "(" + ", ".join(sql_value(row[field]) for field in FACULTY_FIELDS) + ")"
        for row in faculty
    ))
    lines.append(
        "ON CONFLICT (faculty_id) DO UPDATE SET "
        "faculty_name = EXCLUDED.faculty_name, department = EXCLUDED.department, "
        "designation = EXCLUDED.designation, is_active = EXCLUDED.is_active, "
        "is_synthetic = EXCLUDED.is_synthetic;"
    )
    lines.extend([
        "INSERT INTO public.faculty_research_records "
        "(id, faculty_id, academic_year, publications, citations, research_grants, "
        "mentorship_score, faculty_rating, is_synthetic)",
        "VALUES",
    ])
    lines.append(",\n".join(
        "(" + ", ".join(sql_value(row[field]) for field in RECORD_FIELDS) + ")"
        for row in records
    ))
    lines.append(
        "ON CONFLICT (id) DO UPDATE SET "
        "publications = EXCLUDED.publications, citations = EXCLUDED.citations, "
        "research_grants = EXCLUDED.research_grants, "
        "mentorship_score = EXCLUDED.mentorship_score, "
        "faculty_rating = EXCLUDED.faculty_rating, is_synthetic = EXCLUDED.is_synthetic;"
    )
    lines.extend([
        "COMMIT;",
        "",
        "SELECT 'research_faculty' AS table_name, count(*) FROM public.research_faculty "
        "WHERE is_synthetic;",
        "SELECT 'faculty_research_records' AS table_name, count(*) "
        "FROM public.faculty_research_records WHERE is_synthetic;",
        "SELECT count(*) AS orphaned_research_records "
        "FROM public.faculty_research_records AS records "
        "LEFT JOIN public.research_faculty AS faculty USING (faculty_id) "
        "WHERE faculty.faculty_id IS NULL;",
        "SELECT count(*) AS active_faculty_without_publications "
        "FROM public.research_faculty AS faculty "
        "WHERE faculty.is_active AND faculty.is_synthetic "
        "AND NOT EXISTS (SELECT 1 FROM public.faculty_research_records AS records "
        "WHERE records.faculty_id = faculty.faculty_id AND records.publications > 0);",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    output_dir = Path(__file__).resolve().parents[2] / "data" / "research" / "faculty"
    output_dir.mkdir(parents=True, exist_ok=True)
    faculty, records = build_data()
    write_csv(output_dir / "research_faculty.csv", FACULTY_FIELDS, faculty)
    write_csv(output_dir / "faculty_research_records.csv", RECORD_FIELDS, records)
    write_seed_sql(output_dir / "faculty_research_seed.sql", faculty, records)
    print(f"Generated {len(faculty)} faculty and {len(records)} annual research records.")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
