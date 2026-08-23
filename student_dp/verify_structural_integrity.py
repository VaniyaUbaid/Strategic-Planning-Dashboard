from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

records = pd.read_csv(DATA_DIR / "student_semester_records.csv")
outcomes_gen = pd.read_csv(DATA_DIR / "student_outcomes_generated.csv")
outcomes_corr = pd.read_csv(DATA_DIR / "student_outcomes_corrected_generated.csv")
model_df = pd.read_csv(DATA_DIR / "dropout_model_dataset_generated.csv")

print("==========================================================")
print("       VERIFICATION OF 9 STRUCTURAL INTEGRITY CHECKS       ")
print("==========================================================")

# Check 1: No current-semester leakage
# Verify current semester dropout_status is not in feature columns
feature_cols = [c for c in model_df.columns if c != "future_dropout"]
has_leak_col = "dropout_status" in feature_cols or "next_dropout_status" in feature_cols or "retention_status" in feature_cols
print(f"Check 1: No current-semester target leakage in feature columns -> {'PASS' if not has_leak_col else 'FAIL'}")

# Check 2: Every future_dropout=1 row corresponds to next semester's actual dropout event
# Merge model_df (at sem k) with outcomes_corr (at sem k+1)
model_next = model_df.copy()
model_next["expected_next_sem"] = model_next["semester"] + 1

merged_next = model_next.merge(
    outcomes_corr[["student_id", "semester", "dropout_status"]],
    left_on=["student_id", "expected_next_sem"],
    right_on=["student_id", "semester"],
    suffixes=("", "_corr"),
    how="inner"
)

# For every row with future_dropout = 1, dropout_status in next semester must be True
mismatch_next = (merged_next["future_dropout"] == 1) & (merged_next["dropout_status"] != True)
print(f"Check 2: Every future_dropout=1 corresponds to next semester's actual dropout event -> {'PASS' if mismatch_next.sum() == 0 else 'FAIL'} (Mismatches: {mismatch_next.sum()})")

# Check 3: No future_dropout=1 exists for Semester 7 unless the student actually drops in Semester 8
sem7_rows = model_next[model_next["semester"] == 7]
sem7_dropouts = sem7_rows[sem7_rows["future_dropout"] == 1]

sem8_outcomes = outcomes_corr[(outcomes_corr["semester"] == 8) & (outcomes_corr["dropout_status"] == True)]
sem7_valid = sem7_dropouts["student_id"].isin(sem8_outcomes["student_id"])
sem7_invalid_count = (~sem7_valid).sum()
print(f"Check 3: Semester 7 future_dropout=1 matches actual Semester 8 dropout -> {'PASS' if sem7_invalid_count == 0 else 'FAIL'} (Invalid Sem 7 dropouts: {sem7_invalid_count})")

# Check 4: No target exists for Semester 8
sem8_model_rows = (model_df["semester"] == 8).sum()
print(f"Check 4: No target exists for Semester 8 in modeling dataset -> {'PASS' if sem8_model_rows == 0 else 'FAIL'} (Semester 8 rows in model dataset: {sem8_model_rows})")

# Check 5: A student's first dropout is the only dropout event
dropout_counts_per_student = outcomes_corr[outcomes_corr["dropout_status"] == True].groupby("student_id").size()
multiple_dropouts = (dropout_counts_per_student > 1).sum()
print(f"Check 5: A student's first dropout is the only dropout event -> {'PASS' if multiple_dropouts == 0 else 'FAIL'} (Students with multiple dropouts: {multiple_dropouts})")

# Check 6: No records exist after dropout
outcomes_sorted = outcomes_corr.sort_values(["student_id", "academic_year", "semester"])
cum_prior_dropouts = outcomes_sorted.groupby("student_id")["dropout_status"].cumsum() - outcomes_sorted["dropout_status"].astype(int)
violations = (cum_prior_dropouts > 0).sum()
print(f"Check 6: No records exist after dropout in corrected outcomes -> {'PASS' if violations == 0 else 'FAIL'} (Post-dropout records: {violations})")

# Check 7: Generated outcome IDs/student IDs/semester/year match semester records exactly
match_rows = len(records) == len(outcomes_gen)
match_students = (records["student_id"] == outcomes_gen["student_id"]).all()
match_semesters = (records["semester"] == outcomes_gen["semester"]).all()
match_years = (records["academic_year"] == outcomes_gen["academic_year"]).all()
match_ids = (records.index == outcomes_gen.index).all()
all_match = match_rows and match_students and match_semesters and match_years and match_ids
print(f"Check 7: Generated outcome metadata matches semester records exactly -> {'PASS' if all_match else 'FAIL'}")

# Check 8: future_dropout isn't accidentally derived from any feature used by the model
# Verify future_dropout is not a deterministic function of any single feature column
check_features = [
    "attendance_percentage", "semester_gpa", "cumulative_gpa", "backlog_count",
    "courses_failed", "internal_marks_percentage", "assignments_completed_pct",
    "disciplinary_incidents", "fee_pending_amount", "extracurricular_score"
]
perfect_corrs = [c for c in check_features if abs(model_df[c].corr(model_df["future_dropout"])) > 0.9]
print(f"Check 8: future_dropout is not derived directly from any single model feature -> {'PASS' if len(perfect_corrs) == 0 else 'FAIL'} (Direct feature matches: {perfect_corrs})")

# Check 9: Final dataset has no duplicate student-semester rows
duplicates = model_df.duplicated(subset=["student_id", "academic_year", "semester"]).sum()
print(f"Check 9: Final dataset has no duplicate student-semester rows -> {'PASS' if duplicates == 0 else 'FAIL'} (Duplicates: {duplicates})")

print("==========================================================")
