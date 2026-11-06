
from fastapi import FastAPI

from retention_intelligence.api.routes.customers import (
    router as customer_router
)


app = FastAPI(
    title="Customer Churn & Retention API",
    description=(
        "API for customer churn prediction, "
        "fulfilment investigation and retention intelligence"
    ),
    version="1.0.0"
)


app.include_router(customer_router)


@app.get("/")
def home():
    return {
        "message": "Customer Churn & Retention API is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "churn-retention-api"
    }
