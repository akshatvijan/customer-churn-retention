
from retention_intelligence.decision.decision_agent import (
    decision_engine_agent
)


def test_decision_agent_with_valid_actions():

    state = {
        "customer_data": {
            "days_since_last_order": 160,
            "retention_risk_proxy": 1,
            "cancelled_orders": 2
        },
        "candidate_actions": [
            {
                "action_type": "personalised_reengagement",
                "description": "Send re-engagement message",
                "reason": "Customer inactivity",
                "requires_approval": True
            }
        ]
    }

    result = decision_engine_agent(state)

    assert len(result["feasible_actions"]) == 1
    assert result["rejected_actions"] == []
    assert result["review_actions"] == []
    assert result["errors"] == []


def test_decision_agent_with_no_actions():

    state = {
        "customer_data": {
            "days_since_last_order": 160
        },
        "candidate_actions": []
    }

    result = decision_engine_agent(state)

    assert result["feasible_actions"] == []
    assert result["rejected_actions"] == []
    assert result["review_actions"] == []
    assert len(result["errors"]) == 1


def test_decision_agent_with_loyalty_reward():

    state = {
        "customer_data": {
            "days_since_last_order": 160
        },
        "candidate_actions": [
            {
                "action_type": "loyalty_reward",
                "description": "Consider loyalty reward",
                "reason": "Retention opportunity",
                "requires_approval": True
            }
        ]
    }

    result = decision_engine_agent(state)

    assert len(result["review_actions"]) == 1
    assert result["feasible_actions"] == []


def test_decision_agent_with_unsupported_action():

    state = {
        "customer_data": {},
        "candidate_actions": [
            {
                "action_type": "automatic_discount",
                "description": "Give discount",
                "reason": "Customer inactive",
                "requires_approval": True
            }
        ]
    }

    result = decision_engine_agent(state)

    assert len(result["rejected_actions"]) == 1
    assert result["feasible_actions"] == []


def test_decision_agent_returns_policy_result():

    state = {
        "customer_data": {
            "days_since_last_order": 160
        },
        "candidate_actions": [
            {
                "action_type": "personalised_reengagement",
                "description": "Send message",
                "reason": "Customer inactivity",
                "requires_approval": True
            }
        ]
    }

    result = decision_engine_agent(state)

    assert "policy_result" in result
    assert "feasible_actions" in result["policy_result"]
    assert "rejected_actions" in result["policy_result"]
    assert "review_actions" in result["policy_result"]
