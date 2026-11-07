
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from retention_intelligence.agents.state import RetentionState
from retention_intelligence.agents.customer_profile_agent import customer_profile_agent
from retention_intelligence.agents.churn_prediction_agent import churn_prediction_agent
from retention_intelligence.agents.fulfilment_agent import fulfilment_agent
from retention_intelligence.agents.retention_strategy_agent import retention_strategy_agent
from retention_intelligence.agents.ai_search_agent import ai_search_agent

from retention_intelligence.decision.decision_agent import decision_engine_agent
from retention_intelligence.decision.human_approval_agent import human_approval_agent
from retention_intelligence.decision.execution_agent import execution_agent

from retention_intelligence.db.connection import SessionLocal
from retention_intelligence.services.audit_service import (
    create_audit_record,
    update_audit_record
)


def audit_start_node(state: RetentionState):
    """Create an audit record when investigation starts."""

    customer_id = state.get("customer_id")
    source = state.get("source")

    if not customer_id or not source:
        return {
            "errors": [
                "Audit record not created: customer_id or source is missing"
            ]
        }

    db = SessionLocal()

    try:
        audit = create_audit_record(
            db=db,
            customer_id=customer_id,
            source=source
        )

        return {
            "audit_record": {
                "id": audit.id,
                "status": audit.investigation_status
            }
        }

    except Exception as exc:
        db.rollback()
        return {
            "errors": [f"Audit creation failed: {str(exc)}"]
        }

    finally:
        db.close()


def audit_persistence_node(state: RetentionState):
    """Save final workflow results in PostgreSQL."""

    audit_record = state.get("audit_record", {})
    audit_id = audit_record.get("id")

    if not audit_id:
        return {
            "errors": ["Audit update skipped: audit ID is missing"]
        }

    execution_result = state.get("execution_result", {})
    human_approval = state.get("human_approval", {})

    if execution_result.get("status") == "ready_for_execution":
        investigation_status = "completed"
    elif human_approval.get("status") == "pending":
        investigation_status = "awaiting_approval"
    else:
        investigation_status = "completed"

    updates = {
        "investigation_status": investigation_status,
        "churn_prediction": state.get("churn_prediction", {}),
        "retention_strategy": state.get("retention_strategy", {}),
        "policy_result": state.get("policy_result", {}),
        "human_approval": human_approval,
        "execution_result": execution_result,
        "errors": state.get("errors", [])
    }

    db = SessionLocal()

    try:
        updated_record = update_audit_record(
            db=db,
            audit_id=audit_id,
            updates=updates
        )

        if updated_record is None:
            return {
                "errors": ["Audit record not found during update"]
            }

        return {
            "audit_record": {
                "id": updated_record.id,
                "status": updated_record.investigation_status
            }
        }

    except Exception as exc:
        db.rollback()
        return {
            "errors": [f"Audit update failed: {str(exc)}"]
        }

    finally:
        db.close()


def route_from_start(state: RetentionState):
    """Route AI Search requests separately from customer investigations."""

    if state.get("request_type") == "ai_search":
        return "ai_search"

    return "audit_start"


def route_after_churn(state: RetentionState):

    source = state.get("source")

    if source == "olist":
        return "fulfilment"

    return "retention_strategy"


def build_retention_workflow():

    workflow = StateGraph(RetentionState)

    workflow.add_node("audit_start", audit_start_node)
    workflow.add_node("customer_profile", customer_profile_agent)
    workflow.add_node("churn_prediction", churn_prediction_agent)
    workflow.add_node("fulfilment", fulfilment_agent)
    workflow.add_node("retention_strategy", retention_strategy_agent)

    workflow.add_node("ai_search", ai_search_agent)

    workflow.add_node("decision_engine", decision_engine_agent)
    workflow.add_node("human_approval", human_approval_agent)
    workflow.add_node("execution", execution_agent)

    workflow.add_node("audit_persistence", audit_persistence_node)

    workflow.add_conditional_edges(
        START,
        route_from_start,
        {
            "ai_search": "ai_search",
            "audit_start": "audit_start"
        }
    )

    workflow.add_edge("ai_search", END)

    workflow.add_edge("audit_start", "customer_profile")
    workflow.add_edge("customer_profile", "churn_prediction")

    workflow.add_conditional_edges(
        "churn_prediction",
        route_after_churn,
        {
            "fulfilment": "fulfilment",
            "retention_strategy": "retention_strategy"
        }
    )

    workflow.add_edge("fulfilment", "retention_strategy")
    workflow.add_edge("retention_strategy", "decision_engine")
    workflow.add_edge("decision_engine", "human_approval")
    workflow.add_edge("human_approval", "execution")
    workflow.add_edge("execution", "audit_persistence")
    workflow.add_edge("audit_persistence", END)

    checkpointer = InMemorySaver()

    app = workflow.compile(checkpointer=checkpointer)

    original_ainvoke = app.ainvoke
    original_invoke = app.invoke

    def _ensure_config(input, config):
        if config is None:
            thread_id = input.get("customer_id", "default") if isinstance(input, dict) else "default"
            return {"configurable": {"thread_id": str(thread_id)}}
        if isinstance(config, dict):
            if "configurable" not in config:
                config["configurable"] = {"thread_id": "default"}
            elif "thread_id" not in config["configurable"]:
                config["configurable"]["thread_id"] = "default"
        return config

    async def wrapped_ainvoke(input, config=None, **kwargs):
        config = _ensure_config(input, config)
        return await original_ainvoke(input, config=config, **kwargs)

    def wrapped_invoke(input, config=None, **kwargs):
        config = _ensure_config(input, config)
        return original_invoke(input, config=config, **kwargs)

    app.ainvoke = wrapped_ainvoke
    app.invoke = wrapped_invoke

    return app
