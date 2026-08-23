from pathlib import Path
import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

STUDENTS_FILE = DATA_DIR / "students.csv"
RECORDS_FILE = DATA_DIR / "student_semester_records.csv"
OUTCOMES_FILE = DATA_DIR / "student_outcomes_corrected_generated.csv"
OUTPUT_FILE = DATA_DIR / "dropout_model_dataset_generated.csv"

# Load data
students = pd.read_csv(STUDENTS_FILE)
records = pd.read_csv(RECORDS_FILE)
outcomes = pd.read_csv(OUTCOMES_FILE)

print("Loaded:")
print(f"  Students:         {len(students):,}")
print(f"  Semester records: {len(records):,}")
print(f"  Generated outcomes: {len(outcomes):,}")

# Merge semester records with CORRECTED generated outcomes
df = records.merge(
    outcomes[
        [
            "student_id",
            "academic_year",
            "semester",
            "dropout_status",
        ]
    ],
    on=["student_id", "academic_year", "semester"],
    how="inner",
    validate="one_to_one",
)

# Add student profile information
df = df.merge(
    students,
    on="student_id",
    how="left",
    validate="many_to_one",
)

# Sort chronologically
df = df.sort_values(["student_id", "academic_year", "semester"]).reset_index(drop=True)

# Create NEXT-SEMESTER information
df["next_student_id"] = df.groupby("student_id")["student_id"].shift(-1)
df["next_academic_year"] = df.groupby("student_id")["academic_year"].shift(-1)
df["next_semester"] = df.groupby("student_id")["semester"].shift(-1)
df["next_dropout_status"] = df.groupby("student_id")["dropout_status"].shift(-1)

# Verify next semester transition
current_semester = df["semester"]
expected_next_year = df["academic_year"] + (current_semester % 2 == 0).astype(int)
expected_next_semester = current_semester + 1

valid_next_semester = (
    (df["student_id"] == df["next_student_id"])
    & (df["next_academic_year"] == expected_next_year)
    & (df["next_semester"] == expected_next_semester)
    & df["next_dropout_status"].notna()
)

df = df.loc[valid_next_semester].copy()

# Only students who have NOT already dropped out can be prediction candidates
df = df[df["dropout_status"] == False].copy()

# Target
df["future_dropout"] = df["next_dropout_status"].astype(bool).astype("int8")

# Drop target/future tracking columns
DROP_COLUMNS = [
    "record_id",
    "dropout_status",
    "next_student_id",
    "next_academic_year",
    "next_semester",
    "next_dropout_status",
    "future_dropout",
]

feature_columns = [col for col in df.columns if col not in DROP_COLUMNS]
FORBIDDEN_FEATURES = {
    "dropout_status",
    "next_student_id",
    "next_academic_year",
    "next_semester",
    "next_dropout_status",
}

leaked_features = FORBIDDEN_FEATURES.intersection(feature_columns)

if leaked_features:
    raise ValueError(
        f"Target leakage detected: {sorted(leaked_features)}"
    )
model_df = df[feature_columns + ["future_dropout"]].copy()

# Save
model_df.to_csv(OUTPUT_FILE, index=False)

print("\n--- MODEL DATASET GENERATED ---")
print(f"Records: {len(model_df):,}")
print(f"Students: {model_df['student_id'].nunique():,}")
print(f"Target Distribution:\n{model_df['future_dropout'].value_counts()}")
print(f"Target Percentage:\n{model_df['future_dropout'].value_counts(normalize=True).mul(100).round(2)}")
