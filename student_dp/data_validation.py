import pandas as pd

students = pd.read_csv("data/student/students.csv")
semester = pd.read_csv("data/student/student_semester_records.csv")
outcomes = pd.read_csv("data/student/student_outcomes.csv")
enrollment = pd.read_csv("data/student/enrollment_history.csv")

print("Students:", students.shape)
print("Semester records:", semester.shape)
print("Outcomes:", outcomes.shape)
print("Enrollment:", enrollment.shape)
students["scholarship_type"] = students["scholarship_type"].fillna("None")
# -------------------------------
# 1. Missing Value Check
# -------------------------------

print("\n--- MISSING VALUES ---")

print("\nStudents:")
print(students.isnull().sum())

print("\nSemester Records:")
print(semester.isnull().sum())

print("\nOutcomes:")
print(outcomes.isnull().sum())

print("\nEnrollment:")
print(enrollment.isnull().sum())
# -------------------------------
# 2. Duplicate Check
# -------------------------------

print("\n--- DUPLICATE CHECK ---")

# 1. Duplicate student IDs
print(
    "Duplicate student IDs:",
    students["student_id"].duplicated().sum()
)

# 2. Duplicate semester record IDs
print(
    "Duplicate semester record IDs:",
    semester["record_id"].duplicated().sum()
)

# 3. Duplicate outcome IDs
print(
    "Duplicate outcome IDs:",
    outcomes["outcome_id"].duplicated().sum()
)

# 4. Duplicate enrollment IDs
print(
    "Duplicate enrollment IDs:",
    enrollment["enrollment_id"].duplicated().sum()
)

# 5. Duplicate student-semester combinations
print(
    "Duplicate student-semester records:",
    semester.duplicated(
        subset=["student_id", "academic_year", "semester"]
    ).sum()
)

# 6. Duplicate student-outcome combinations
print(
    "Duplicate student-outcome records:",
    outcomes.duplicated(
        subset=["student_id", "academic_year", "semester"]
    ).sum()
)
# -------------------------------
# 3. Numerical Range Validation
# -------------------------------

print("\n--- NUMERICAL RANGE CHECK ---")

# Attendance
print(
    "Attendance range:",
    semester["attendance_percentage"].min(),
    "to",
    semester["attendance_percentage"].max()
)

# Internal marks
print(
    "Internal marks range:",
    semester["internal_marks_percentage"].min(),
    "to",
    semester["internal_marks_percentage"].max()
)

# Semester GPA
print(
    "Semester GPA range:",
    semester["semester_gpa"].min(),
    "to",
    semester["semester_gpa"].max()
)

# Cumulative GPA
print(
    "Cumulative GPA range:",
    semester["cumulative_gpa"].min(),
    "to",
    semester["cumulative_gpa"].max()
)

# Backlogs
print(
    "Backlog range:",
    semester["backlog_count"].min(),
    "to",
    semester["backlog_count"].max()
)

# Assignment completion
print(
    "Assignment completion range:",
    semester["assignments_completed_pct"].min(),
    "to",
    semester["assignments_completed_pct"].max()
)

# Fee pending
print(
    "Fee pending range:",
    semester["fee_pending_amount"].min(),
    "to",
    semester["fee_pending_amount"].max()
)

# Extracurricular score
print(
    "Extracurricular score range:",
    semester["extracurricular_score"].min(),
    "to",
    semester["extracurricular_score"].max()
)
course_check = (
    semester["courses_passed"] +
    semester["courses_failed"]
    ==
    semester["courses_enrolled"]
)

print("Invalid course totals:", (~course_check).sum())
# -------------------------------
# 4. Categorical Value Validation
# -------------------------------

print("\n--- CATEGORICAL VALUE CHECK ---")

print("\nDepartments:")
print(sorted(students["department_id"].unique()))

print("\nPrograms:")
print(sorted(students["program"].unique()))

print("\nAdmission Types:")
print(sorted(students["admission_type"].unique()))

print("\nGenders:")
print(sorted(students["gender"].unique()))

print("\nScholarship Types:")
print(sorted(students["scholarship_type"].unique()))

print("\nFamily Income Bands:")
print(sorted(students["family_income_band"].unique()))

print("\nFee Payment Status:")
print(sorted(semester["fee_payment_status"].unique()))

print("\nInternship Status:")
print(sorted(semester["internship_status"].unique()))
# -------------------------------
# 5. Foreign-Key Validation
# -------------------------------

print("\n--- FOREIGN KEY CHECK ---")

# Semester records → Students
invalid_semester_students = ~semester["student_id"].isin(
    students["student_id"]
)

print(
    "Semester records with invalid student IDs:",
    invalid_semester_students.sum()
)

# Outcomes → Students
invalid_outcome_students = ~outcomes["student_id"].isin(
    students["student_id"]
)

print(
    "Outcomes with invalid student IDs:",
    invalid_outcome_students.sum()
)

# Enrollment → Departments
invalid_enrollment_departments = ~enrollment["department_id"].isin(
    students["department_id"].unique()
)

print(
    "Enrollment records with invalid department IDs:",
    invalid_enrollment_departments.sum()
)

# Student departments → valid department list
valid_departments = {
    "CSE", "AIML", "ECE", "EEE", "ME",
    "BT", "BBA", "MATH", "PHY", "CHEM"
}

invalid_student_departments = ~students["department_id"].isin(
    valid_departments
)

print(
    "Students with invalid department IDs:",
    invalid_student_departments.sum()
)