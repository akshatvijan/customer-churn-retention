
import pytest
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace

from retention_intelligence.agents.fulfilment_agent import (
    fulfilment_agent
)


@pytest.mark.asyncio
async def test_fulfilment_agent_success():

    state = {
        "source": "olist",
        "customer_data": {
            "customer_unique_id": "test_customer",
            "total_orders": 1,
            "delivered_orders": 1,
            "cancelled_orders": 0,
            "last_order_date": "2018-05-10 10:56:27",
            "average_order_value": 141.9,
            "days_since_last_order": 160,
            "retention_risk_proxy": "high_inactivity"
        }
    }

    mock_knowledge = [
        {
            "text": "Long inactivity may indicate reduced engagement.",
            "category": "inactivity",
            "source": "project_playbook",
            "metadata": {},
            "similarity_score": 0.75
        }
    ]

    mock_response = SimpleNamespace(
        content="Customer shows an inactivity signal."
    )

    mock_model = SimpleNamespace(
        ainvoke=AsyncMock(return_value=mock_response)
    )

    with patch(
        "retention_intelligence.agents.fulfilment_agent.retrieve_knowledge",
        return_value=mock_knowledge
    ), patch(
        "retention_intelligence.agents.fulfilment_agent.model",
        new=mock_model
    ):

        result = await fulfilment_agent(state)

    assert result["errors"] == []

    assert (
        result["fulfilment_evidence"]["total_orders"] == 1
    )

    assert (
        result["fulfilment_evidence"]["retention_risk_proxy"]
        == "high_inactivity"
    )

    assert len(result["retrieved_knowledge"]) == 1

    assert (
        result["fulfilment_analysis"]["investigation"]
        == "Customer shows an inactivity signal."
    )


@pytest.mark.asyncio
async def test_fulfilment_agent_wrong_source():

    state = {
        "source": "telco",
        "customer_data": {
            "customerID": "7590-VHVEG"
        }
    }

    result = await fulfilment_agent(state)

    assert result["fulfilment_evidence"] == {}

    assert result["fulfilment_analysis"] == {}

    assert "Olist only" in result["errors"][0]


@pytest.mark.asyncio
async def test_fulfilment_agent_missing_customer_data():

    state = {
        "source": "olist",
        "customer_data": {}
    }

    result = await fulfilment_agent(state)

    assert result["fulfilment_evidence"] == {}

    assert result["fulfilment_analysis"] == {}

    assert "Customer data is missing" in result["errors"]


@pytest.mark.asyncio
async def test_fulfilment_agent_missing_customer_id():

    state = {
        "source": "olist",
        "customer_data": {
            "total_orders": 1
        }
    }

    result = await fulfilment_agent(state)

    assert result["fulfilment_evidence"] == {}

    assert result["fulfilment_analysis"] == {}

    assert "Olist customer ID is missing" in result["errors"]


@pytest.mark.asyncio
async def test_fulfilment_agent_rag_failure():

    state = {
        "source": "olist",
        "customer_data": {
            "customer_unique_id": "test_customer",
            "total_orders": 1,
            "delivered_orders": 1,
            "cancelled_orders": 0,
            "last_order_date": "2018-05-10 10:56:27",
            "average_order_value": 141.9,
            "days_since_last_order": 160,
            "retention_risk_proxy": "high_inactivity"
        }
    }

    with patch(
        "retention_intelligence.agents.fulfilment_agent.retrieve_knowledge",
        side_effect=RuntimeError("Milvus connection failed")
    ):

        result = await fulfilment_agent(state)

    assert result["fulfilment_evidence"] == {}

    assert result["fulfilment_analysis"] == {}

    assert "Milvus connection failed" in result["errors"][0]
