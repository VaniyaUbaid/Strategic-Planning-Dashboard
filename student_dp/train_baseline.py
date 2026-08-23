from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "student"

TRAIN_FILE = DATA_DIR / "dropout_train.csv"
TEST_FILE = DATA_DIR / "dropout_test.csv"


# ---------------------------------------------------------
# Load train/test data
# ---------------------------------------------------------
train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

print(f"Training records: {len(train_df):,}")
print(f"Testing records:  {len(test_df):,}")


# ---------------------------------------------------------
# Create age feature
# ---------------------------------------------------------
train_df["age_at_admission"] = (
    train_df["admission_year"]
    - pd.to_datetime(train_df["date_of_birth"]).dt.year
)

test_df["age_at_admission"] = (
    test_df["admission_year"]
    - pd.to_datetime(test_df["date_of_birth"]).dt.year
)


# ---------------------------------------------------------
# Separate X and y
# ---------------------------------------------------------
TARGET = "future_dropout"

DROP_COLUMNS = [
    "student_id",
    "date_of_birth",
    TARGET,
    "academic_year",
]

X_train = train_df.drop(columns=DROP_COLUMNS)
y_train = train_df[TARGET]

X_test = test_df.drop(columns=DROP_COLUMNS)
y_test = test_df[TARGET]


# ---------------------------------------------------------
# Convert boolean columns to numeric
# ---------------------------------------------------------
boolean_columns = [
    "scholarship_status",
    "hostel_status",
]

for column in boolean_columns:
    X_train[column] = X_train[column].astype("int8")
    X_test[column] = X_test[column].astype("int8")


# ---------------------------------------------------------
# Identify feature types
# ---------------------------------------------------------
numeric_features = X_train.select_dtypes(
    include=["int64", "float64", "int32", "float32", "int8"]
).columns.tolist()

categorical_features = X_train.select_dtypes(
    include=["object"]
).columns.tolist()


print("\n--- FEATURES ---")
print(f"Numeric features:     {len(numeric_features)}")
print(f"Categorical features: {len(categorical_features)}")


# ---------------------------------------------------------
# Numeric preprocessing
# ---------------------------------------------------------
numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "scaler",
            StandardScaler(),
        ),
    ]
)


# ---------------------------------------------------------
# Categorical preprocessing
# ---------------------------------------------------------
categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
        ),
    ]
)


# ---------------------------------------------------------
# Combined preprocessing
# ---------------------------------------------------------
preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            numeric_features,
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features,
        ),
    ],
    remainder="drop",
)


# ---------------------------------------------------------
# Baseline Logistic Regression
#
# class_weight="balanced" is important because only ~3.2%
# of the training examples represent future dropout.
# ---------------------------------------------------------
model = LogisticRegression(
    class_weight="balanced",
    max_iter=1000,
    random_state=42,
)


# ---------------------------------------------------------
# Complete ML pipeline
# ---------------------------------------------------------
pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor,
        ),
        (
            "model",
            model,
        ),
    ]
)


# ---------------------------------------------------------
# Train
# ---------------------------------------------------------
print("\n--- TRAINING ---")

pipeline.fit(
    X_train,
    y_train,
)

print("Training complete.")


# ---------------------------------------------------------
# Predictions
# ---------------------------------------------------------
y_pred = pipeline.predict(X_test)
y_probability = pipeline.predict_proba(X_test)[:, 1]


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------
roc_auc = roc_auc_score(
    y_test,
    y_probability,
)

pr_auc = average_precision_score(
    y_test,
    y_probability,
)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0,
)


print("\n========================================")
print("        BASELINE MODEL RESULTS")
print("========================================")

print(f"ROC-AUC:  {roc_auc:.4f}")
print(f"PR-AUC:   {pr_auc:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-score:  {f1:.4f}")


# ---------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------
print("\n--- CONFUSION MATRIX ---")

cm = confusion_matrix(
    y_test,
    y_pred,
)

print(cm)

print("\nFormat:")
print("[[TN  FP]")
print(" [FN  TP]]")


# ---------------------------------------------------------
# Classification report
# ---------------------------------------------------------
print("\n--- CLASSIFICATION REPORT ---")

print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "No Future Dropout",
            "Future Dropout",
        ],
        zero_division=0,
    )
)


# ---------------------------------------------------------
# Actual class distribution
# ---------------------------------------------------------
print("\n--- TEST SET ---")
print(f"Actual dropout cases: {y_test.sum():,}")
print(f"Actual non-dropout cases: {(y_test == 0).sum():,}")
print(f"Predicted dropout cases: {y_pred.sum():,}")

print("\nSUCCESS: Baseline model trained and evaluated.")