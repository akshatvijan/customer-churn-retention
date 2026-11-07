
import os
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from retention_intelligence.agents.state import RetentionState
from retention_intelligence.rag.retrieval import retrieve_knowledge

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    timeout=45,
    max_retries=1,
    api_key=os.getenv("GROQ_API_KEY") or "gsk_placeholder_for_startup"
)

RETRIEVAL_TIMEOUT = 30
LLM_TIMEOUT = 50


async def fulfilment_agent(state: RetentionState):

    source = state.get("source")
    customer_data = state.get("customer_data", {})

    if source != "olist":
        return {
            "fulfilment_evidence": {},
            "fulfilment_analysis": {},
            "errors": ["Fulfilment investigation is supported for Olist only"]
        }

    if not customer_data:
        return {
            "fulfilment_evidence": {},
            "fulfilment_analysis": {},
            "errors": ["Customer data is missing"]
        }

    customer_id = (
        customer_data.get("customer_id")
        or customer_data.get("customer_unique_id")
        or state.get("customer_id")
    )

    if not customer_id:
        return {
            "fulfilment_evidence": {},
            "fulfilment_analysis": {},
            "errors": ["Olist customer ID is missing"]
        }

    try:
        evidence = {
            "customer_unique_id": customer_id,
            "total_orders": customer_data.get("total_orders"),
            "delivered_orders": customer_data.get("delivered_orders"),
            "cancelled_orders": customer_data.get("cancelled_orders"),
            "last_order_date": customer_data.get("last_order_date"),
            "average_order_value": customer_data.get("average_order_value"),
            "days_since_last_order": customer_data.get("days_since_last_order"),
            "retention_risk_proxy": customer_data.get("retention_risk_proxy")
        }

        query = (
            "Investigate customer fulfilment and inactivity indicators. "
            f"Total orders: {evidence['total_orders']}. "
            f"Delivered orders: {evidence['delivered_orders']}. "
            f"Cancelled orders: {evidence['cancelled_orders']}. "
            f"Days since last order: {evidence['days_since_last_order']}. "
            f"Retention risk proxy: {evidence['retention_risk_proxy']}."
        )

        print(
            f"[FULFILMENT] Starting knowledge retrieval for {customer_id}",
            flush=True
        )

        retrieved_knowledge = await asyncio.wait_for(
            asyncio.to_thread(
                retrieve_knowledge,
                query=query,
                top_k=3
            ),
            timeout=RETRIEVAL_TIMEOUT
        )

        print(
            f"[FULFILMENT] Retrieved {len(retrieved_knowledge)} documents",
            flush=True
        )

        if not retrieved_knowledge:
            retrieved_knowledge = [
                {
                    "text": (
                        "Fulfilment indicators should be evaluated against historical "
                        "order delivery, cancellations, and order completion timelines."
                    ),
                    "category": "fulfilment",
                    "source": "fulfilment_guidelines",
                    "similarity_score": 0.8
                }
            ]

        system_prompt = """
You are a Fulfilment Investigation Agent.

Investigate customer fulfilment indicators using only supplied
customer evidence and retrieved knowledge.

STRICT RULES:

1. Use only supplied customer evidence.
2. Never invent delivery delays, review sentiments or complaints.
3. Never claim a fulfilment issue caused churn without evidence.
4. Inactivity-based retention risk is not confirmed churn.
5. Distinguish observed facts from interpretations.
6. Explicitly mention evidence limitations.
7. Return a concise structured investigation.

Return these sections:
- observed_indicators
- investigation_findings
- evidence_limitations
- overall_assessment
"""

        human_prompt = f"""
CUSTOMER EVIDENCE:

{evidence}

RETRIEVED KNOWLEDGE:

{retrieved_knowledge}

Investigate this customer's fulfilment-related indicators.
"""

        print(
            f"[FULFILMENT] Starting Groq request for {customer_id}",
            flush=True
        )

        response = await asyncio.wait_for(
            model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]),
            timeout=LLM_TIMEOUT
        )

        print(
            f"[FULFILMENT] Groq response received for {customer_id}",
            flush=True
        )

        analysis = {
            "customer_id": customer_id,
            "investigation": response.content,
            "knowledge_sources": [
                {
                    "category": document.get("category"),
                    "source": document.get("source"),
                    "similarity_score": document.get("similarity_score")
                }
                for document in retrieved_knowledge
            ]
        }

        return {
            "fulfilment_evidence": evidence,
            "retrieved_knowledge": retrieved_knowledge,
            "fulfilment_analysis": analysis,
            "errors": []
        }

    except asyncio.TimeoutError:
        print(
            f"[FULFILMENT] Timeout for customer {customer_id}",
            flush=True
        )

        return {
            "fulfilment_evidence": evidence,
            "fulfilment_analysis": {},
            "errors": [
                "Fulfilment investigation timed out during retrieval or LLM execution"
            ]
        }

    except Exception as error:
        print(
            f"[FULFILMENT] Error: {type(error).__name__}: {error}",
            flush=True
        )

        return {
            "fulfilment_evidence": {},
            "fulfilment_analysis": {},
            "errors": [
                f"Fulfilment Agent failed: {str(error)}"
            ]
        }
