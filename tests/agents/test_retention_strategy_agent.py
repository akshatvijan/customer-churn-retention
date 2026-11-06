
import json

import pytest

from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

from retention_intelligence.agents.retention_strategy_agent import (
    retention_strategy_agent
)


@pytest.fixture
def valid_state():

    return {
        "source": "olist",
        "customer_id": "test_customer",

        "customer_data": {
            "customer_unique_id": "test_customer",
            "total_orders": 1,
            "delivered_orders": 1,
            "cancelled_orders": 0,
            "last_order_date": "2018-05-10 10:56:27",
            "average_order_value": 141.9,
            "days_since_last_order": 160,
            "retention_risk_proxy": "high_inactivity"
        },

        "churn_prediction": {
            "risk_type": "inactivity_proxy",
            "risk_level": "high",
            "days_since_last_order": 160
        },

        "fulfilment_analysis": {
            "investigation": "High inactivity signal detected."
        }
    }


@pytest.fixture
def mock_knowledge():

    return [
        {
            "text": "Consider personalised re-engagement for inactive customers.",
            "category": "retention_strategy",
            "source": "project_retention_playbook",
            "metadata": {},
            "similarity_score": 0.75
        }
    ]


@pytest.fixture
def valid_llm_response():

    return {
        "strategy_summary": "Customer shows high inactivity.",
        "candidate_actions": [
            {
                "action_type": "personalised_reengagement",
                "description": "Send a personalised re-engagement message.",
                "reason": "Customer has been inactive for 160 days.",
                "priority": "high",
                "requires_approval": True
            }
        ],
        "evidence_limitations": [
            "Customer product preferences are unavailable."
        ]
    }


@pytest.mark.asyncio
async def test_retention_strategy_success(
    valid_state,
    mock_knowledge,
    valid_llm_response
):

    mock_response = SimpleNamespace(
        content=json.dumps(valid_llm_response)
    )

    mock_model = SimpleNamespace(
        ainvoke=AsyncMock(return_value=mock_response)
    )

    with patch(
        "retention_intelligence.agents.retention_strategy_agent.retrieve_knowledge",
        return_value=mock_knowledge
    ), patch(
        "retention_intelligence.agents.retention_strategy_agent.model",
        new=mock_model
    ):

        result = await retention_strategy_agent(valid_state)

    assert result["errors"] == []

    assert len(result["candidate_actions"]) == 1

    action = result["candidate_actions"][0]

    assert action["action_type"] == "personalised_reengagement"
    assert action["priority"] == "high"
    assert action["requires_approval"] is True
    assert action["status"] == "candidate"

    assert result["retention_strategy"]["customer_id"] == "test_customer"

    assert (
        result["retention_strategy"]["knowledge_sources"][0]["category"]
        == "retention_strategy"
    )

    mock_model.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_customer_data(valid_state):

    valid_state["customer_data"] = {}

    result = await retention_strategy_agent(valid_state)

    assert result["candidate_actions"] == []
    assert result["retention_strategy"] == {}

    assert "Customer data is missing" in result["errors"]


@pytest.mark.asyncio
async def test_missing_churn_prediction(valid_state):

    valid_state["churn_prediction"] = {}

    result = await retention_strategy_agent(valid_state)

    assert result["candidate_actions"] == []
    assert result["retention_strategy"] == {}

    assert "Churn prediction is missing" in result["errors"]


@pytest.mark.asyncio
async def test_rag_failure(
    valid_state
):

    with patch(
        "retention_intelligence.agents.retention_strategy_agent.retrieve_knowledge",
        side_effect=RuntimeError("Milvus connection failed")
    ):

        result = await retention_strategy_agent(valid_state)

    assert result["candidate_actions"] == []
    assert result["retention_strategy"] == {}

    assert "Milvus connection failed" in result["errors"][0]


@pytest.mark.asyncio
async def test_invalid_action_type(
    valid_state,
    mock_knowledge
):

    invalid_response = {
        "strategy_summary": "Test strategy",
        "candidate_actions": [
            {
                "action_type": "automatic_discount",
                "description": "Give automatic discount.",
                "reason": "Invalid action type.",
                "priority": "high",
                "requires_approval": True
            }
        ],
        "evidence_limitations": []
    }

    mock_response = SimpleNamespace(
        content=json.dumps(invalid_response)
    )

    mock_model = SimpleNamespace(
        ainvoke=AsyncMock(return_value=mock_response)
    )

    with patch(
        "retention_intelligence.agents.retention_strategy_agent.retrieve_knowledge",
        return_value=mock_knowledge
    ), patch(
        "retention_intelligence.agents.retention_strategy_agent.model",
        new=mock_model
    ):

        result = await retention_strategy_agent(valid_state)

    assert result["candidate_actions"] == []
    assert result["retention_strategy"] == {}

    assert (
        "No valid retention candidate actions generated"
        in result["errors"][0]
    )
