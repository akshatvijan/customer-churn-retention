
from typing import Any

from sqlalchemy.orm import Session

from retention_intelligence.db.model import RetentionAuditLog


def create_audit_record(
    db: Session,
    customer_id: str,
    source: str
) -> RetentionAuditLog:
    """
    Create an initial audit record when an investigation starts.
    """

    audit_record = RetentionAuditLog(
        customer_id=customer_id,
        source=source,
        investigation_status="started"
    )

    db.add(audit_record)
    db.commit()

    return audit_record


def update_audit_record(
    db: Session,
    audit_id: int,
    updates: dict[str, Any]
) -> RetentionAuditLog | None:
    """
    Update an existing audit record with workflow results.
    """

    audit_record = db.query(RetentionAuditLog).filter(
        RetentionAuditLog.id == audit_id
    ).first()

    if audit_record is None:
        return None

    allowed_fields = {
        "investigation_status",
        "churn_prediction",
        "retention_strategy",
        "policy_result",
        "human_approval",
        "execution_result",
        "errors"
    }

    for field, value in updates.items():
        if field in allowed_fields:
            setattr(audit_record, field, value)

    db.commit()
    db.refresh(audit_record)

    return audit_record


def get_audit_record(
    db: Session,
    audit_id: int
) -> RetentionAuditLog | None:
    """
    Retrieve an audit record using its ID.
    """

    return db.query(RetentionAuditLog).filter(
        RetentionAuditLog.id == audit_id
    ).first()


def get_customer_audit_history(
    db: Session,
    customer_id: str,
    source: str
) -> list[RetentionAuditLog]:
    """
    Retrieve investigation history for a customer.
    """

    return (
        db.query(RetentionAuditLog)
        .filter(
            RetentionAuditLog.customer_id == customer_id,
            RetentionAuditLog.source == source
        )
        .order_by(RetentionAuditLog.created_at.desc())
        .all()
    )
