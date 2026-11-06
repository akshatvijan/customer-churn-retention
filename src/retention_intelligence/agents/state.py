
from typing import TypedDict, Literal, Any


class RetentionState(TypedDict, total=False):

    # User request
    customer_id: str
    source: Literal["olist", "telco"]
    request_type: Literal["investigation", "ai_search"]
    question: str

    # AI Search Agent
    ai_search_result: dict[str, Any]

    # Customer Profile Agent
    customer_data: dict[str, Any]

    # Churn Prediction Agent
    churn_prediction: dict[str, Any]
    shap_explanation: dict[str, Any]

    # Fulfilment Investigation Agent
    fulfilment_evidence: dict[str, Any]
    fulfilment_analysis: dict[str, Any]

    # Shared Customer Context
    shared_customer_context: dict[str, Any]

    # Retention Strategy Agent
    retrieved_knowledge: list[dict[str, Any]]
    candidate_actions: list[dict[str, Any]]
    retention_strategy: dict[str, Any]

    # Deterministic Policy Engine
    policy_result: dict[str, Any]
    feasible_actions: list[dict[str, Any]]

    # Decision Agent
    decision_result: dict[str, Any]

    # Human Approval and Execution
    human_approval: dict[str, Any]
    execution_result: dict[str, Any]

    # Audit and Final Response
    audit_record: dict[str, Any]
    final_response: dict[str, Any]

    rejected_actions: list[dict[str, Any]]
    review_actions: list[dict[str, Any]]

    # Error handling
    errors: list[str]
