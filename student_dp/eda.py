import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load datasets
students = pd.read_csv("data/student/students.csv")
semester = pd.read_csv("data/student/student_semester_records.csv")
outcomes = pd.read_csv("data/student/student_outcomes.csv")
enrollment = pd.read_csv("data/student/enrollment_history.csv")

print("Students:", students.shape)
print("Semester records:", semester.shape)
print("Outcomes:", outcomes.shape)
print("Enrollment:", enrollment.shape)
# -------------------------------
# 3. Student Distribution by Department
# -------------------------------

plt.figure(figsize=(10, 6))

sns.countplot(
    data=students,
    x="department_id",
    order=students["department_id"].value_counts().index
)

plt.title("Student Distribution by Department")
plt.xlabel("Department")
plt.ylabel("Number of Students")
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()
# -------------------------------
# 4. Academic Performance Distributions
# -------------------------------

# Attendance
plt.figure(figsize=(8, 5))
sns.histplot(
    semester["attendance_percentage"],
    bins=20,
    kde=True
)
plt.title("Attendance Distribution")
plt.xlabel("Attendance Percentage")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.show()


# GPA
plt.figure(figsize=(8, 5))
sns.histplot(
    semester["cumulative_gpa"],
    bins=20,
    kde=True
)
plt.title("Cumulative GPA Distribution")
plt.xlabel("Cumulative GPA")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.show()


# Internal Marks
plt.figure(figsize=(8, 5))
sns.histplot(
    semester["internal_marks_percentage"],
    bins=20,
    kde=True
)
plt.title("Internal Marks Distribution")
plt.xlabel("Internal Marks (%)")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.show()


# Backlogs
plt.figure(figsize=(8, 5))
sns.countplot(
    data=semester,
    x="backlog_count"
)
plt.title("Backlog Distribution")
plt.xlabel("Number of Backlogs")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.show()


# Assignment Completion
plt.figure(figsize=(8, 5))
sns.histplot(
    semester["assignments_completed_pct"],
    bins=20,
    kde=True
)
plt.title("Assignment Completion Distribution")
plt.xlabel("Assignment Completion (%)")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.show()


# Fee Pending
plt.figure(figsize=(8, 5))
sns.histplot(
    semester["fee_pending_amount"],
    bins=30,
    kde=True
)
plt.title("Fee Pending Distribution")
plt.xlabel("Pending Fee Amount (₹)")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.show()
# -------------------------------
# 5. Merge Semester + Outcomes
# -------------------------------

analysis_df = semester.merge(
    outcomes[
        [
            "student_id",
            "academic_year",
            "semester",
            "dropout_status",
            "placement_status",
            "retention_status"
        ]
    ],
    on=[
        "student_id",
        "academic_year",
        "semester"
    ],
    how="inner"
)

print("\n--- ANALYSIS DATASET ---")
print("Shape:", analysis_df.shape)
print(analysis_df.head())
# -------------------------------
# 6. Attendance vs Dropout
# -------------------------------

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=analysis_df,
    x="dropout_status",
    y="attendance_percentage"
)

plt.title("Attendance vs Dropout")
plt.xlabel("Dropout Status")
plt.ylabel("Attendance Percentage")

plt.tight_layout()
plt.show()
print("\n--- ATTENDANCE BY DROPOUT ---")

print(
    analysis_df.groupby("dropout_status")[
        "attendance_percentage"
    ].mean()
)
# -------------------------------
# 7. CGPA vs Dropout
# -------------------------------

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=analysis_df,
    x="dropout_status",
    y="cumulative_gpa"
)

plt.title("Cumulative GPA vs Dropout")
plt.xlabel("Dropout Status")
plt.ylabel("Cumulative GPA")

plt.tight_layout()
plt.show()

print("\n--- CGPA BY DROPOUT ---")

print(
    analysis_df.groupby("dropout_status")[
        "cumulative_gpa"
    ].mean()
)
# -------------------------------
# 8. Backlogs vs Dropout
# -------------------------------

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=analysis_df,
    x="dropout_status",
    y="backlog_count"
)

plt.title("Backlogs vs Dropout")
plt.xlabel("Dropout Status")
plt.ylabel("Number of Backlogs")

plt.tight_layout()
plt.show()

print("\n--- BACKLOGS BY DROPOUT ---")

print(
    analysis_df.groupby("dropout_status")[
        "backlog_count"
    ].mean()
)
# -------------------------------
# 9. Fee Pending vs Dropout
# -------------------------------

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=analysis_df,
    x="dropout_status",
    y="fee_pending_amount"
)

plt.title("Fee Pending vs Dropout")
plt.xlabel("Dropout Status")
plt.ylabel("Fee Pending Amount (₹)")

plt.tight_layout()
plt.show()

print("\n--- FEE PENDING BY DROPOUT ---")

print(
    analysis_df.groupby("dropout_status")[
        "fee_pending_amount"
    ].mean()
)
# -------------------------------
# 10. Internship vs Placement
# -------------------------------

print("\n--- PLACEMENT RATE BY INTERNSHIP ---")

placement_by_internship = (
    analysis_df
    .groupby("internship_status")["placement_status"]
    .mean()
    .sort_values(ascending=False)
)

print(placement_by_internship)

plt.figure(figsize=(8, 5))

sns.barplot(
    data=analysis_df,
    x="internship_status",
    y="placement_status"
)

plt.title("Internship Status vs Placement")
plt.xlabel("Internship Status")
plt.ylabel("Placement Rate")

plt.tight_layout()
plt.show()
# -------------------------------
# 11. CGPA vs Placement
# -------------------------------

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=analysis_df,
    x="placement_status",
    y="cumulative_gpa"
)

plt.title("Cumulative GPA vs Placement")
plt.xlabel("Placement Status")
plt.ylabel("Cumulative GPA")

plt.tight_layout()
plt.show()

print("\n--- CGPA BY PLACEMENT ---")

print(
    analysis_df.groupby("placement_status")[
        "cumulative_gpa"
    ].mean()
)
# -------------------------------
# 12. Backlogs vs Placement
# -------------------------------

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=analysis_df,
    x="placement_status",
    y="backlog_count"
)

plt.title("Backlogs vs Placement")
plt.xlabel("Placement Status")
plt.ylabel("Number of Backlogs")

plt.tight_layout()
plt.show()

print("\n--- BACKLOGS BY PLACEMENT ---")

print(
    analysis_df.groupby("placement_status")[
        "backlog_count"
    ].mean()
)
# -------------------------------
# 13. Correlation Analysis
# -------------------------------

numeric_features = [
    "attendance_percentage",
    "courses_enrolled",
    "courses_passed",
    "courses_failed",
    "internal_marks_percentage",
    "semester_gpa",
    "cumulative_gpa",
    "backlog_count",
    "assignments_completed_pct",
    "disciplinary_incidents",
    "fee_pending_amount",
    "extracurricular_score",
    "dropout_status",
    "placement_status"
]

correlation_matrix = analysis_df[numeric_features].corr()

print("\n--- CORRELATION WITH DROPOUT ---")

print(
    correlation_matrix["dropout_status"]
    .sort_values(ascending=False)
)

print("\n--- CORRELATION WITH PLACEMENT ---")

print(
    correlation_matrix["placement_status"]
    .sort_values(ascending=False)
)

# Correlation heatmap
plt.figure(figsize=(12, 9))

sns.heatmap(
    correlation_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0
)

plt.title("Student Dataset Correlation Matrix")
plt.tight_layout()
plt.show()