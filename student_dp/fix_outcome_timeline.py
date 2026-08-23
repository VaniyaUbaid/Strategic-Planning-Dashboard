from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

INPUT_FILE = DATA_DIR / "student_outcomes.csv"
OUTPUT_FILE = DATA_DIR / "student_outcomes_corrected.csv"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
df = pd.read_csv(INPUT_FILE)

print(f"Original records: {len(df):,}")
print(f"Students: {df['student_id'].nunique():,}")


# ---------------------------------------------------------
# Sort chronologically
# ---------------------------------------------------------
df = df.sort_values(
    ["student_id", "academic_year", "semester"]
).reset_index(drop=True)


# ---------------------------------------------------------
# Find the first dropout semester for each student
# ---------------------------------------------------------
dropout_rows = df[df["dropout_status"] == True]

first_dropout = (
    dropout_rows
    .groupby("student_id")
    .first()
    [["academic_year", "semester"]]
    .rename(columns={
        "academic_year": "dropout_year",
        "semester": "dropout_semester"
    })
)


# ---------------------------------------------------------
# Remove records AFTER the first dropout
#
# The dropout semester itself is retained.
# Any later semester is removed.
# ---------------------------------------------------------
df = df.merge(
    first_dropout,
    left_on="student_id",
    right_index=True,
    how="left"
)


has_dropout = df["dropout_year"].notna()

after_dropout = (
    has_dropout
    & (
        (df["academic_year"] > df["dropout_year"])
        |
        (
            (df["academic_year"] == df["dropout_year"])
            & (df["semester"] > df["dropout_semester"])
        )
    )
)

removed = after_dropout.sum()

df = df.loc[~after_dropout].copy()


# ---------------------------------------------------------
# Remove helper columns
# ---------------------------------------------------------
df = df.drop(
    columns=["dropout_year", "dropout_semester"]
)


# ---------------------------------------------------------
# Save corrected dataset
# ---------------------------------------------------------
df.to_csv(OUTPUT_FILE, index=False)


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------
print("\n--- CORRECTION RESULTS ---")
print(f"Records removed: {removed:,}")
print(f"Records remaining: {len(df):,}")

print(
    f"Students with dropout: "
    f"{df.loc[df['dropout_status'] == True, 'student_id'].nunique():,}"
)


# ---------------------------------------------------------
# Verify that no student has records after dropout
# ---------------------------------------------------------
df_sorted = df.sort_values(["student_id", "academic_year", "semester"])
cum_prior_dropouts = df_sorted.groupby("student_id")["dropout_status"].cumsum() - df_sorted["dropout_status"].astype(int)
violations = (cum_prior_dropouts > 0).sum()

print(f"Students with post-dropout records: {violations}")


if violations == 0:
    print("\nSUCCESS: Dropout timelines are now consistent.")
else:
    print("\nWARNING: Some dropout timeline violations remain.")