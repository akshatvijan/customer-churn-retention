
from fastapi.testclient import TestClient

from retention_intelligence.api.main import app

client = TestClient(app)


def test_get_telco_customers():
    response = client.get("/api/v1/customers/telco")

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "telco"
    assert "total_records" in data
    assert "data" in data


def test_telco_prediction_invalid_input():
    response = client.post(
        "/api/v1/customers/telco/predict",
        json={}
    )

    assert response.status_code == 422
