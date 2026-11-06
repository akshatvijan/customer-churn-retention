
from langgraph.types import interrupt


def human_approval_agent(state: dict):

    feasible_actions = state.get("feasible_actions", [])

    print("\n========== HUMAN APPROVAL DEBUG ==========")
    print("Feasible action count:", len(feasible_actions))

    if not feasible_actions:

        return {
            "human_approval": {
                "status": "not_required",
                "approved_actions": [],
                "rejected_actions": [],
                "message": "No eligible actions available for approval"
            },
            "errors": []
        }

    pending_actions = []

    for index, item in enumerate(feasible_actions):

        if not isinstance(item, dict):
            continue

        action = item.get("action")

        if not isinstance(action, dict):
            continue

        pending_actions.append({
            "action_index": index,
            "action": action,
            "policy_reason": item.get("policy_reason", "")
        })

    if not pending_actions:

        return {
            "human_approval": {
                "status": "not_required",
                "approved_actions": [],
                "rejected_actions": [],
                "message": "No valid actions available for approval"
            },
            "errors": []
        }

    print("Pending actions:", pending_actions)

    # ---------------------------------
    # Human Approval Interrupt
    # ---------------------------------

    human_response = interrupt({
        "message": (
            "Please review and approve or reject "
            "the proposed retention actions"
        ),
        "pending_actions": pending_actions
    })

    if not isinstance(human_response, dict):

        raise ValueError(
            "Invalid human approval response"
        )

    decisions = human_response.get("decisions", [])

    if not isinstance(decisions, list):

        raise ValueError(
            "Approval decisions must be a list"
        )

    valid_indices = {
        item["action_index"] for item in pending_actions
    }

    approved_actions = []
    rejected_actions = []
    processed_indices = set()

    # ---------------------------------
    # Process Admin Decisions
    # ---------------------------------

    for decision in decisions:

        if not isinstance(decision, dict):
            continue

        index = decision.get("action_index")
        status = decision.get("decision")

        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or index not in valid_indices
        ):
            continue

        if index in processed_indices:
            continue

        if status not in ("approved", "rejected"):
            continue

        action_item = next(
            item for item in pending_actions
            if item["action_index"] == index
        )

        evaluated_action = {
            "action": action_item["action"],
            "policy_reason": action_item["policy_reason"],
            "approved_by": decision.get("approved_by") or "admin"
        }

        if status == "approved":
            approved_actions.append(evaluated_action)

        else:
            rejected_actions.append(evaluated_action)

        processed_indices.add(index)

    # ---------------------------------
    # Do not silently skip undecided actions
    # ---------------------------------

    undecided_indices = valid_indices - processed_indices

    if undecided_indices:

        raise ValueError(
            "Admin response is incomplete. "
            f"Missing decisions for action indices: "
            f"{sorted(undecided_indices)}"
        )

    print("Approved actions:", approved_actions)
    print("Rejected actions:", rejected_actions)
    print("==========================================\n")

    # ---------------------------------
    # Return Approval Result
    # ---------------------------------

    return {
        "human_approval": {
            "status": "completed",
            "approved_actions": approved_actions,
            "rejected_actions": rejected_actions,
            "message": "All retention actions have received an admin decision"
        },
        "errors": []
    }
