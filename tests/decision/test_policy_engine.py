
import pytest

from retention_intelligence.decision.policy_engine import (
    evaluate_candidate_action,
    evaluate_candidate_actions
)


@pytest.fixture
def customer_data():
    return {
        "days_since_last_order": 160,
        "retention_risk_proxy": 1,
        "cancelled_orders": 2
    }


def test_reengagement_is_feasible(customer_data):
    action = {
        "action_type": "personalised_reengagement",
        "description": "Send re-engagement message",
        "reason": "Customer inactive for 160 days",
        "requires_approval": True
    }

    result = evaluate_candidate_action(action, customer_data)

    assert result["status"] == "feasible"


def test_reengagement_without_evidence_requires_review():
    action = {
        "action_type": "personalised_reengagement",
        "description": "Send message",
        "reason": "Retention opportunity",
        "requires_approval": True
    }

    result = evaluate_candidate_action(action, {})

    assert result["status"] == "requires_review"


def test_support_followup_is_feasible(customer_data):
    action = {
        "action_type": "customer_support_followup",
        "description": "Contact customer",
        "reason": "Previous cancellations",
        "requires_approval": True
    }

    result = evaluate_candidate_action(action, customer_data)

    assert result["status"] == "feasible"


def test_loyalty_reward_requires_review(customer_data):
    action = {
        "action_type": "loyalty_reward",
        "description": "Consider loyalty reward",
        "reason": "Retention opportunity",
        "requires_approval": True
    }

    result = evaluate_candidate_action(action, customer_data)

    assert result["status"] == "requires_review"


def test_product_recommendation_requires_review(customer_data):
    action = {
        "action_type": "product_recommendation",
        "description": "Recommend a product",
        "reason": "Retention opportunity",
        "requires_approval": True
    }

    result = evaluate_candidate_action(action, customer_data)

    assert result["status"] == "requires_review"


def test_unsupported_action_is_rejected(customer_data):
    action = {
        "action_type": "automatic_discount",
        "description": "Give discount",
        "reason": "Customer inactive",
        "requires_approval": True
    }

    result = evaluate_candidate_action(action, customer_data)

    assert result["status"] == "rejected"


def test_missing_description_is_invalid(customer_data):
    action = {
        "action_type": "personalised_reengagement",
        "description": "",
        "reason": "Customer inactive",
        "requires_approval": True
    }

    result = evaluate_candidate_action(action, customer_data)

    assert result["status"] == "invalid"


def test_approval_is_mandatory(customer_data):
    action = {
        "action_type": "personalised_reengagement",
        "description": "Send message",
        "reason": "Customer inactive",
        "requires_approval": False
    }

    result = evaluate_candidate_action(action, customer_data)

    assert result["status"] == "rejected"


def test_evaluate_multiple_actions(customer_data):
    actions = [
        {
            "action_type": "personalised_reengagement",
            "description": "Send message",
            "reason": "High inactivity",
            "requires_approval": True
        },
        {
            "action_type": "loyalty_reward",
            "description": "Consider reward",
            "reason": "Retention opportunity",
            "requires_approval": True
        },
        {
            "action_type": "automatic_discount",
            "description": "Give discount",
            "reason": "Inactive customer",
            "requires_approval": True
        }
    ]

    result = evaluate_candidate_actions(actions, customer_data)

    assert len(result["feasible_actions"]) == 1
    assert len(result["review_actions"]) == 1
    assert len(result["rejected_actions"]) == 1
    assert result["errors"] == []


def test_invalid_actions_input():
    result = evaluate_candidate_actions(
        "not a list",
        {}
    )

    assert result["feasible_actions"] == []
    assert len(result["errors"]) == 1
