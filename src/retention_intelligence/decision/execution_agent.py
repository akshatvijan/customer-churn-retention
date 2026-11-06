
def execution_agent(state: dict):

    human_approval = state.get("human_approval", {})

    if human_approval.get("status") != "completed":
        return {
            "execution_result": {
                "status": "not_executed",
                "executed_actions": [],
                "message": "Human approval is not completed"
            },
            "errors": ["Execution requires completed human approval"]
        }

    approved_actions = human_approval.get(
        "approved_actions", []
    )

    executed_actions = []

    for item in approved_actions:

        if not isinstance(item, dict):
            continue

        action = item.get("action", {})

        if not isinstance(action, dict):
            continue

        executed_actions.append({
            "action_type": action.get("action_type"),
            "description": action.get("description"),
            "status": "ready_for_execution",
            "approved_by": item.get("approved_by")
        })

    return {
        "execution_result": {
            "status": (
                "ready_for_execution"
                if executed_actions
                else "nothing_to_execute"
            ),
            "executed_actions": executed_actions,
            "message": (
                "Approved actions passed execution checks"
                if executed_actions
                else "No approved actions available"
            )
        },
        "errors": []
    }
