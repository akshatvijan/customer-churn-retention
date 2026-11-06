
from typing import Any


ALLOWED_ACTION_TYPES = {
    "personalised_reengagement",
    "customer_support_followup",
    "loyalty_reward",
    "product_recommendation"
}


def evaluate_candidate_action(
    action: dict[str, Any],
    customer_data: dict[str, Any]
) -> dict[str, Any]:

    # 1. Validate action structure
    if not isinstance(action, dict):
        return {
            "status": "invalid",
            "reason": "Action must be a dictionary"
        }

    action_type = action.get("action_type")

    if action_type not in ALLOWED_ACTION_TYPES:
        return {
            "status": "rejected",
            "reason": "Action type is not allowed by retention policy"
        }

    if not action.get("description") or not action.get("reason"):
        return {
            "status": "invalid",
            "reason": "Action description or reason is missing"
        }

    # 2. Human approval is mandatory
    if action.get("requires_approval") is not True:
        return {
            "status": "rejected",
            "reason": "All retention actions require human approval"
        }

    # 3. Action-specific business policies

    if action_type == "personalised_reengagement":

        days_inactive = customer_data.get("days_since_last_order")
        risk = customer_data.get("retention_risk_proxy")

        has_inactivity_evidence = (
            days_inactive is not None or risk is not None
        )

        if not has_inactivity_evidence:
            return {
                "status": "requires_review",
                "reason": "Sufficient inactivity evidence is unavailable"
            }

        return {
            "status": "feasible",
            "reason": "Re-engagement is supported by available inactivity evidence"
        }

    if action_type == "customer_support_followup":

        cancelled_orders = customer_data.get("cancelled_orders", 0)

        if not isinstance(cancelled_orders, (int, float)):
            return {
                "status": "requires_review",
                "reason": "Cancellation evidence needs verification"
            }

        if cancelled_orders <= 0:
            return {
                "status": "requires_review",
                "reason": "No cancellation evidence is available to support follow-up"
            }

        return {
            "status": "feasible",
            "reason": "Available cancellation data supports a customer support follow-up"
        }

    if action_type == "loyalty_reward":

        total_orders = customer_data.get("total_orders")
        delivered_orders = customer_data.get("delivered_orders")
        cancelled_orders = customer_data.get("cancelled_orders")
        average_order_value = customer_data.get("average_order_value")

        required_values = [
            total_orders,
            delivered_orders,
            cancelled_orders,
            average_order_value
        ]

        if any(value is None for value in required_values):
            return {
                "status": "requires_review",
                "reason": "Customer purchase history is incomplete"
            }

        numeric_values = [
            total_orders,
            delivered_orders,
            cancelled_orders,
            average_order_value
        ]

        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in numeric_values
        ):
            return {
                "status": "requires_review",
                "reason": "Customer purchase metrics are invalid"
            }

        if (
            total_orders < 10
            or delivered_orders < 8
            or average_order_value < 1000
            or total_orders <= 0
            or cancelled_orders < 0
            or delivered_orders < 0
            or delivered_orders > total_orders
            or cancelled_orders > total_orders
        ):
            return {
                "status": "requires_review",
                "reason": "Customer does not meet the loyalty reward eligibility criteria"
            }

        cancellation_ratio = cancelled_orders / total_orders

        if cancellation_ratio > 0.25:
            return {
                "status": "requires_review",
                "reason": "Cancellation ratio is too high for automatic eligibility"
            }

        return {
            "status": "feasible",
            "reason": (
                "Customer meets loyalty eligibility criteria based on "
                "purchase frequency, delivered orders and average order value. "
                "Admin approval and campaign budget verification are still required."
            )
        }

    if action_type == "product_recommendation":

        return {
            "status": "requires_review",
            "reason": "Explicit product preference or product-level evidence must be verified"
        }

    return {
        "status": "rejected",
        "reason": "No applicable retention policy found"
    }


def evaluate_candidate_actions(
    actions: list[dict[str, Any]],
    customer_data: dict[str, Any]
) -> dict[str, Any]:

    if not isinstance(actions, list):
        return {
            "feasible_actions": [],
            "rejected_actions": [],
            "review_actions": [],
            "errors": ["Actions must be provided as a list"]
        }

    if not isinstance(customer_data, dict):
        return {
            "feasible_actions": [],
            "rejected_actions": [],
            "review_actions": [],
            "errors": ["Customer data must be a dictionary"]
        }

    feasible_actions = []
    rejected_actions = []
    review_actions = []
    errors = []

    for action in actions:

        result = evaluate_candidate_action(
            action,
            customer_data
        )

        evaluated_action = {
            "action": action,
            "policy_status": result["status"],
            "policy_reason": result["reason"]
        }

        if result["status"] == "feasible":
            feasible_actions.append(evaluated_action)

        elif result["status"] == "rejected":
            rejected_actions.append(evaluated_action)

        elif result["status"] == "requires_review":
            review_actions.append(evaluated_action)

        else:
            errors.append(result["reason"])

    return {
        "feasible_actions": feasible_actions,
        "rejected_actions": rejected_actions,
        "review_actions": review_actions,
        "errors": errors
    }
