
from retention_intelligence.decision.policy_engine import (
    evaluate_candidate_actions
)


def decision_engine_agent(state: dict):

    candidate_actions = state.get("candidate_actions", [])
    customer_data = state.get("customer_data", {})

    print("\n========== DECISION ENGINE DEBUG ==========")

    print("Customer ID:", state.get("customer_id"))
    print("Source:", state.get("source"))

    print("\nCUSTOMER DATA:")
    print(customer_data)

    print("\nCHURN PREDICTION:")
    print(state.get("churn_prediction", {}))

    print("\nCANDIDATE ACTIONS:")
    print(candidate_actions)

    print("\nCANDIDATE ACTION COUNT:", len(candidate_actions))

    if not candidate_actions:

        print("RESULT: No candidate actions received")

        return {
            "policy_result": {
                "feasible_actions": [],
                "rejected_actions": [],
                "review_actions": []
            },
            "feasible_actions": [],
            "rejected_actions": [],
            "review_actions": [],
            "errors": [
                "No candidate actions available for policy evaluation"
            ]
        }

    result = evaluate_candidate_actions(
        candidate_actions,
        customer_data
    )

    print("\nPOLICY RESULT:")
    print(result)

    print("\nFEASIBLE ACTIONS:", result["feasible_actions"])
    print("REJECTED ACTIONS:", result["rejected_actions"])
    print("REVIEW ACTIONS:", result["review_actions"])

    print("===========================================\n")

    return {
        "policy_result": result,
        "feasible_actions": result["feasible_actions"],
        "rejected_actions": result["rejected_actions"],
        "review_actions": result["review_actions"],
        "errors": result["errors"]
    }
