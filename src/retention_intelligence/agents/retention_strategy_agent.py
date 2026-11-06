
import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from retention_intelligence.agents.state import RetentionState
from retention_intelligence.services.mcp_client import call_mcp_tool
from retention_intelligence.guardrails.validation_pipeline import (
    validate_retention_output
)


load_dotenv()


model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


ALLOWED_ACTION_TYPES = {
    "personalised_reengagement",
    "customer_support_followup",
    "loyalty_reward",
    "product_recommendation"
}


# ---------------------------------
# 1. JSON Response Parser
# ---------------------------------

def parse_json_response(response_text: str) -> dict:

    if not response_text:
        raise ValueError("LLM returned an empty response")

    if not isinstance(response_text, str):
        raise ValueError(
            f"Expected string response, received "
            f"{type(response_text).__name__}"
        )

    response_text = response_text.strip()

    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "").strip()

    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            f"Valid JSON object not found: {response_text[:500]}"
        )

    parsed = json.loads(response_text[start:end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object")

    return parsed


# ---------------------------------
# 2. Normalize Retention MCP Response
# ---------------------------------

def normalize_retention_mcp_response(result):

    if isinstance(result, dict):
        return result

    if isinstance(result, list):

        parsed_items = []

        for item in result:

            if isinstance(item, dict):
                parsed_items.append(item)

            elif isinstance(item, str):

                try:
                    parsed = json.loads(item)

                    if isinstance(parsed, dict):
                        parsed_items.append(parsed)

                except json.JSONDecodeError:
                    continue

        if not parsed_items:
            raise ValueError(
                f"Could not parse Retention MCP response: {repr(result)}"
            )

        for item in parsed_items:

            if item.get("status") in ("success", "error"):
                return item

        if len(parsed_items) == 1:
            return parsed_items[0]

        raise ValueError(
            f"No valid status found in MCP response: {parsed_items}"
        )

    if isinstance(result, str):

        try:
            parsed = json.loads(result)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON from Retention MCP: {str(error)}"
            ) from error

    raise ValueError(
        f"Unsupported Retention MCP response type: "
        f"{type(result).__name__}"
    )


# ---------------------------------
# 3. Retention Strategy Agent
# ---------------------------------

async def retention_strategy_agent(state: RetentionState):

    customer_data = state.get("customer_data", {})
    churn_prediction = state.get("churn_prediction", {})
    fulfilment_analysis = state.get("fulfilment_analysis", {})
    source = state.get("source")

    customer_id = (
        customer_data.get("customer_id")
        or customer_data.get("customer_unique_id")
        or customer_data.get("customerID")
        or state.get("customer_id")
    )

    print("\n========== RETENTION STRATEGY DEBUG ==========")
    print("Customer ID:", customer_id)
    print("Source:", source)
    print("Customer Data:", customer_data)
    print("Churn Prediction:", churn_prediction)

    # ---------------------------------
    # 4. Basic Input Validation
    # ---------------------------------

    if source not in ("olist", "telco"):

        return {
            "candidate_actions": [],
            "retention_strategy": {},
            "errors": ["Unsupported customer data source"]
        }

    if not customer_data:

        return {
            "candidate_actions": [],
            "retention_strategy": {},
            "errors": ["Customer data is missing"]
        }

    if not churn_prediction:

        return {
            "candidate_actions": [],
            "retention_strategy": {},
            "errors": ["Churn prediction is missing"]
        }

    try:

        # ---------------------------------
        # 5. Retrieve Retention Knowledge Through MCP
        # ---------------------------------

        retrieval_query = (
            f"Retention strategy for {source} customer. "
            f"Customer data: {json.dumps(customer_data, default=str)}. "
            f"Churn prediction: {json.dumps(churn_prediction, default=str)}. "
            f"Fulfilment investigation: "
            f"{json.dumps(fulfilment_analysis, default=str)}"
        )

        print("\nCalling Retention MCP Server...")

        raw_mcp_result = await call_mcp_tool(
            server_name="retention",
            tool_name="search_retention_knowledge",
            arguments={
                "query": retrieval_query,
                "top_k": 5,
                "category": "retention_strategy"
            }
        )

        print("\n========== RETENTION MCP DEBUG ==========")
        print("RAW RESPONSE:")
        print(repr(raw_mcp_result))

        mcp_result = normalize_retention_mcp_response(
            raw_mcp_result
        )

        print("\nNORMALIZED RESPONSE:")
        print(mcp_result)

        if mcp_result.get("status") != "success":

            raise ValueError(
                mcp_result.get(
                    "message",
                    "Retention MCP knowledge search failed"
                )
            )

        retrieved_knowledge = mcp_result.get("results", [])

        if not isinstance(retrieved_knowledge, list):

            raise ValueError(
                "Retention MCP results must be a list"
            )

        if not retrieved_knowledge:

            raise ValueError(
                "No retention knowledge retrieved from Milvus"
            )

        knowledge_context = [
            {
                "text": document.get("text", ""),
                "metadata": document.get("metadata", {})
            }
            for document in retrieved_knowledge
            if isinstance(document, dict)
        ]

        if not knowledge_context:

            raise ValueError(
                "Retrieved retention knowledge is invalid"
            )

        print(
            "\nRetrieved knowledge documents:",
            len(knowledge_context)
        )

        # ---------------------------------
        # 6. System Prompt
        # ---------------------------------

        system_prompt = """
You are a Customer Retention Strategy Agent.

Your responsibility is to suggest evidence-based candidate
retention actions using customer data and retrieved knowledge.

STRICT RULES:

1. Use only supplied customer data, churn prediction,
   fulfilment investigation and retrieved knowledge.

2. Never invent customer preferences, complaints,
   delivery delays or cancellation reasons.

3. Do not treat an inactivity proxy as confirmed churn.

4. Generate candidate actions only.
   Never generate approved actions.

5. Do not execute actions or promise rewards.

6. Every candidate action must require human approval
   and subsequent deterministic policy validation.

7. Use only these action types:

   - personalised_reengagement
   - customer_support_followup
   - loyalty_reward
   - product_recommendation

8. If the customer has high inactivity or a high retention
   risk proxy, consider personalised_reengagement when
   the available evidence supports it.

9. If cancelled_orders is greater than zero, consider
   customer_support_followup, but do not invent cancellation
   reasons.

10. Suggest loyalty_reward only when customer evidence
    provides a reasonable basis for considering a reward.
    Mention that eligibility and campaign budget must
    be verified.

11. Product recommendations must not assume preferences
    or popular products that are not in the supplied evidence.

12. If evidence is insufficient for a particular action,
    do not generate that action.

13. Missing delivery or complaint data does not mean
    there were no delivery issues or complaints.
    Mention these limitations where relevant.

14. Never claim that an action will definitely prevent churn.

15. Never promise an unapproved reward or discount.

16. Use numeric values exactly as supplied.
    Do not invent currency symbols or amounts.

17. Generate candidate actions when available evidence
    supports a valid recommendation.

18. If no action is supported, return an empty list and
    explain the reason in evidence_limitations.

Return ONLY a valid JSON object in this structure:

{
    "strategy_summary": "Short strategy summary",
    "candidate_actions": [
        {
            "action_type": "personalised_reengagement",
            "description": "Suggested action",
            "reason": "Evidence supporting the action",
            "priority": "high",
            "requires_approval": true
        }
    ],
    "evidence_limitations": [
        "Limitations in the available evidence"
    ]
}

Priority must be high, medium or low.

Do not include markdown or text outside the JSON object.
"""

        # ---------------------------------
        # 7. Human Prompt
        # ---------------------------------

        human_prompt = f"""
CUSTOMER SOURCE:
{source}

CUSTOMER ID:
{customer_id}

CUSTOMER DATA:
{json.dumps(customer_data, indent=2, default=str)}

CHURN PREDICTION:
{json.dumps(churn_prediction, indent=2, default=str)}

FULFILMENT INVESTIGATION:
{json.dumps(fulfilment_analysis, indent=2, default=str)}

RETRIEVED RETENTION KNOWLEDGE:
{json.dumps(knowledge_context, indent=2, default=str)}

Analyze the evidence and generate suitable candidate
retention actions following all system rules.
"""

        # ---------------------------------
        # 8. Invoke Groq LLM
        # ---------------------------------

        print("\nInvoking Groq Retention Strategy Model...")

        response = await model.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])

        response_content = response.content

        print("\n========== GROQ RESPONSE ==========")
        print(response_content)

        if not isinstance(response_content, str):

            raise ValueError(
                "Groq returned an unexpected response content type"
            )

        # ---------------------------------
        # 9. Parse LLM Response
        # ---------------------------------

        parsed_response = parse_json_response(
            response_content
        )

        strategy_summary = parsed_response.get(
            "strategy_summary",
            ""
        )

        generated_actions = parsed_response.get(
            "candidate_actions",
            []
        )

        evidence_limitations = parsed_response.get(
            "evidence_limitations",
            []
        )

        if not isinstance(strategy_summary, str):
            raise ValueError(
                "strategy_summary must be a string"
            )

        if not isinstance(generated_actions, list):
            raise ValueError(
                "candidate_actions must be a list"
            )

        if not isinstance(evidence_limitations, list):
            raise ValueError(
                "evidence_limitations must be a list"
            )

        print("\nLLM GENERATED ACTIONS:")
        print(generated_actions)

        # ---------------------------------
        # 10. Filter Candidate Actions
        # ---------------------------------

        candidate_actions = []
        rejected_generation_actions = []

        for index, action in enumerate(generated_actions):

            if not isinstance(action, dict):

                rejected_generation_actions.append({
                    "index": index,
                    "reason": "Action is not a dictionary"
                })

                continue

            action_type = action.get("action_type")

            if action_type not in ALLOWED_ACTION_TYPES:

                rejected_generation_actions.append({
                    "index": index,
                    "reason": f"Unsupported action type: {action_type}"
                })

                continue

            priority = action.get("priority", "medium")

            if priority not in ("high", "medium", "low"):
                priority = "medium"

            description = action.get("description", "")
            reason = action.get("reason", "")

            if (
                not isinstance(description, str)
                or not description.strip()
            ):

                rejected_generation_actions.append({
                    "index": index,
                    "reason": "Missing or invalid description"
                })

                continue

            if not isinstance(reason, str) or not reason.strip():

                rejected_generation_actions.append({
                    "index": index,
                    "reason": "Missing or invalid reason"
                })

                continue

            if action.get("requires_approval") is not True:

                rejected_generation_actions.append({
                    "index": index,
                    "reason": "requires_approval must be true"
                })

                continue

            candidate_actions.append({
                "action_type": action_type,
                "description": description.strip(),
                "reason": reason.strip(),
                "priority": priority,
                "requires_approval": True,
                "status": "candidate"
            })

        print("\nFILTERED CANDIDATE ACTIONS:")
        print(candidate_actions)

        print("\nREJECTED GENERATED ACTIONS:")
        print(rejected_generation_actions)

        # ---------------------------------
        # 11. Handle Empty Candidate Actions
        # ---------------------------------

        if not candidate_actions:

            return {
                "candidate_actions": [],
                "retention_strategy": {
                    "customer_id": customer_id,
                    "source": source,
                    "strategy_summary": strategy_summary,
                    "evidence_limitations": evidence_limitations,
                    "debug": {
                        "retrieved_knowledge_count": len(
                            retrieved_knowledge
                        ),
                        "llm_generated_action_count": len(
                            generated_actions
                        ),
                        "accepted_action_count": 0,
                        "rejected_generation_actions": (
                            rejected_generation_actions
                        ),
                        "llm_response": response_content
                    }
                },
                "errors": [
                    "No valid retention candidate actions generated. "
                    f"Generated: {len(generated_actions)}, "
                    f"accepted: 0. "
                    f"Filtering details: {rejected_generation_actions}"
                ]
            }

        # ---------------------------------
        # 12. Prepare Guardrails Input
        # ---------------------------------

        agent_output = {
            "strategy_summary": strategy_summary,
            "candidate_actions": candidate_actions,
            "evidence_limitations": evidence_limitations
        }

        # ---------------------------------
        # 13. Guardrails Validation
        # ---------------------------------

        print("\nRunning retention output validation...")

        validation_result = validate_retention_output(
            agent_output
        )

        print("\nGUARDRAILS RESULT:")
        print(validation_result)

        if not isinstance(validation_result, dict):

            raise ValueError(
                f"Unexpected guardrails response: {validation_result}"
            )

        if not validation_result.get("is_valid"):

            return {
                "candidate_actions": [],
                "retention_strategy": {
                    "customer_id": customer_id,
                    "source": source,
                    "debug": {
                        "validation_result": validation_result,
                        "filtered_action_count": len(candidate_actions)
                    }
                },
                "errors": [
                    f"Retention output validation failed: "
                    f"{validation_result}"
                ]
            }

        validated_output = validation_result.get("data")

        if not isinstance(validated_output, dict):

            raise ValueError(
                "Guardrails returned invalid or missing validated data"
            )

        candidate_actions = validated_output.get(
            "candidate_actions",
            []
        )

        strategy_summary = validated_output.get(
            "strategy_summary",
            strategy_summary
        )

        evidence_limitations = validated_output.get(
            "evidence_limitations",
            evidence_limitations
        )

        if not candidate_actions:

            raise ValueError(
                "Guardrails returned an empty candidate_actions list"
            )

        # ---------------------------------
        # 14. Build Final Retention Strategy
        # ---------------------------------

        retention_strategy = {
            "customer_id": customer_id,
            "source": source,
            "strategy_summary": strategy_summary,
            "evidence_limitations": evidence_limitations,
            "knowledge_sources": [
                {
                    "category": document.get("category"),
                    "source": document.get("source"),
                    "similarity_score": document.get("similarity_score")
                }
                for document in retrieved_knowledge
                if isinstance(document, dict)
            ],
            "debug": {
                "retrieved_knowledge_count": len(retrieved_knowledge),
                "llm_generated_action_count": len(generated_actions),
                "filtered_action_count": len(candidate_actions),
                "validation_status": "passed"
            }
        }

        print("\nRETENTION STRATEGY SUCCESS")
        print("Candidate action count:", len(candidate_actions))
        print("============================================\n")

        # ---------------------------------
        # 15. Return Agent Output
        # ---------------------------------

        return {
            "candidate_actions": candidate_actions,
            "retention_strategy": retention_strategy,
            "errors": []
        }

    except Exception as error:

        error_message = (
            f"{type(error).__name__}: {str(error)}"
        )

        print("\nRETENTION STRATEGY ERROR:")
        print(error_message)
        print("============================================\n")

        return {
            "candidate_actions": [],
            "retention_strategy": {
                "customer_id": customer_id,
                "source": source,
                "debug": {
                    "failure_stage": "retention_strategy_agent"
                }
            },
            "errors": [
                f"Retention strategy failed: {error_message}"
            ]
        }
