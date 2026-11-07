
from pathlib import Path
from functools import lru_cache


BASE_DIR = Path.cwd()
MODEL_PATH = BASE_DIR / "models" / "churn_model.joblib"


@lru_cache(maxsize=1)
def load_churn_model():
    import joblib

    return joblib.load(MODEL_PATH)


def predict_telco_churn(customer_data: dict):

    import pandas as pd

    customer_data = customer_data.copy()

    # Extract customer ID
    customer_id = customer_data.pop("customer_id")

    # Remove actual churn label
    customer_data.pop("Churn", None)
    customer_data.pop("churn", None)

    # Convert input into DataFrame
    input_df = pd.DataFrame([customer_data])

    # Load model only when prediction is requested
    model = load_churn_model()

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
