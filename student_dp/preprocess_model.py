from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
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
# Load split datasets
# ---------------------------------------------------------
train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

print(f"Training records: {len(train_df):,}")
print(f"Testing records:  {len(test_df):,}")


# ---------------------------------------------------------
# Create age feature
#
# We don't want to feed the raw date of birth to the model.
# Use admission year as a simple reference because the
# prediction dataset spans multiple academic years.
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
# Separate features and target
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
# Convert boolean features to numeric 0/1
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
    include=["int64", "float64", "int32", "float32"]
).columns.tolist()

categorical_features = X_train.select_dtypes(
    include=["object"]
).columns.tolist()

boolean_features = []

print("\n--- FEATURE TYPES ---")
print(f"Numeric:     {len(numeric_features)}")
print(f"Categorical: {len(categorical_features)}")
print(f"Boolean:     {len(boolean_features)}")

print("\nNumeric features:")
print(numeric_features)

print("\nCategorical features:")
print(categorical_features)

print("\nBoolean features:")
print(boolean_features)


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
# FIT ONLY ON TRAINING DATA
# ---------------------------------------------------------
X_train_processed = preprocessor.fit_transform(X_train)

X_test_processed = preprocessor.transform(X_test)


# ---------------------------------------------------------
# Convert boolean columns to numeric-compatible values
# ---------------------------------------------------------
X_train_processed = X_train_processed.astype("float32")
X_test_processed = X_test_processed.astype("float32")


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------
print("\n--- PREPROCESSING RESULTS ---")
print(f"Original training features: {X_train.shape[1]}")
print(f"Original testing features:  {X_test.shape[1]}")

print(
    f"Processed training shape: "
    f"{X_train_processed.shape}"
)

print(
    f"Processed testing shape:  "
    f"{X_test_processed.shape}"
)

print(
    f"\nTraining target shape: "
    f"{y_train.shape}"
)

print(
    f"Testing target shape:  "
    f"{y_test.shape}"
)

print("\nSUCCESS: Preprocessing completed.")