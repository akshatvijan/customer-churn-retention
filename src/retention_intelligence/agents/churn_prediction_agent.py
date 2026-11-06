from retention_intelligence.agents.state import RetentionState

from retention_intelligence.services.telco_prediction_service import (
    predict_telco_churn
)


async def churn_prediction_agent(state: RetentionState):

    source = state.get("source")
    customer_data = state.get("customer_data", {})

    if not customer_data:
        return {
            "churn_prediction": {},
            "errors": ["Customer profile is missing"]
        }

    try:

        # Olist: Use existing inactivity risk proxy
        if source == "olist":

            return {
                "churn_prediction": {
                    "source": "olist",
                    "risk_type": "inactivity_proxy",
                    "risk_level": customer_data.get(
                        "retention_risk_proxy"
                    ),
                    "days_since_last_order": customer_data.get(
                        "days_since_last_order"
                    ),
                    "total_orders": customer_data.get(
                        "total_orders"
                    ),
                    "note": (
                        "Inactivity-based retention risk proxy, "
                        "not an observed churn prediction."
                    )
                },
                "errors": []
            }

        # Telco: Use existing trained ML pipeline
        elif source == "telco":

            prediction = predict_telco_churn(customer_data)

            return {
                "churn_prediction": {
                    "source": "telco",
                    **prediction
                },    
                "errors": []
            }

        else:

            return {
                "churn_prediction": {},
                "errors": ["Unsupported customer source"]
            }

    except Exception as error:

        return {
            "churn_prediction": {},
            "errors": [
                f"Churn Prediction Agent failed: {str(error)}"
            ]
        }