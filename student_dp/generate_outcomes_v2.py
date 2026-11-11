from pathlib import Path
import numpy as np
import pandas as pd

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

RECORDS_FILE = DATA_DIR / "student_semester_records.csv"
STUDENTS_FILE = DATA_DIR / "students.csv"
OUTPUT_OUTCOMES_FILE = DATA_DIR / "student_outcomes_v2.csv"

# Reproducibility
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

print("=" * 70)
print("GENERATING PROBABILISTIC OUTCOMES V2")
print("=" * 70)

# Load records and student profile data
records = pd.read_csv(RECORDS_FILE)
students = pd.read_csv(STUDENTS_FILE)

records = records.merge(students, on="student_id", how="left")
records = records.sort_values(["student_id", "academic_year", "semester"]).reset_index(drop=True)

print(f"Total Semester Records: {len(records):,}")
print(f"Total Unique Students: {records['student_id'].nunique():,}")

# ---------------------------------------------------------
# Risk Factor Calculation
# ---------------------------------------------------------
# Academic Risk Sub-factors
gpa_risk = np.clip((6.5 - records["cumulative_gpa"]) / 2.5, -1.0, 1.5)
attendance_risk = np.clip((75.0 - records["attendance_percentage"]) / 25.0, -1.0, 1.5)
backlog_risk = np.clip(records["backlog_count"] / 3.0, 0.0, 1.5)
failure_risk = np.clip(records["courses_failed"] / 2.0, 0.0, 1.5)
marks_risk = np.clip((70.0 - records["internal_marks_percentage"]) / 30.0, -1.0, 1.5)
assignment_risk = np.clip((75.0 - records["assignments_completed_pct"]) / 25.0, -1.0, 1.5)

# Financial Risk Sub-factors
fee_pending_risk = np.clip(records["fee_pending_amount"] / 50000.0, 0.0, 1.5)
fee_unpaid = records["fee_payment_status"].isin(["Unpaid", "Overdue"]).astype(float)
fee_partial = (records["fee_payment_status"] == "Partial").astype(float) * 0.5
financial_risk = fee_pending_risk + fee_unpaid + fee_partial

# Protective Factors
scholarship_prot = (records["scholarship_status"].astype(bool)).astype(float) * 0.4
extra_prot = np.clip(records["extracurricular_score"] / 10.0, 0.0, 1.0) * 0.3

# Behavioral / Disciplinary Risk
discipline_risk = records["disciplinary_incidents"] * 0.6

# Composite Risk Score
composite_risk = (
    1.2 * gpa_risk
    + 1.0 * attendance_risk
    + 0.8 * backlog_risk
    + 0.6 * failure_risk
    + 0.5 * marks_risk
    + 0.4 * assignment_risk
    + 0.6 * financial_risk
    + 0.6 * discipline_risk
    - scholarship_prot
    - extra_prot
)

# Add non-deterministic Gaussian noise to ensure risk model is probabilistic
noise = rng.normal(0, 0.9, size=len(records))
logit = -3.5 + 0.95 * composite_risk + noise
next_dropout_probability = 1 / (1 + np.exp(-logit))

# ---------------------------------------------------------
# Transition & Dropout Assignment (Semester k -> k+1)
# ---------------------------------------------------------
is_not_sem8 = (records["semester"] < 8).values
trigger_next_dropout = (rng.random(len(records)) < next_dropout_probability) & is_not_sem8

# Align next semester transition per student
is_same_student_next = (records["student_id"] == records["student_id"].shift(1)).values
is_next_sem = (records["semester"] == (records["semester"].shift(1) + 1)).values
is_valid_next = is_same_student_next & is_next_sem

dropout_status = np.zeros(len(records), dtype=bool)
dropout_status[1:] = trigger_next_dropout[:-1] & is_valid_next[1:]

records["raw_dropout_status"] = dropout_status

# ---------------------------------------------------------
# Enforce Chronological Timeline Truncation (Remove post-dropout rows)
# ---------------------------------------------------------
dropout_rows = records[records["raw_dropout_status"] == True]
first_dropout = (
    dropout_rows
    .groupby("student_id")
    .first()[["academic_year", "semester"]]
    .rename(columns={"academic_year": "dropout_year", "semester": "dropout_semester"})
)

records = records.merge(first_dropout, left_on="student_id", right_index=True, how="left")
has_dropout = records["dropout_year"].notna()

after_dropout = (
    has_dropout
    & (
        (records["academic_year"] > records["dropout_year"])
        |
        (
            (records["academic_year"] == records["dropout_year"])
            & (records["semester"] > records["dropout_semester"])
        )
    )
)

print(f"Truncated post-dropout records: {after_dropout.sum():,}")
valid_records = records.loc[~after_dropout].copy()

# Output outcome dataset
outcomes_v2 = pd.DataFrame(
    {
        "outcome_id": np.arange(1, len(valid_records) + 1),
        "student_id": valid_records["student_id"],
        "academic_year": valid_records["academic_year"],
        "semester": valid_records["semester"],
        "retention_status": ~valid_records["raw_dropout_status"],
        "dropout_status": valid_records["raw_dropout_status"],
        "placement_status": False,
        "placement_package": 0.0,
        "graduation_status": False,
        "graduation_year": np.nan,
    }
)

outcomes_v2.to_csv(OUTPUT_OUTCOMES_FILE, index=False)
print(f"Saved generated outcomes to: {OUTPUT_OUTCOMES_FILE}")
print(f"Final valid records: {len(outcomes_v2):,}")
print(f"Total dropout students: {outcomes_v2[outcomes_v2['dropout_status']]['student_id'].nunique():,}")
