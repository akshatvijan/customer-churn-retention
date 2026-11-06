
from pydantic import BaseModel, Field, ValidationError
from typing import Literal


class ValidatedAction(BaseModel):

    action_type: Literal[
        "personalised_reengagement",
        "customer_support_followup",
        "loyalty_reward",
        "product_recommendation"
    ]

    description: str = Field(min_length=1)
    reason: str = Field(min_length=1)

    priority: Literal["high", "medium", "low"]

    requires_approval: Literal[True]

    status: Literal["candidate"]


class AgentOutput(BaseModel):

    candidate_actions: list[ValidatedAction]

    strategy_summary: str = ""

    evidence_limitations: list[str] = []


def validate_agent_output(output: dict):

    try:

        validated_output = AgentOutput(**output)

        return {
            "is_valid": True,
            "data": validated_output.model_dump(),
            "errors": []
        }

    except ValidationError as error:

        return {
            "is_valid": False,
            "data": {},
            "errors": error.errors()
        }
