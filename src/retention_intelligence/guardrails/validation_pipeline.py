
from retention_intelligence.guardrails.prompt_injection import (
    detect_prompt_injection
)

from retention_intelligence.guardrails.input_validator import (
    validate_customer_input,
    validate_candidate_actions
)

from retention_intelligence.guardrails.output_validator import (
    validate_agent_output
)


def validate_incoming_request(customer_data: dict):

    injection_result = detect_prompt_injection(
        str(customer_data)
    )

    if injection_result["is_suspicious"]:
        return {
            "is_valid": False,
            "status": "requires_review",
            "stage": "prompt_injection",
            "errors": [injection_result["reason"]]
        }

    input_result = validate_customer_input(
        customer_data
    )

    if not input_result["is_valid"]:
        return {
            "is_valid": False,
            "status": "rejected",
            "stage": "input_validation",
            "errors": input_result["errors"]
        }

    return {
        "is_valid": True,
        "status": "safe",
        "stage": "completed",
        "data": input_result["data"],
        "errors": []
    }


def validate_retention_actions(actions: list):

    action_result = validate_candidate_actions(
        actions
    )

    if not action_result["is_valid"]:
        return {
            "is_valid": False,
            "status": "rejected",
            "stage": "action_validation",
            "errors": action_result["errors"]
        }

    return {
        "is_valid": True,
        "status": "safe",
        "stage": "completed",
        "data": action_result["data"],
        "errors": []
    }


def validate_retention_output(output: dict):

    output_result = validate_agent_output(
        output
    )

    if not output_result["is_valid"]:
        return {
            "is_valid": False,
            "status": "rejected",
            "stage": "output_validation",
            "errors": output_result["errors"]
        }

    return {
        "is_valid": True,
        "status": "safe",
        "stage": "completed",
        "data": output_result["data"],
        "errors": []
    }
