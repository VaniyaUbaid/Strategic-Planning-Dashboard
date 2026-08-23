from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

INPUT_FILE = DATA_DIR / "dropout_model_dataset.csv"

TRAIN_FILE = DATA_DIR / "dropout_train.csv"
TEST_FILE = DATA_DIR / "dropout_test.csv"

# Load dataset
df = pd.read_csv(INPUT_FILE)

print(f"Total records: {len(df):,}")
print(f"Total students: {df['student_id'].nunique():,}")

# Student-level split
# IMPORTANT: Rows belonging to the same student must stay together.

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42,
)

train_indices, test_indices = next(
    splitter.split(
        df,
        y=df["future_dropout"],
        groups=df["student_id"],
    )
)

train_df = df.iloc[train_indices].copy()
test_df = df.iloc[test_indices].copy()

# Save

train_df.to_csv(TRAIN_FILE, index=False)
test_df.to_csv(TEST_FILE, index=False)

# Verification

train_students = set(train_df["student_id"])
test_students = set(test_df["student_id"])

overlap = train_students & test_students

print("\n--- SPLIT RESULTS ---")
print(f"Training records: {len(train_df):,}")
print(f"Testing records:  {len(test_df):,}")
print(f"Training students: {len(train_students):,}")
print(f"Testing students:  {len(test_students):,}")
print(f"\nStudent overlap: {len(overlap)}")
print("\n--- TRAIN TARGET ---")
print(train_df["future_dropout"].value_counts())
print(
    train_df["future_dropout"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)
print("\n--- TEST TARGET ---")
print(test_df["future_dropout"].value_counts())
print(
    test_df["future_dropout"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)
if len(overlap) == 0:
    print("\nSUCCESS: No student appears in both train and test.")
else:
    print("\nERROR: Student leakage detected!")