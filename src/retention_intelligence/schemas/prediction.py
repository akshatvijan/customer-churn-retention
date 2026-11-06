
from pydantic import BaseModel, Field
from typing import Literal


# 1. Telco Churn Prediction Request

class ChurnPredictionRequest(BaseModel):

    customer_id: str = Field(min_length=1)

    gender: Literal["Male", "Female"]
    SeniorCitizen: Literal[0, 1]
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int = Field(ge=0)

    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]

    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]

    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]

    PaymentMethod: Literal[
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)"
    ]

    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float = Field(ge=0)

    class Config:
        extra = "forbid"


# 2. Telco Churn Prediction Response

class ChurnPredictionResponse(BaseModel):

    customer_id: str
    churn_prediction: int
    churn_probability: float
    risk_level: str
    message: str


# 3. Olist Retention Risk Request

class OlistRetentionRequest(BaseModel):

    customer_unique_id: str = Field(min_length=1)

    total_orders: int = Field(ge=0)
    delivered_orders: int = Field(ge=0)
    cancelled_orders: int = Field(ge=0)

    last_order_date: str

    average_order_value: float = Field(ge=0)

    days_since_last_order: int = Field(ge=0)

    retention_risk_proxy: Literal[
        "high_inactivity",
        "monitor",
        "at_risk",
        "recent"
    ]

    class Config:
        extra = "forbid"


# 4. Olist Retention Risk Response

class OlistRetentionResponse(BaseModel):

    customer_id: str
    retention_risk_proxy: str
    days_since_last_order: int
    risk_level: str
    message: str
