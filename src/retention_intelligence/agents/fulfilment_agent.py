
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from retention_intelligence.agents.state import RetentionState
from retention_intelligence.rag.retrieval import retrieve_knowledge

load_dotenv()


model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


async def fulfilment_agent(state: RetentionState):

    source = state.get("source")
    customer_data = state.get("customer_data", {})

    # Fulfilment investigation is currently Olist-only
    if source != "olist":
        return {
            "fulfilment_evidence": {},
            "fulfilment_analysis": {},
            "errors": [
                "Fulfilment investigation is supported for Olist only"
            ]
        }

    if not customer_data:
        return {
            "fulfilment_evidence": {},
            "fulfilment_analysis": {},
            "errors": ["Customer data is missing"]
        }

    customer_id = customer_data.get("customer_id")

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
            "days_since_last_order": customer_data.get(
                "days_since_last_order"
            ),
            "retention_risk_proxy": customer_data.get(
                "retention_risk_proxy"
            )
        }

        # Step 2: Build investigation query
        query = (
            f"Investigate customer fulfilment and inactivity indicators. "
            f"Total orders: {evidence['total_orders']}. "
            f"Delivered orders: {evidence['delivered_orders']}. "
            f"Cancelled orders: {evidence['cancelled_orders']}. "
            f"Days since last order: {evidence['days_since_last_order']}. "
            f"Retention risk proxy: {evidence['retention_risk_proxy']}."
        )

        # Step 3: Retrieve relevant knowledge from Milvus
        retrieved_knowledge = retrieve_knowledge(
            query=query,
            top_k=3
        )

        if not retrieved_knowledge:
            raise ValueError("No relevant knowledge found in Milvus")

        # Step 4: Prepare grounded LLM input
        system_prompt = """
        You are a Fulfilment Investigation Agent.

        Your responsibility is to investigate customer fulfilment-related
        indicators using the provided customer evidence and retrieved knowledge.

        STRICT RULES:

        1. Use only the supplied customer evidence.
        2. Do not invent delivery delays, review sentiments,
           complaint reasons or other missing information.
        3. Do not claim that a specific fulfilment issue caused churn.
        4. An inactivity-based retention risk proxy is not confirmed churn.
        5. Clearly distinguish observed facts from possible interpretations.
        6. If evidence is insufficient, explicitly mention the limitation.
        7. Return a concise, structured investigation.

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

        # Step 5: Generate investigation
        response = await model.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])

        analysis = {
            "customer_id": customer_id,
            "investigation": response.content,
            "knowledge_sources": [
                {
                    "category": document["category"],
                    "source": document["source"],
                    "similarity_score": document["similarity_score"]
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

    except Exception as error:

        return {
            "fulfilment_evidence": {},
            "fulfilment_analysis": {},
            "errors": [
                f"Fulfilment Agent failed: {str(error)}"
            ]
        }
