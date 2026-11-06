
from retention_intelligence.decision.human_approval_agent import (
    human_approval_agent
)


def test_feasible_action_goes_for_approval():

    state = {
        "feasible_actions": [
            {
                "action": {
                    "action_type": "personalised_reengagement",
                    "description": "Send re-engagement message"
                },
                "policy_reason": "Inactivity evidence available"
            }
        ]
    }

    result = human_approval_agent(state)

    assert result["human_approval"]["status"] == "pending"
    assert len(result["human_approval"]["pending_actions"]) == 1


def test_no_feasible_actions():

    state = {
        "feasible_actions": []
    }

    result = human_approval_agent(state)

    assert result["human_approval"]["status"] == "not_required"
    assert result["human_approval"]["pending_actions"] == []


def test_invalid_action_is_skipped():

    state = {
        "feasible_actions": [
            {"invalid": "data"}
        ]
    }

    result = human_approval_agent(state)

    assert result["human_approval"]["status"] == "not_required"
    assert result["human_approval"]["pending_actions"] == []


def test_multiple_actions_go_for_approval():

    state = {
        "feasible_actions": [
            {
                "action": {
                    "action_type": "personalised_reengagement",
                    "description": "Send message"
                },
                "policy_reason": "Inactivity evidence available"
            },
            {
                "action": {
                    "action_type": "customer_support_followup",
                    "description": "Contact customer"
                },
                "policy_reason": "Cancellation evidence available"
            }
        ]
    }

    result = human_approval_agent(state)

    assert len(result["human_approval"]["pending_actions"]) == 2
    assert result["human_approval"]["status"] == "pending"


def test_approval_status_is_pending():

    state = {
        "feasible_actions": [
            {
                "action": {
                    "action_type": "personalised_reengagement",
                    "description": "Send message"
                },
                "policy_reason": "Inactivity evidence available"
            }
        ]
    }

    result = human_approval_agent(state)

    pending_action = result["human_approval"]["pending_actions"][0]

    assert pending_action["status"] == "pending"
    assert pending_action["policy_reason"] == "Inactivity evidence available"
