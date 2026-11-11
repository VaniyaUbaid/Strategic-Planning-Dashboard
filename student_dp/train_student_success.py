from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "student" / "dropout_model_dataset_v2.csv"
MODEL_DIR = PROJECT_ROOT / "models"

MODEL_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------
# 1. Load dataset
# ---------------------------------------------------------

print("=" * 70)
print("STUDENT SUCCESS MODEL TRAINING PIPELINE (V2 DATASET)")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(f"\nDataset shape: {df.shape}")
print(f"Unique students: {df['student_id'].nunique()}")

print("\nTarget distribution:")
print(df["future_dropout"].value_counts())

print("\nTarget proportions:")
print(df["future_dropout"].value_counts(normalize=True))


# ---------------------------------------------------------
# 2. Basic feature engineering
# ---------------------------------------------------------

# Convert DOB into approximate age at the academic record.
if "date_of_birth" in df.columns:
    df["date_of_birth"] = pd.to_datetime(
        df["date_of_birth"],
        errors="coerce"
    )
    df["age"] = df["academic_year"] - df["date_of_birth"].dt.year
    df = df.drop(columns=["date_of_birth"])

# Convert boolean columns to 0/1 numeric integers
bool_cols = ["scholarship_status", "hostel_status"]
for col in bool_cols:
    if col in df.columns:
        df[col] = df[col].astype(int)


# ---------------------------------------------------------
# 3. Define target and groups
# ---------------------------------------------------------

TARGET = "future_dropout"
EXCLUDED_FEATURES = ["state"]

y = df[TARGET]

# student_id is needed for splitting but MUST NOT be a model feature.
groups = df["student_id"]

X = df.drop(
    columns=[
        TARGET,
        "student_id",
        *EXCLUDED_FEATURES,
    ]
)

assert not set(EXCLUDED_FEATURES).intersection(X.columns), (
    "Excluded features must not be passed to model training."
)


# ---------------------------------------------------------
# 4. Group-aware train/test split
# ---------------------------------------------------------

# GroupShuffleSplit prevents records belonging to the same student
# from appearing in both training and test sets.

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42,
)

train_idx, test_idx = next(
    splitter.split(X, y, groups=groups)
)

X_train = X.iloc[train_idx].copy()
X_test = X.iloc[test_idx].copy()

y_train = y.iloc[train_idx].copy()
y_test = y.iloc[test_idx].copy()

train_groups = groups.iloc[train_idx]
test_groups = groups.iloc[test_idx]


# ---------------------------------------------------------
# 5. Leakage verification
# ---------------------------------------------------------

overlap = set(train_groups).intersection(set(test_groups))

assert len(overlap) == 0, (
    "DATA LEAKAGE: students appear in both train and test sets."
)

print("\n" + "=" * 70)
print("TRAIN / TEST SPLIT VERIFICATION")
print("=" * 70)

print(f"Training rows: {len(X_train):,}")
print(f"Testing rows:  {len(X_test):,}")

print(f"Training students: {train_groups.nunique():,}")
print(f"Testing students:  {test_groups.nunique():,}")

print(f"Student overlap: {len(overlap)}")

print("\nTraining target distribution:")
print(y_train.value_counts(normalize=True))

print("\nTesting target distribution:")
print(y_test.value_counts(normalize=True))


# ---------------------------------------------------------
# 6. Identify feature types
# ---------------------------------------------------------

categorical_features = X_train.select_dtypes(
    include=["object", "category"]
).columns.tolist()

boolean_features = X_train.select_dtypes(
    include=["bool"]
).columns.tolist()

numerical_features = X_train.select_dtypes(
    include=["number"]
).columns.tolist()


print("\n" + "=" * 70)
print("FEATURE TYPES")
print("=" * 70)

print(f"Numerical features ({len(numerical_features)}):")
print(numerical_features)

print(f"\nCategorical features ({len(categorical_features)}):")
print(categorical_features)

print(f"\nBoolean features ({len(boolean_features)}):")
print(boolean_features)


# ---------------------------------------------------------
# 7. Preprocessing pipelines
# ---------------------------------------------------------

numeric_transformer = Pipeline(
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

categorical_transformer = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="constant",
                fill_value="Missing",
            ),
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

transformers = [
    (
        "num",
        numeric_transformer,
        numerical_features,
    ),
    (
        "cat",
        categorical_transformer,
        categorical_features,
    ),
]

if boolean_features:
    boolean_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
        ]
    )
    transformers.append(
        (
            "bool",
            boolean_transformer,
            boolean_features,
        )
    )

preprocessor = ColumnTransformer(
    transformers=transformers
)


# ---------------------------------------------------------
# 8. Define models
# ---------------------------------------------------------

models = {
    "Logistic Regression": LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        random_state=42,
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
    ),

    "HistGradientBoostingClassifier": HistGradientBoostingClassifier(
        class_weight="balanced",
        random_state=42,
    ),
}


# ---------------------------------------------------------
# 9. Train and evaluate
# ---------------------------------------------------------

results = []
trained_pipelines = {}

for model_name, model in models.items():

    print("\n" + "=" * 70)
    print(f"TRAINING: {model_name}")
    print("=" * 70)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", model),
        ]
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)
    roc_auc = roc_auc_score(y_test, probabilities)
    pr_auc = average_precision_score(y_test, probabilities)
    cm = confusion_matrix(y_test, predictions)

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            digits=4,
            zero_division=0,
        )
    )

    print("Confusion Matrix:")
    print(cm)

    print(f"\nAccuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"ROC-AUC  : {roc_auc:.4f}")
    print(f"PR-AUC   : {pr_auc:.4f}")

    results.append(
        {
            "Model": model_name,
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1": f1,
            "ROC_AUC": roc_auc,
            "PR_AUC": pr_auc,
        }
    )

    trained_pipelines[model_name] = pipeline


# ---------------------------------------------------------
# 10. Compare models
# ---------------------------------------------------------

results_df = pd.DataFrame(results)
results_df = results_df.sort_values(
    by="PR_AUC",
    ascending=False,
)

print("\n" + "=" * 70)
print("MODEL COMPARISON (SORTED BY PR-AUC)")
print("=" * 70)

print(
    results_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}",
    )
)


# ---------------------------------------------------------
# 11. Keep the deployed coefficient-explainable model consistent
#     with the Logistic Regression feature-insights API.
# ---------------------------------------------------------

best_model_name = "Logistic Regression"
best_pipeline = trained_pipelines[best_model_name]

print("\n" + "=" * 70)
print("DEPLOYED OPERATIONAL MODEL")
print("=" * 70)
print(f"Selected: {best_model_name}")


# ---------------------------------------------------------
# 12. Save model pipeline
# ---------------------------------------------------------

MODEL_PATH = MODEL_DIR / "student_success_model.joblib"

joblib.dump(
    best_pipeline,
    MODEL_PATH,
)

print(f"\nWinning model pipeline saved to:")
print(MODEL_PATH)


# ---------------------------------------------------------
# 13. Save evaluation results
# ---------------------------------------------------------

RESULTS_PATH = MODEL_DIR / "student_model_results.csv"

results_df.to_csv(
    RESULTS_PATH,
    index=False,
)

print(f"\nEvaluation results saved to:")
print(RESULTS_PATH)


# ---------------------------------------------------------
# 14. Predictions & Provisional Risk Allocation
# ---------------------------------------------------------

best_probabilities = best_pipeline.predict_proba(X_test)[:, 1]

preview = pd.DataFrame(
    {
        "student_id": test_groups.values,
        "actual_dropout": y_test.values,
        "dropout_probability": best_probabilities,
    }
)

preview["retention_probability"] = 1 - preview["dropout_probability"]


def provisional_risk_category(prob):
    if prob >= 0.60:
        return "HIGH"
    elif prob >= 0.40:
        return "MEDIUM"
    else:
        return "LOW"


preview["risk_level"] = preview["dropout_probability"].apply(provisional_risk_category)

print("\n" + "=" * 70)
print("SAMPLE STUDENT RISK PREDICTIONS (PROVISIONAL RISK LEVELS)")
print("=" * 70)

print(preview.head(20).to_string(index=False))

PREDICTIONS_PATH = MODEL_DIR / "student_risk_predictions.csv"

preview.to_csv(
    PREDICTIONS_PATH,
    index=False,
)

print(f"\nPredictions saved to:")
print(PREDICTIONS_PATH)

print("\nTraining completed successfully.")