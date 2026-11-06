from typing import Literal

from mcp.server.fastmcp import FastMCP
from sqlalchemy import text

from retention_intelligence.db.connection import SessionLocal


mcp = FastMCP("postgres-customer-server")


@mcp.tool()
def get_customer_profile(
    source: Literal["olist", "telco"],
    customer_id: str
) -> dict:
    """
    Retrieve a customer profile from PostgreSQL.

    Olist uses olist_customer_features.
    Telco uses telco_customer_churn.
    """

    if not customer_id or not customer_id.strip():
        raise ValueError("Customer ID cannot be empty")

    customer_id = customer_id.strip()

    if source == "olist":

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

    elif source == "telco":

        query = text("""
            SELECT *
            FROM telco_customer_churn
            WHERE "customerID" = :customer_id
            LIMIT 1
        """)

    else:
        raise ValueError("Source must be 'olist' or 'telco'")

    db = SessionLocal()

    try:
        result = db.execute(
            query,
            {"customer_id": customer_id}
        ).mappings().first()

        if not result:
            return {
                "status": "not_found",
                "customer_id": customer_id,
                "source": source,
                "message": "Customer not found"
            }

        customer_data = dict(result)

        if source == "telco":

            customer_data["customer_id"] = customer_data.get(
                "customerID"
            )

            customer_data.pop("customerID", None)
            customer_data.pop("Churn", None)
            customer_data.pop("churn", None)

        return {
            "status": "success",
            "source": source,
            "customer_data": customer_data
        }

    except Exception as error:
        db.rollback()
        raise RuntimeError(
            f"Customer profile retrieval failed: {str(error)}"
        ) from error

    finally:
        db.close()


@mcp.tool()
def get_customer_count(
    source: Literal["olist", "telco"]
) -> dict:
    """
    Get the total number of customers in the selected dataset.
    """

    if source == "olist":
        query = text("""
            SELECT COUNT(*)
            FROM olist_customer_features
        """)

    elif source == "telco":
        query = text("""
            SELECT COUNT(*)
            FROM telco_customer_churn
        """)

    else:
        raise ValueError("Source must be 'olist' or 'telco'")

    db = SessionLocal()

    try:
        total = db.execute(query).scalar_one()

        return {
            "status": "success",
            "source": source,
            "total_customers": int(total)
        }

    except Exception as error:
        db.rollback()
        raise RuntimeError(
            f"Customer count retrieval failed: {str(error)}"
        ) from error

    finally:
        db.close()


@mcp.tool()
def find_inactive_olist_customers(
    days: int = 90,
    limit: int = 10
) -> dict:
    """
    Find Olist customers who have been inactive
    for at least the specified number of days.
    """

    if days < 0:
        raise ValueError("Days cannot be negative")

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")

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
        WHERE days_since_last_order >= :days
        ORDER BY days_since_last_order DESC
        LIMIT :limit
    """)

    db = SessionLocal()

    try:
        results = db.execute(
            query,
            {
                "days": days,
                "limit": limit
            }
        ).mappings().all()

        customers = [dict(row) for row in results]

        return {
            "status": "success",
            "source": "olist",
            "inactive_days_threshold": days,
            "total_found": len(customers),
            "customers": customers
        }

    except Exception as error:
        db.rollback()
        raise RuntimeError(
            f"Inactive customer search failed: {str(error)}"
        ) from error

    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")