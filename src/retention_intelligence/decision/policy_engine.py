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

        # Telco indicators
        tenure = customer_data.get("tenure")
        contract = customer_data.get("Contract")
        monthly_charges = customer_data.get("MonthlyCharges")

        has_olist_inactivity = (
            days_inactive is not None or risk is not None
        )

        has_telco_reengagement_evidence = (
            tenure is not None
            or contract is not None
            or monthly_charges is not None
        )

        if not (has_olist_inactivity or has_telco_reengagement_evidence):
            return {
                "status": "requires_review",
                "reason": "Sufficient inactivity or tenure evidence is unavailable"
            }

        return {
            "status": "feasible",
            "reason": (
                "Re-engagement is supported by available customer inactivity "
                "or tenure/contract evidence"
            )
        }

    if action_type == "customer_support_followup":

        cancelled_orders = customer_data.get("cancelled_orders")

        # Telco service indicators
        tech_support = customer_data.get("TechSupport")
        online_security = customer_data.get("OnlineSecurity")
        senior_citizen = customer_data.get("SeniorCitizen")

        has_telco_support_evidence = (
            tech_support in ("No", "No internet service")
            or online_security == "No"
            or senior_citizen == 1
        )

        if cancelled_orders is not None:
            if not isinstance(cancelled_orders, (int, float)):
                return {
                    "status": "requires_review",
                    "reason": "Cancellation evidence needs verification"
                }

            if cancelled_orders > 0:
                return {
                    "status": "feasible",
                    "reason": "Available cancellation data supports a customer support follow-up"
                }

        if has_telco_support_evidence:
            return {
                "status": "feasible",
                "reason": "Service profile indicates opportunity for proactive customer support follow-up"
            }

        return {
            "status": "requires_review",
            "reason": "No cancellation or service support evidence is available to support follow-up"
        }

    if action_type == "loyalty_reward":

        total_orders = customer_data.get("total_orders")
        delivered_orders = customer_data.get("delivered_orders")
        cancelled_orders = customer_data.get("cancelled_orders")
        average_order_value = customer_data.get("average_order_value")

        # 1. Olist loyalty path
        if (
            total_orders is not None
            and delivered_orders is not None
            and cancelled_orders is not None
            and average_order_value is not None
        ):
            numeric_values = [
                total_orders,
                delivered_orders,
                cancelled_orders,
                average_order_value
            ]

            if not any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                for value in numeric_values
            ):
                if (
                    total_orders >= 10
                    and delivered_orders >= 8
                    and average_order_value >= 1000
                    and total_orders > 0
                    and 0 <= cancelled_orders <= total_orders
                    and 0 <= delivered_orders <= total_orders
                ):
                    cancellation_ratio = cancelled_orders / total_orders
                    if cancellation_ratio <= 0.25:
                        return {
                            "status": "feasible",
                            "reason": (
                                "Customer meets loyalty eligibility criteria based on "
                                "purchase frequency, delivered orders and average order value. "
                                "Admin approval and campaign budget verification are still required."
                            )
                        }

        # 2. Telco loyalty path
        tenure = customer_data.get("tenure")
        total_charges = customer_data.get("TotalCharges")

        if tenure is not None and isinstance(tenure, (int, float)):
            if tenure >= 12 or (isinstance(total_charges, (int, float)) and total_charges >= 1000):
                return {
                    "status": "feasible",
                    "reason": (
                        "Customer qualifies for loyalty reward consideration based on "
                        "tenure and customer relationship history."
                    )
                }

        return {
            "status": "requires_review",
            "reason": "Customer does not meet the loyalty reward eligibility criteria"
        }

    if action_type == "product_recommendation":

        # Telco add-on upsell / plan bundling eligibility
        internet_service = customer_data.get("InternetService")
        tech_support = customer_data.get("TechSupport")
        online_security = customer_data.get("OnlineSecurity")
        device_protection = customer_data.get("DeviceProtection")

        if internet_service in ("DSL", "Fiber optic"):
            if (
                tech_support == "No"
                or online_security == "No"
                or device_protection == "No"
            ):
                return {
                    "status": "feasible",
                    "reason": "Recommendation is supported by missing security/support add-on services"
                }

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
