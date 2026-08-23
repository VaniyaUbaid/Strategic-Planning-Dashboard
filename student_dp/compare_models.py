from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

INPUT_FILE = DATA_DIR / "dropout_model_dataset_generated.csv"

# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------
df = pd.read_csv(INPUT_FILE)

print("==========================================================")
print("            MODEL COMPARISON EXPERIMENT REPORT            ")
print("==========================================================")
print(f"Dataset: {INPUT_FILE.name}")
print(f"Total Records: {len(df):,}")
print(f"Total Students: {df['student_id'].nunique():,}")
print(f"Target Distribution:\n{df['future_dropout'].value_counts()}")
print(f"Target Percentage:\n{(df['future_dropout'].value_counts(normalize=True)*100).round(2)}")

# ---------------------------------------------------------
# Feature Engineering & Target Separation
# ---------------------------------------------------------
df["age_at_admission"] = (
    df["admission_year"] - pd.to_datetime(df["date_of_birth"]).dt.year
)

TARGET = "future_dropout"
DROP_COLS = ["student_id", "date_of_birth", TARGET, "academic_year"]

X = df.drop(columns=DROP_COLS)
y = df[TARGET]

# Convert boolean columns
bool_cols = ["scholarship_status", "hostel_status"]
for col in bool_cols:
    if col in X.columns:
        X[col] = X[col].astype("int8")

# ---------------------------------------------------------
# Student-Level Train/Test Split (GroupShuffleSplit)
# ---------------------------------------------------------
splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=df["student_id"]))

X_train, y_train = X.iloc[train_idx].copy(), y.iloc[train_idx].copy()
X_test, y_test = X.iloc[test_idx].copy(), y.iloc[test_idx].copy()

train_students = set(df.iloc[train_idx]["student_id"])
test_students = set(df.iloc[test_idx]["student_id"])
overlap = train_students & test_students

print(f"\n--- SPLIT SUMMARY ---")
print(f"Train records: {len(X_train):,} ({len(train_students):,} students)")
print(f"Test records:  {len(X_test):,} ({len(test_students):,} students)")
print(f"Student ID Overlap: {len(overlap)}")

# ---------------------------------------------------------
# Preprocessing Pipeline
# ---------------------------------------------------------
num_features = X_train.select_dtypes(
    include=["int64", "float64", "int32", "float32", "int8"]
).columns.tolist()

cat_features = X_train.select_dtypes(
    include=["object"]
).columns.tolist()

num_pipe = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]
)

cat_pipe = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("numeric", num_pipe, num_features),
        ("categorical", cat_pipe, cat_features),
    ],
    remainder="drop",
)

# Fit preprocessor on training data only
X_train_proc = preprocessor.fit_transform(X_train)
X_test_proc = preprocessor.transform(X_test)

# ---------------------------------------------------------
# Define Models to Compare
# ---------------------------------------------------------
models = {
    "Logistic Regression (Baseline)": LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
    "HistGradientBoosting": HistGradientBoostingClassifier(
        class_weight="balanced",
        random_state=42,
        max_iter=100,
    ),
}

# ---------------------------------------------------------
# Train and Evaluate Models
# ---------------------------------------------------------
results = []

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_proc, y_train)
    
    y_pred = model.predict(X_test_proc)
    y_prob = model.predict_proba(X_test_proc)[:, 1]
    
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    results.append({
        "Model": name,
        "ROC-AUC": roc_auc,
        "PR-AUC": pr_auc,
        "Precision": precision,
        "Recall": recall,
        "F1-Score": f1,
        "TN": cm[0, 0],
        "FP": cm[0, 1],
        "FN": cm[1, 0],
        "TP": cm[1, 1],
    })

# ---------------------------------------------------------
# Summary Table & Report
# ---------------------------------------------------------
results_df = pd.DataFrame(results)

print("\n==========================================================")
print("             MODEL EXPERIMENT RESULTS SUMMARY             ")
print("==========================================================")

summary_cols = ["Model", "ROC-AUC", "PR-AUC", "Precision", "Recall", "F1-Score"]
print(results_df[summary_cols].to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n--- CONFUSION MATRICES ---")
for r in results:
    print(f"\nModel: {r['Model']}")
    print(f"[[TN={r['TN']:<5}  FP={r['FP']:<5}]")
    print( f" [FN={r['FN']:<5}  TP={r['TP']:<5}]]")

print("\nSUCCESS: Model comparison experiment complete.")
