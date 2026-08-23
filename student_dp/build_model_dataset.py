from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

STUDENTS_FILE = DATA_DIR / "students.csv"
RECORDS_FILE = DATA_DIR / "student_semester_records.csv"
OUTCOMES_FILE = DATA_DIR / "student_outcomes_corrected.csv"

OUTPUT_FILE = DATA_DIR / "dropout_model_dataset.csv"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
students = pd.read_csv(STUDENTS_FILE)
records = pd.read_csv(RECORDS_FILE)
outcomes = pd.read_csv(OUTCOMES_FILE)

print("Loaded:")
print(f"  Students:         {len(students):,}")
print(f"  Semester records: {len(records):,}")
print(f"  Outcomes:         {len(outcomes):,}")


# ---------------------------------------------------------
# Merge semester records with CORRECTED outcomes
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Add student profile information
# ---------------------------------------------------------
df = df.merge(
    students,
    on="student_id",
    how="left",
    validate="many_to_one",
)


# ---------------------------------------------------------
# Sort chronologically
# ---------------------------------------------------------
df = df.sort_values(
    ["student_id", "academic_year", "semester"]
).reset_index(drop=True)


print(f"\nRecords with valid outcomes: {len(df):,}")


# ---------------------------------------------------------
# Create NEXT-SEMESTER information
#
# IMPORTANT:
# We do this BEFORE removing dropout rows.
#
# Otherwise, a dropout semester would disappear and the
# previous semester would incorrectly jump to a later row.
# ---------------------------------------------------------
df["next_student_id"] = (
    df.groupby("student_id")["student_id"].shift(-1)
)

df["next_academic_year"] = (
    df.groupby("student_id")["academic_year"].shift(-1)
)

df["next_semester"] = (
    df.groupby("student_id")["semester"].shift(-1)
)

df["next_dropout_status"] = (
    df.groupby("student_id")["dropout_status"].shift(-1)
)


# ---------------------------------------------------------
# Verify next semester transition
# ---------------------------------------------------------
current_semester = df["semester"]

expected_next_year = (
    df["academic_year"]
    + (current_semester % 2 == 0).astype(int)
)

expected_next_semester = current_semester + 1


valid_next_semester = (
    (df["student_id"] == df["next_student_id"])
    & (df["next_academic_year"] == expected_next_year)
    & (df["next_semester"] == expected_next_semester)
    & df["next_dropout_status"].notna()
)


df = df.loc[valid_next_semester].copy()


# ---------------------------------------------------------
# IMPORTANT:
# Only students who have NOT already dropped out can be
# prediction candidates.
#
# Example:
#
# Sem 1 → dropout=False → valid prediction
# Sem 2 → dropout=True  → STOP
# Sem 3 → never becomes a prediction row
# ---------------------------------------------------------
df = df[df["dropout_status"] == False].copy()


# ---------------------------------------------------------
# Create target
# ---------------------------------------------------------
df["future_dropout"] = (
    df["next_dropout_status"]
    .astype(bool)
    .astype("int8")
)


# ---------------------------------------------------------
# Remove target/future information
# ---------------------------------------------------------
DROP_COLUMNS = [
    "record_id",
    "dropout_status",
    "next_student_id",
    "next_academic_year",
    "next_semester",
    "next_dropout_status",
    "future_dropout",
]

feature_columns = [
    column
    for column in df.columns
    if column not in DROP_COLUMNS
]


model_df = df[feature_columns + ["future_dropout"]].copy()


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
model_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------
print("\n--- MODEL DATASET ---")
print(f"Records: {len(model_df):,}")
print(f"Students: {model_df['student_id'].nunique():,}")
print(f"Features: {len(model_df.columns) - 1}")

print(f"Output: {OUTPUT_FILE}")


print("\n--- TARGET DISTRIBUTION ---")
print(
    model_df["future_dropout"]
    .value_counts()
    .sort_index()
)


print("\n--- TARGET PERCENTAGE ---")
print(
    model_df["future_dropout"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


print("\n--- TARGET BY CURRENT SEMESTER ---")
print(
    model_df.groupby("semester")["future_dropout"]
    .agg(["count", "sum"])
)


print("\n--- ROWS PER STUDENT ---")
print(
    model_df.groupby("student_id")
    .size()
    .describe()
)


print("\nSUCCESS: Modeling dataset created.")