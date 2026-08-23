from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

RECORDS_FILE = DATA_DIR / "student_semester_records.csv"
OUTPUT_FILE = DATA_DIR / "student_outcomes_generated.csv"


# ---------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)


# ---------------------------------------------------------
# Load semester records
# ---------------------------------------------------------
records = pd.read_csv(RECORDS_FILE)

records = records.sort_values(
    ["student_id", "academic_year", "semester"]
).reset_index(drop=True)

print(f"Semester records: {len(records):,}")
print(f"Students: {records['student_id'].nunique():,}")


# ---------------------------------------------------------
# Helper: normalize a value to 0-1
# ---------------------------------------------------------
def normalize(series, low, high):
    return ((series - low) / (high - low)).clip(0, 1)


# ---------------------------------------------------------
# Construct sub-risk factors from CURRENT semester features
# Higher value = higher dropout risk.
# ---------------------------------------------------------

# 1. Academic Risk Sub-components
attendance_risk = 1 - normalize(records["attendance_percentage"], 50, 95)
gpa_risk = 1 - normalize(records["cumulative_gpa"], 4.5, 9.5)
backlog_risk = normalize(records["backlog_count"], 0, 5)
failure_risk = normalize(records["courses_failed"], 0, 4)
marks_risk = 1 - normalize(records["internal_marks_percentage"], 40, 90)
assignment_risk = 1 - normalize(records["assignments_completed_pct"], 40, 95)

academic_risk = (
    0.25 * gpa_risk
    + 0.20 * attendance_risk
    + 0.20 * backlog_risk
    + 0.15 * failure_risk
    + 0.10 * marks_risk
    + 0.10 * assignment_risk
)

# 2. Financial Risk Sub-components
fee_pending_risk = normalize(records["fee_pending_amount"], 0, 50000)
fee_status_unpaid = records["fee_payment_status"].isin(["Unpaid", "Overdue"]).astype(float)
financial_risk = 0.70 * fee_pending_risk + 0.30 * fee_status_unpaid

# 3. Engagement & Behavioral Risk Sub-components
discipline_risk = normalize(records["disciplinary_incidents"], 0, 2)
extra_risk = 1 - normalize(records["extracurricular_score"], 0, 10)
engagement_risk = 0.65 * discipline_risk + 0.35 * extra_risk

# Composite Risk Score (strictly internal generation component based on current semester k features)
risk_score = (
    0.55 * academic_risk
    + 0.30 * financial_risk
    + 0.15 * engagement_risk
)

# ---------------------------------------------------------
# Add semester-dependent baseline risk
# ---------------------------------------------------------
semester_effect = {
    1: 0.12,
    2: 0.10,
    3: 0.08,
    4: 0.06,
    5: 0.04,
    6: 0.02,
    7: 0.01,
    8: 0.00,
}

sem_bump = records["semester"].map(semester_effect).fillna(0.0)

# ---------------------------------------------------------
# Convert risk score at semester k into probability of dropout in semester k+1
# Semester 8 has no next-semester target and should not generate one.
# ---------------------------------------------------------
is_not_sem8 = (records["semester"] < 8).values

logit = -4.3 + 4.2 * risk_score + sem_bump
next_dropout_probability = 1 / (1 + np.exp(-logit))

# Sample candidate next-semester dropout triggers strictly from current semester k features
trigger_next_dropout = (rng.random(len(records)) < next_dropout_probability.values) & is_not_sem8

# Identify valid contiguous next semester rows for the same student
is_same_student_next = (records["student_id"] == records["student_id"].shift(1)).values
is_next_sem = (records["semester"] == (records["semester"].shift(1) + 1)).values
is_valid_next = is_same_student_next & is_next_sem

# Assign dropout_status at semester k+1 from trigger_next_dropout at semester k
# No semester receives a dropout label from its own semester's features.
dropout = np.zeros(len(records), dtype=bool)
dropout[1:] = trigger_next_dropout[:-1] & is_valid_next[1:]

records["dropout_status"] = dropout

# ---------------------------------------------------------
# Create outcome dataset
# ---------------------------------------------------------
outcomes = pd.DataFrame(
    {
        "outcome_id": np.arange(1, len(records) + 1),
        "student_id": records["student_id"],
        "academic_year": records["academic_year"],
        "semester": records["semester"],
        "retention_status": ~dropout,
        "dropout_status": dropout,
        "placement_status": False,
        "placement_package": 0.0,
        "graduation_status": False,
        "graduation_year": np.nan,
    }
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
outcomes.to_csv(OUTPUT_FILE, index=False)

# ---------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------
print("\n--- GENERATED OUTCOMES ---")
print(f"Records: {len(outcomes):,}")
print(f"Candidate dropout records: {dropout.sum():,}")
print(f"Candidate dropout rate: {dropout.mean() * 100:.2f}%")
print("\nDropout by semester:")
print(outcomes[outcomes["dropout_status"]]["semester"].value_counts().sort_index())
print("\nSUCCESS: Outcome generation completed.")
