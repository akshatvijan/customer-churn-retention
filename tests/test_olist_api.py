
from fastapi.testclient import TestClient

from retention_intelligence.api.main import app

client = TestClient(app)


def test_get_olist_customers():
    response = client.get("/api/v1/customers/olist")

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "olist"
    assert len(data["data"]) <= 100
    assert data["total_records"] == len(data["data"])

    if data["data"]:
        customer = data["data"][0]

        assert "customer_id" in customer
        assert "total_orders" in customer
        assert "delivered_orders" in customer
        assert "cancelled_orders" in customer
        assert "retention_risk_proxy" in customer
        assert "days_since_last_order" in customer
