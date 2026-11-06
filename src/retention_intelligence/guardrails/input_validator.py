from pydantic import BaseModel, Field, ValidationError
from typing import Literal


ALLOWED_ACTION_TYPES = {
    "personalised_reengagement",
    "customer_support_followup",
    "loyalty_reward",
    "product_recommendation"
}


class CustomerInput(BaseModel):

    customer_id: str = Field(min_length=1)
    source: Literal["olist", "telco"]


class CandidateAction(BaseModel):

    action_type: Literal[
        "personalised_reengagement",
        "customer_support_followup",
        "loyalty_reward",
        "product_recommendation"
    ]

    description: str = Field(min_length=1)
    reason: str = Field(min_length=1)

    priority: Literal["high", "medium", "low"]

    requires_approval: bool = True
    status: Literal["candidate"] = "candidate"


def validate_customer_input(data: dict):

    try:

        validated_data = CustomerInput(**data)

        return {
            "is_valid": True,
            "data": validated_data.model_dump(),
            "errors": []
        }

    except ValidationError as error:

        return {
            "is_valid": False,
            "data": {},
            "errors": error.errors()
        }


def validate_candidate_actions(actions: list):

    if not isinstance(actions, list):

        return {
            "is_valid": False,
            "data": [],
            "errors": ["Candidate actions must be a list"]
        }

    validated_actions = []
    errors = []

    for index, action in enumerate(actions):

        try:

            validated_action = CandidateAction(**action)

            validated_actions.append(
                validated_action.model_dump()
            )

        except (ValidationError, TypeError) as error:

            errors.append({
                "index": index,
                "error": str(error)
            })

    return {
        "is_valid": len(errors) == 0,
        "data": validated_actions,
        "errors": errors
    }