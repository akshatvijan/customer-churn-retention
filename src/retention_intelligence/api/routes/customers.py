
import logging
from uuid import uuid4
from typing import Literal

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from retention_intelligence.db.connection import get_db
from retention_intelligence.db.model import (
    TelcoChurnPrediction,
    OlistRetentionRisk,
    RetentionAuditLog
)

from retention_intelligence.schemas.prediction import (
    ChurnPredictionRequest,
    ChurnPredictionResponse
)

from retention_intelligence.services.telco_prediction_service import (
    predict_telco_churn
)

from retention_intelligence.graph.workflow import build_retention_workflow


# ---------------- INITIAL CONFIGURATION ----------------

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers"]
)


# ---------------- WORKFLOW ----------------

retention_workflow = build_retention_workflow()


# ---------------- LANGFUSE CONFIGURATION ----------------

def get_workflow_config(thread_id: str, operation: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        },
        "run_name": operation,
        "metadata": {
            "langfuse_session_id": thread_id,
            "langfuse_tags": [
                "customer-retention",
                operation
            ]
        }
    }

    try:
        config["callbacks"] = [CallbackHandler()]

    except Exception:
        logger.exception("Langfuse callback initialization failed")

    return config


# ---------------- REQUEST SCHEMAS ----------------

class InvestigationRequest(BaseModel):
    customer_id: str
    source: Literal["olist", "telco"]


class AISearchRequest(BaseModel):
    question: str


class ApprovalDecision(BaseModel):
    action_index: int
    decision: Literal["approved", "rejected"]
    approved_by: str


class ApprovalRequest(BaseModel):
    thread_id: str
    decisions: list[ApprovalDecision]


# ---------------- 1. GET TELCO CUSTOMERS ----------------

@router.get("/telco")
def get_telco_customers(db: Session = Depends(get_db)):

    try:
        query = text("""
            SELECT
                "customerID" AS customer_id,
                gender,
                "SeniorCitizen",
                "Partner",
                "Dependents",
                tenure,
                "PhoneService",
                "MultipleLines",
                "InternetService",
                "OnlineSecurity",
                "OnlineBackup",
                "DeviceProtection",
                "TechSupport",
                "StreamingTV",
                "StreamingMovies",
                "Contract",
                "PaperlessBilling",
                "PaymentMethod",
                "MonthlyCharges",
                "TotalCharges"
            FROM telco_customer_churn
            ORDER BY "customerID"
            LIMIT 100
        """)

        customers = db.execute(query).mappings().all()

        return {
            "source": "telco",
            "total_records": len(customers),
            "data": [dict(customer) for customer in customers]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch Telco customers: {str(error)}"
        )


# ---------------- 2. GET OLIST CUSTOMERS ----------------

@router.get("/olist")
def get_olist_customers(db: Session = Depends(get_db)):

    try:
        customers = (
            db.query(OlistRetentionRisk)
            .limit(100)
            .all()
        )

        return {
            "source": "olist",
            "total_records": len(customers),
            "data": customers
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch Olist customers: {str(error)}"
        )


# ---------------- 3. GET OLIST CUSTOMER PROFILE ----------------

@router.get("/olist/profile/{customer_id}")
def get_olist_customer_profile(
    customer_id: str,
    db: Session = Depends(get_db)
):

    try:
        query = text("""
            SELECT
                customer_unique_id AS customer_id,
                total_orders,
                delivered_orders,
                cancelled_orders,
                last_order_date,
                average_order_value,
                days_since_last_order,
                retention_risk_proxy
            FROM olist_customer_features
            WHERE customer_unique_id = :customer_id
            LIMIT 1
        """)

        result = db.execute(
            query,
            {"customer_id": customer_id}
        ).mappings().first()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Olist customer not found"
            )

        return {
            "success": True,
            "source": "olist",
            "customer_data": dict(result)
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch Olist profile: {str(error)}"
        )


# ---------------- 4. GET TELCO CUSTOMER PROFILE ----------------

@router.get("/telco/profile/{customer_id}")
def get_telco_customer_profile(
    customer_id: str,
    db: Session = Depends(get_db)
):

    try:
        query = text("""
            SELECT *
            FROM telco_customer_churn
            WHERE "customerID" = :customer_id
            LIMIT 1
        """)

        result = db.execute(
            query,
            {"customer_id": customer_id}
        ).mappings().first()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Telco customer not found"
            )

        customer_data = dict(result)

        customer_data["customer_id"] = customer_data.get("customerID")

        customer_data.pop("Churn", None)
        customer_data.pop("churn", None)

        return {
            "success": True,
            "source": "telco",
            "customer_data": customer_data
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch Telco profile: {str(error)}"
        )


# ---------------- 5. GET APPROVED RETENTION ACTIONS ----------------

@router.get("/{customer_id}/retention-actions")
def get_customer_retention_actions(
    customer_id: str,
    source: Literal["olist", "telco"] = "olist",
    db: Session = Depends(get_db)
):

    audit_records = (
        db.query(RetentionAuditLog)
        .filter(
            RetentionAuditLog.customer_id == customer_id,
            RetentionAuditLog.source == source,
            RetentionAuditLog.investigation_status == "completed"
        )
        .order_by(RetentionAuditLog.created_at.desc())
        .all()
    )

    approved_actions = []

    allowed_action_types = {
        "personalised_reengagement",
        "customer_support_followup",
        "loyalty_reward",
        "product_recommendation"
    }

    for audit in audit_records:

        human_approval = audit.human_approval or {}

        if human_approval.get("status") != "completed":
            continue

        actions = human_approval.get("approved_actions", [])

        for item in actions:

            action = item.get("action", {})
            action_type = action.get("action_type")

            if action_type not in allowed_action_types:
                continue

            approved_actions.append({
                "audit_id": audit.id,
                "action_type": action_type,
                "description": action.get("description", ""),
                "approved_at": audit.updated_at
            })

    return {
        "customer_id": customer_id,
        "source": source,
        "total_approved_actions": len(approved_actions),
        "data": approved_actions
    }


# ---------------- 6. PREDICT TELCO CHURN ----------------

@router.post(
    "/telco/predict",
    response_model=ChurnPredictionResponse
)
def predict_customer_churn(
    request: ChurnPredictionRequest,
    db: Session = Depends(get_db)
):

    try:
        customer_data = request.model_dump()

        prediction_result = predict_telco_churn(customer_data)

        db_record = TelcoChurnPrediction(
            customer_id=prediction_result["customer_id"],
            churn_prediction=prediction_result["churn_prediction"],
            churn_probability=prediction_result["churn_probability"],
            risk_level=prediction_result["risk_level"]
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return prediction_result

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        )


# ---------------- 7. RUN CUSTOMER INVESTIGATION ----------------

@router.post("/investigate")
async def investigate_customer(request: InvestigationRequest):

    thread_id = str(uuid4())

    initial_state = {
        "customer_id": request.customer_id,
        "source": request.source,
        "errors": []
    }

    config = get_workflow_config(
        thread_id,
        "customer-investigation"
    )

    try:
        result = await retention_workflow.ainvoke(
            initial_state,
            config=config
        )

        interrupts = result.get("__interrupt__", [])

        if interrupts:
            return {
                "status": "awaiting_approval",
                "thread_id": thread_id,
                "customer_id": request.customer_id,
                "source": request.source,
                "approval_request": [
                    interrupt.value for interrupt in interrupts
                ],
                "audit_record": result.get("audit_record", {}),
                "message": "Human approval is required before execution"
            }

        return {
            "status": "completed",
            "thread_id": thread_id,
            "customer_id": request.customer_id,
            "source": request.source,
            "churn_prediction": result.get("churn_prediction", {}),
            "fulfilment_analysis": result.get("fulfilment_analysis", {}),
            "retention_strategy": result.get("retention_strategy", {}),
            "policy_result": result.get("policy_result", {}),
            "human_approval": result.get("human_approval", {}),
            "execution_result": result.get("execution_result", {}),
            "audit_record": result.get("audit_record", {}),
            "errors": result.get("errors", [])
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Customer investigation failed: {str(error)}"
        )


# ---------------- 8. APPROVE OR REJECT ACTIONS ----------------

@router.post("/approve")
async def approve_customer_actions(request: ApprovalRequest):

    config = get_workflow_config(
        request.thread_id,
        "human-approval-resume"
    )

    try:
        snapshot = await retention_workflow.aget_state(config)

        if not snapshot or not snapshot.next:
            raise HTTPException(
                status_code=404,
                detail="Workflow not found or already completed"
            )

        if "human_approval" not in snapshot.next:
            raise HTTPException(
                status_code=409,
                detail="Workflow is not waiting for human approval"
            )

        human_response = {
            "decisions": [
                decision.model_dump()
                for decision in request.decisions
            ]
        }

        result = await retention_workflow.ainvoke(
            Command(resume=human_response),
            config=config
        )

        interrupts = result.get("__interrupt__", [])

        if interrupts:
            return {
                "status": "awaiting_approval",
                "thread_id": request.thread_id,
                "approval_request": [
                    interrupt.value for interrupt in interrupts
                ],
                "message": "Workflow is still waiting for approval"
            }

        return {
            "status": "completed",
            "thread_id": request.thread_id,
            "human_approval": result.get("human_approval", {}),
            "execution_result": result.get("execution_result", {}),
            "audit_record": result.get("audit_record", {}),
            "errors": result.get("errors", []),
            "message": "Approval processed and workflow resumed successfully"
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Approval processing failed: {str(error)}"
        )


# ---------------- 9. AI SEARCH ----------------

@router.post("/ai-search")
async def ai_search(request: AISearchRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Search question cannot be empty"
        )

    thread_id = str(uuid4())

    initial_state = {
        "request_type": "ai_search",
        "question": question,
        "errors": []
    }

    config = get_workflow_config(
        thread_id,
        "ai-search"
    )

    try:
        result = await retention_workflow.ainvoke(
            initial_state,
            config=config
        )

        search_result = result.get("ai_search_result", {})

        if not search_result:
            raise HTTPException(
                status_code=500,
                detail="AI Search did not return a result"
            )

        return {
            "status": search_result.get("status", "unknown"),
            "thread_id": thread_id,
            "question": question,
            "answer": search_result.get("answer", ""),
            "sources": search_result.get("sources", []),
            "errors": result.get("errors", [])
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"AI Search failed: {str(error)}"
        )
