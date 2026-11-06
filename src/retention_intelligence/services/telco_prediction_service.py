import joblib
import pandas as pd

from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[3]

MODEL_PATH = BASE_DIR / "models" / "churn_model.joblib"


# Load trained ML pipeline
model = joblib.load(MODEL_PATH)


def predict_telco_churn(customer_data: dict):

    customer_data = customer_data.copy()

    # Extract customer ID
    customer_id = customer_data.pop("customer_id")

    # Remove actual churn label
    customer_data.pop("Churn", None)
    customer_data.pop("churn", None)

    # Convert input into DataFrame
    input_df = pd.DataFrame([customer_data])

    # Get churn probability
    churn_probability = float(
        model.predict_proba(input_df)[0][1]
    )

    # Apply selected threshold
    churn_prediction = int(churn_probability >= 0.40)

    # Determine risk level
    if churn_probability >= 0.60:
        risk_level = "high"

    elif churn_probability >= 0.40:
        risk_level = "medium"

    else:
        risk_level = "low"

    return {
        "customer_id": customer_id,
        "churn_prediction": churn_prediction,
        "churn_probability": round(churn_probability, 4),
        "risk_level": risk_level,
        "message": (
            "Customer is likely to churn"
            if churn_prediction == 1
            else "Customer is unlikely to churn"
        )
    }