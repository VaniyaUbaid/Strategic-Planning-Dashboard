from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

outcomes_gen = pd.read_csv(DATA_DIR / "student_outcomes_generated.csv")
outcomes_corr = pd.read_csv(DATA_DIR / "student_outcomes_corrected_generated.csv")
model_df = pd.read_csv(DATA_DIR / "dropout_model_dataset_generated.csv")

print("==========================================================")
print("            COMPLETE PIPELINE VALIDATION REPORT           ")
print("==========================================================")

# 1. Candidate Dropout Rate
candidate_count = outcomes_gen["dropout_status"].sum()
candidate_rate = outcomes_gen["dropout_status"].mean() * 100
print(f"\n1. CANDIDATE DROPOUT RATE: {candidate_rate:.2f}% ({candidate_count:,} / {len(outcomes_gen):,} records)")

# 2. Final Unique Dropout-Student Rate
total_students = 20000
unique_dropout_students = outcomes_corr.loc[outcomes_corr["dropout_status"] == True, "student_id"].nunique()
dropout_student_pct = (unique_dropout_students / total_students) * 100
print(f"\n2. FINAL UNIQUE DROPOUT-STUDENT RATE: {dropout_student_pct:.2f}% ({unique_dropout_students:,} / {total_students:,} total students)")

# 3. Final future_dropout Prevalence
final_records = len(model_df)
final_dropout_count = model_df["future_dropout"].sum()
final_prevalence = model_df["future_dropout"].mean() * 100
print(f"\n3. FINAL future_dropout PREVALENCE: {final_prevalence:.2f}% ({final_dropout_count:,} / {final_records:,} modeling records)")

# 4. Dropout Counts by Semester
print("\n4. DROPOUT COUNTS BY CURRENT SEMESTER:")
sem_summary = model_df.groupby("semester")["future_dropout"].agg(["count", "sum", "mean"])
sem_summary["mean"] = (sem_summary["mean"] * 100).round(2)
sem_summary.columns = ["Total Records", "Future Dropouts", "Dropout Rate (%)"]
print(sem_summary)

# 5. Feature Distributions by Target
print("\n5. FEATURE DISTRIBUTIONS BY TARGET (Mean Values):")
check_features = [
    "attendance_percentage",
    "semester_gpa",
    "cumulative_gpa",
    "backlog_count",
    "courses_failed",
    "internal_marks_percentage",
    "assignments_completed_pct",
    "disciplinary_incidents",
    "fee_pending_amount",
    "extracurricular_score",
]

grouped = model_df.groupby("future_dropout")[check_features].mean().T
grouped.columns = ["No Dropout (0)", "Future Dropout (1)"]
grouped["Difference (1 - 0)"] = grouped["Future Dropout (1)"] - grouped["No Dropout (0)"]
print(grouped.round(3))

# 6. Correlation / Directional Association Results
print("\n6. FEATURE CORRELATION WITH future_dropout:")
corrs = model_df[check_features].apply(lambda x: x.corr(model_df["future_dropout"])).sort_values()
for feat, corr_val in corrs.items():
    print(f"  {feat:30s}: {corr_val:+.4f}")

# 7. Post-Dropout Violations
df_sorted = outcomes_corr.sort_values(["student_id", "academic_year", "semester"])
cum_prior_dropouts = df_sorted.groupby("student_id")["dropout_status"].cumsum() - df_sorted["dropout_status"].astype(int)
violations = (cum_prior_dropouts > 0).sum()
print(f"\n7. POST-DROPOUT TIMELINE VIOLATIONS: {violations}")

# 8. Train/Test Student Overlap Check
splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_idx, test_idx = next(splitter.split(model_df, y=model_df["future_dropout"], groups=model_df["student_id"]))

train_df = model_df.iloc[train_idx].copy()
test_df = model_df.iloc[test_idx].copy()

train_students = set(train_df["student_id"])
test_students = set(test_df["student_id"])
overlap = train_students & test_students
print(f"\n8. TRAIN / TEST STUDENT OVERLAP: {len(overlap)} (Train Students: {len(train_students):,}, Test Students: {len(test_students):,})")

# 9. Baseline ML Metrics
train_df["age_at_admission"] = train_df["admission_year"] - pd.to_datetime(train_df["date_of_birth"]).dt.year
test_df["age_at_admission"] = test_df["admission_year"] - pd.to_datetime(test_df["date_of_birth"]).dt.year

TARGET = "future_dropout"
DROP_COLS = ["student_id", "date_of_birth", TARGET, "academic_year", "state"]

X_train = train_df.drop(columns=DROP_COLS)
y_train = train_df[TARGET]

X_test = test_df.drop(columns=DROP_COLS)
y_test = test_df[TARGET]

bool_cols = ["scholarship_status", "hostel_status"]
for c in bool_cols:
    X_train[c] = X_train[c].astype("int8")
    X_test[c] = X_test[c].astype("int8")

num_features = X_train.select_dtypes(include=["int64", "float64", "int32", "float32", "int8"]).columns.tolist()
cat_features = X_train.select_dtypes(include=["object"]).columns.tolist()

num_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
cat_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])

preprocessor = ColumnTransformer(transformers=[("numeric", num_pipe, num_features), ("categorical", cat_pipe, cat_features)])

model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])

pipeline.fit(X_train, y_train)

y_pred = pipeline.predict(X_test)
y_prob = pipeline.predict_proba(X_test)[:, 1]

roc_auc = roc_auc_score(y_test, y_prob)
pr_auc = average_precision_score(y_test, y_prob)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

print("\n9. BASELINE LOGISTIC REGRESSION METRICS:")
print(f"   ROC-AUC:   {roc_auc:.4f}")
print(f"   PR-AUC:    {pr_auc:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall:    {recall:.4f}")
print(f"   F1-score:  {f1:.4f}")
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
