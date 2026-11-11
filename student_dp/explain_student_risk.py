import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "student" / "dropout_model_dataset_v2.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "student_success_model.joblib"
MODEL_DIR = PROJECT_ROOT / "models"
EXPLANATIONS_DIR = MODEL_DIR / "student_explanations"
EXPLANATIONS_DIR.mkdir(exist_ok=True)
VALIDATION_CSV = MODEL_DIR / "student_explanation_validation.csv"

# ---------------------------------------------------------
# Risk Level Classifier Helper
# ---------------------------------------------------------
def get_risk_level(prob):
    if prob >= 0.60:
        return "HIGH"
    elif prob >= 0.40:
        return "MEDIUM"
    else:
        return "LOW"

# ---------------------------------------------------------
# Main Explanation Function
# ---------------------------------------------------------
def explain_student(pipeline, df, student_id, save_json=True, verbose=True):
    # Filter records for student
    student_records = df[df["student_id"] == student_id].sort_values(by="semester", ascending=True)
    if student_records.empty:
        raise ValueError(f"Student ID '{student_id}' not found in dataset.")

    # Select the most recent semester record valid for prediction
    latest_record = student_records.iloc[[-1]].copy()
    semester_num = int(latest_record["semester"].values[0])

    # Prepare features matching model pipeline
    X_record = latest_record.drop(columns=["future_dropout", "student_id", "state"], errors="ignore")

    # Predict probabilities
    prob = float(pipeline.predict_proba(X_record)[0, 1])
    retention_prob = float(1.0 - prob)
    risk_level = get_risk_level(prob)

    # Extract pipeline components
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    # Transform record and extract preprocessed feature names
    X_trans = preprocessor.transform(X_record)
    feature_names = preprocessor.get_feature_names_out()
    coefs = classifier.coef_[0]

    # Calculate contribution = coef * transformed_value
    contributions = coefs * X_trans[0]

    # List of categorical feature names to match one-hot columns
    known_cats = [
        "fee_payment_status", "internship_status", "department_id", "program",
        "specialization", "admission_type", "gender",
        "scholarship_type", "family_income_band"
    ]

    raw_contributions = []

    for name, val_trans, contrib in zip(feature_names, X_trans[0], contributions):
        if abs(contrib) < 1e-6:
            continue

        if name.startswith("num__"):
            raw_feature = name.replace("num__", "")
            student_val = latest_record[raw_feature].values[0] if raw_feature in latest_record.columns else val_trans
            # Format display value cleanly
            if isinstance(student_val, (float, np.floating)):
                display_val = float(round(student_val, 2))
            elif isinstance(student_val, (int, np.integer)):
                display_val = int(student_val)
            else:
                display_val = str(student_val)

            raw_contributions.append({
                "feature": raw_feature,
                "value": display_val,
                "contribution": float(round(contrib, 4)),
                "direction": "increases_risk" if contrib > 0 else "reduces_risk"
            })

        elif name.startswith("cat__"):
            # Identify which known categorical feature this column belongs to
            matched_cat = None
            for cat in known_cats:
                prefix = f"cat__{cat}_"
                if name.startswith(prefix):
                    matched_cat = cat
                    cat_val = name[len(prefix):]
                    break

            if matched_cat and val_trans > 0:
                raw_contributions.append({
                    "feature": matched_cat,
                    "value": cat_val,
                    "contribution": float(round(contrib, 4)),
                    "direction": "increases_risk" if contrib > 0 else "reduces_risk"
                })

    # Sort risk factors (positive contribution) and protective factors (negative contribution)
    risk_factors = sorted(
        [c for c in raw_contributions if c["direction"] == "increases_risk"],
        key=lambda x: x["contribution"],
        reverse=True
    )

    protective_factors = sorted(
        [c for c in raw_contributions if c["direction"] == "reduces_risk"],
        key=lambda x: x["contribution"]
    )

    explanation_payload = {
        "student_id": student_id,
        "semester": semester_num,
        "dropout_probability": round(prob, 4),
        "retention_probability": round(retention_prob, 4),
        "risk_level": risk_level,
        "risk_factors": risk_factors[:5],
        "protective_factors": protective_factors[:5]
    }

    if save_json:
        json_path = EXPLANATIONS_DIR / f"{student_id}.json"
        with open(json_path, "w") as f:
            json.dump(explanation_payload, f, indent=2)
        if verbose:
            print(f"Saved explanation JSON to: {json_path}")

    if verbose:
        print("\n" + "=" * 60)
        print(f"STUDENT DROPOUT RISK EXPLANATION: {student_id}")
        print("=" * 60)
        print(f"Semester: {semester_num}")
        print(f"Dropout Risk Probability : {prob:.2%}")
        print(f"Retention Probability    : {retention_prob:.2%}")
        print(f"Operational Risk Level   : {risk_level}")

        print("\nTop Risk Factors (Increasing Dropout Risk):")
        if risk_factors:
            for idx, rf in enumerate(risk_factors[:5], 1):
                print(f"  {idx}. {rf['feature']} = {rf['value']} (Contribution: +{rf['contribution']:.4f})")
        else:
            print("  None detected.")

        print("\nTop Protective Factors (Reducing Dropout Risk):")
        if protective_factors:
            for idx, pf in enumerate(protective_factors[:5], 1):
                print(f"  {idx}. {pf['feature']} = {pf['value']} (Contribution: {pf['contribution']:.4f})")
        else:
            print("  None detected.")
        print("=" * 60)

    return explanation_payload

# ---------------------------------------------------------
# CLI Execution & Representative Validation
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Explain Student Dropout Risk")
    parser.add_argument("student_id", nargs="?", type=str, help="Student ID to explain (e.g. STU00042)")
    args = parser.parse_args()

    # Load model and dataset
    pipeline = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)

    # Feature engineering matching train_student_success.py
    if "date_of_birth" in df.columns:
        df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
        df["age"] = df["academic_year"] - df["date_of_birth"].dt.year
        df = df.drop(columns=["date_of_birth"])

    bool_cols = ["scholarship_status", "hostel_status"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # Replicate test split to find representative test students
    TARGET = "future_dropout"
    y = df[TARGET]
    groups = df["student_id"]
    X = df.drop(columns=[TARGET, "student_id", "state"], errors="ignore")

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    test_df = df.iloc[test_idx].copy()

    # Select latest record per test student
    latest_test_df = test_df.sort_values(by="semester", ascending=True).groupby("student_id").last().reset_index()
    latest_test_df["pred_prob"] = pipeline.predict_proba(
        latest_test_df.drop(columns=[TARGET, "student_id", "state"], errors="ignore")
    )[:, 1]
    latest_test_df["pred_risk_level"] = latest_test_df["pred_prob"].apply(get_risk_level)

    # If specific student requested via CLI
    if args.student_id:
        explain_student(pipeline, df, args.student_id, save_json=True, verbose=True)

    # Automatically select 3 representative test students (LOW, MEDIUM, HIGH)
    print("\nRunning representative 3-student validation (LOW, MEDIUM, HIGH risk)...")
    
    low_student = latest_test_df[latest_test_df["pred_risk_level"] == "LOW"].iloc[0]["student_id"]
    med_student = latest_test_df[latest_test_df["pred_risk_level"] == "MEDIUM"].iloc[0]["student_id"]
    high_student = latest_test_df[latest_test_df["pred_risk_level"] == "HIGH"].iloc[0]["student_id"]

    validation_targets = [low_student, med_student, high_student]
    validation_rows = []

    for sid in validation_targets:
        payload = explain_student(pipeline, df, sid, save_json=True, verbose=True)
        r_factors = payload["risk_factors"]
        rf1 = f"{r_factors[0]['feature']} ({r_factors[0]['value']})" if len(r_factors) > 0 else "None"
        rf2 = f"{r_factors[1]['feature']} ({r_factors[1]['value']})" if len(r_factors) > 1 else "None"
        rf3 = f"{r_factors[2]['feature']} ({r_factors[2]['value']})" if len(r_factors) > 2 else "None"

        validation_rows.append({
            "student_id": payload["student_id"],
            "semester": payload["semester"],
            "probability": payload["dropout_probability"],
            "risk_level": payload["risk_level"],
            "top_risk_factor_1": rf1,
            "top_risk_factor_2": rf2,
            "top_risk_factor_3": rf3,
        })

    val_df = pd.DataFrame(validation_rows)
    val_df.to_csv(VALIDATION_CSV, index=False)

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY (SAVED TO models/student_explanation_validation.csv)")
    print("=" * 70)
    print(val_df.to_string(index=False))

if __name__ == "__main__":
    main()
