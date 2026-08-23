import pandas as pd

# -------------------------------
# Load datasets
# -------------------------------

students = pd.read_csv("data/student/students.csv")
semester = pd.read_csv("data/student/student_semester_records.csv")
outcomes = pd.read_csv("data/student/student_outcomes.csv")

print("Students:", students.shape)
print("Semester records:", semester.shape)
print("Outcomes:", outcomes.shape)
# -------------------------------
# Inspect Outcome Patterns
# -------------------------------

print("\n--- DROPOUT DISTRIBUTION ---")
print(outcomes["dropout_status"].value_counts())

print("\n--- PLACEMENT DISTRIBUTION ---")
print(outcomes["placement_status"].value_counts())

print("\n--- OUTCOMES PER STUDENT ---")
outcome_counts = outcomes.groupby("student_id").size()

print(outcome_counts.describe())

print("\nStudents with multiple outcome records:")
print(outcome_counts.value_counts().sort_index())
# -------------------------------
# Inspect Dropout Timing
# -------------------------------

dropout_records = outcomes[
    outcomes["dropout_status"] == True
].copy()

print("\n--- DROPOUT RECORDS ---")
print(dropout_records[
    ["student_id", "academic_year", "semester"]
].head(20))

# First dropout record for each student
first_dropout = (
    dropout_records
    .sort_values(["student_id", "academic_year", "semester"])
    .groupby("student_id")
    .first()
    .reset_index()
)

print("\n--- FIRST DROPOUT SEMESTER DISTRIBUTION ---")
print(
    first_dropout["semester"]
    .value_counts()
    .sort_index()
)

print("\n--- FIRST DROPOUT YEAR DISTRIBUTION ---")
print(
    first_dropout["academic_year"]
    .value_counts()
    .sort_index()
)
# -------------------------------
# Check Records After Dropout
# -------------------------------

# Sort outcomes chronologically
outcomes_sorted = outcomes.sort_values(
    ["student_id", "academic_year", "semester"]
).copy()

# Identify the first dropout semester for each student
outcomes_sorted["is_dropout"] = outcomes_sorted["dropout_status"].astype(bool)

first_dropout_index = (
    outcomes_sorted[outcomes_sorted["is_dropout"]]
    .groupby("student_id")
    .head(1)
    [["student_id", "academic_year", "semester"]]
    .rename(columns={
        "academic_year": "dropout_year",
        "semester": "dropout_semester"
    })
)

# Merge first dropout information back
outcomes_sorted = outcomes_sorted.merge(
    first_dropout_index,
    on="student_id",
    how="left"
)

# Identify records occurring after first dropout
after_dropout = outcomes_sorted[
    (
        outcomes_sorted["dropout_year"].notna()
    )
    &
    (
        (
            outcomes_sorted["academic_year"] > outcomes_sorted["dropout_year"]
        )
        |
        (
            (outcomes_sorted["academic_year"] == outcomes_sorted["dropout_year"])
            &
            (outcomes_sorted["semester"] > outcomes_sorted["dropout_semester"])
        )
    )
]

print("\n--- RECORDS AFTER FIRST DROPOUT ---")
print("Number of records:", len(after_dropout))
print("Number of affected students:", after_dropout["student_id"].nunique())

print("\nExamples:")
print(
    after_dropout[
        [
            "student_id",
            "academic_year",
            "semester",
            "dropout_status"
        ]
    ].head(20)
)