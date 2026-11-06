
import pytest
from unittest.mock import AsyncMock, patch

from retention_intelligence.graph.workflow import (
    build_retention_workflow
)


@pytest.mark.asyncio
async def test_olist_workflow():

    mock_profile = AsyncMock(return_value={
        "customer_data": {
            "customer_unique_id": "test_customer",
            "total_orders": 1
        },
        "errors": []
    })

    mock_churn = AsyncMock(return_value={
        "churn_prediction": {
            "risk_level": "high_inactivity"
        },
        "errors": []
    })

    mock_fulfilment = AsyncMock(return_value={
        "fulfilment_analysis": {
            "investigation": "Inactivity detected."
        },
        "errors": []
    })

    with patch(
        "retention_intelligence.graph.workflow.customer_profile_agent",
        mock_profile
    ), patch(
        "retention_intelligence.graph.workflow.churn_prediction_agent",
        mock_churn
    ), patch(
        "retention_intelligence.graph.workflow.fulfilment_agent",
        mock_fulfilment
    ):

        app = build_retention_workflow()

        result = await app.ainvoke({
            "customer_id": "test_customer",
            "source": "olist"
        })

    mock_profile.assert_awaited_once()
    mock_churn.assert_awaited_once()
    mock_fulfilment.assert_awaited_once()

    assert result["fulfilment_analysis"]["investigation"] == (
        "Inactivity detected."
    )


@pytest.mark.asyncio
async def test_telco_workflow():

    mock_profile = AsyncMock(return_value={
        "customer_data": {
            "customerID": "7590-VHVEG"
        },
        "errors": []
    })

    mock_churn = AsyncMock(return_value={
        "churn_prediction": {
            "risk_level": "high"
        },
        "errors": []
    })

    mock_fulfilment = AsyncMock(return_value={
        "fulfilment_analysis": {},
        "errors": []
    })

    with patch(
        "retention_intelligence.graph.workflow.customer_profile_agent",
        mock_profile
    ), patch(
        "retention_intelligence.graph.workflow.churn_prediction_agent",
        mock_churn
    ), patch(
        "retention_intelligence.graph.workflow.fulfilment_agent",
        mock_fulfilment
    ):

        app = build_retention_workflow()

        result = await app.ainvoke({
            "customer_id": "7590-VHVEG",
            "source": "telco"
        })

    mock_profile.assert_awaited_once()
    mock_churn.assert_awaited_once()

    # Telco should skip the Olist-only Fulfilment Agent
    mock_fulfilment.assert_not_awaited()

    assert result["churn_prediction"]["risk_level"] == "high"
