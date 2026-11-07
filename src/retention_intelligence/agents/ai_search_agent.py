import asyncio
import json
import re
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from retention_intelligence.agents.state import RetentionState
from retention_intelligence.services.mcp_client import (
    discover_all_mcp_tools,
    call_mcp_tool
)

load_dotenv()

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    timeout=45,
    max_retries=1
)

MAX_TOOL_CALLS = 5
DISCOVERY_TIMEOUT = 35
MCP_TIMEOUT = 40
LLM_TIMEOUT = 50


SYSTEM_PROMPT = """
You are an AI Search Agent for Customer Churn and
Retention Through Fulfilment Intelligence.

Your job is to answer admin queries using available MCP tools.

AVAILABLE MCP SERVERS:

1. PostgreSQL MCP Server:
   - get_customer_profile
   - get_customer_count
   - find_inactive_olist_customers

2. Retention MCP Server:
   - search_retention_knowledge
   - get_knowledge_base_status

RULES:

1. Use MCP tools whenever the question requires database
   or knowledge-base information.
2. Never invent customer records, statistics or evidence.
3. For customer-specific queries, identify the source
   and customer ID before calling the profile tool.
4. For Olist inactivity queries, use the inactive customer tool.
5. For retention or fulfilment guidance, search Milvus.
6. You may call multiple tools when necessary.
7. Do not claim that inactivity confirms customer churn.
8. Clearly distinguish retrieved facts from interpretations.
9. If evidence is unavailable, explain the limitation.
10. Do not execute retention actions or modify customer records.

Return a clear, concise answer for an admin user.
"""


def _normalize_parsed_action(result: dict) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"action": "final_answer", "answer": str(result)}

    # Check for direct final_answer or answer key
    if "final_answer" in result:
        return {
            "action": "final_answer",
            "answer": str(result["final_answer"])
        }

    if "answer" in result and result.get("action") != "tool_call":
        return {
            "action": "final_answer",
            "answer": str(result["answer"])
        }

    action = result.get("action")
    if action == "tool_call" or "tool" in result:
        return {
            "action": "tool_call",
            "server": result.get("server", ""),
            "tool": result.get("tool", ""),
            "arguments": result.get("arguments", {})
        }

    if action == "final_answer":
        return result

    for key in ("summary", "message", "response", "result"):
        if key in result and isinstance(result[key], str):
            return {
                "action": "final_answer",
                "answer": result[key]
            }

    return result


def parse_tool_arguments(content: str) -> dict[str, Any]:
    if not isinstance(content, str):
        raise ValueError("Unexpected Groq response format")

    content = content.strip()

    # 1. Check for markdown code blocks
    if "```" in content:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if match:
            candidate = match.group(1).strip()
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return _normalize_parsed_action(parsed)
            except json.JSONDecodeError:
                pass

    # 2. Extract JSON from between first { and last }
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = content[first_brace:last_brace + 1]
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return _normalize_parsed_action(parsed)
        except json.JSONDecodeError:
            pass

    # 3. If no JSON could be parsed, it's a direct textual answer from the model
    return {
        "action": "final_answer",
        "answer": content
    }


async def ai_search_agent(state: RetentionState):
    question = state.get("question", "").strip()

    if not question:
        return {
            "ai_search_result": {
                "status": "error",
                "answer": "Please enter a search question.",
                "sources": []
            },
            "errors": ["AI Search question is missing"]
        }

    collected_results = []

    try:
        # 1. Discover MCP tools
        print("[AI SEARCH] Discovering MCP tools...", flush=True)

        available_tools = await asyncio.wait_for(
            discover_all_mcp_tools(),
            timeout=DISCOVERY_TIMEOUT
        )

        if not available_tools:
            raise RuntimeError("No MCP tools are available")

        tool_descriptions = "\n".join(
            [
                (
                    f"Server: {tool['server']}\n"
                    f"Tool: {tool['name']}\n"
                    f"Description: {tool['description']}\n"
                    f"Arguments: {json.dumps(tool['input_schema'])}"
                )
                for tool in available_tools
            ]
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"""
ADMIN QUESTION:

{question}

AVAILABLE MCP TOOLS:

{tool_descriptions}

Choose the appropriate MCP tool.

If a tool is required, return ONLY this JSON format:

{{
    "action": "tool_call",
    "server": "postgres",
    "tool": "get_customer_count",
    "arguments": {{
        "source": "olist"
    }}
}}

If no tool is required, return:

{{
    "action": "final_answer",
    "answer": "Your answer"
}}
""")
        ]

        # 2. LLM and MCP execution loop
        for tool_call_count in range(MAX_TOOL_CALLS):
            print(
                f"[AI SEARCH] Groq request {tool_call_count + 1}",
                flush=True
            )

            response = await asyncio.wait_for(
                model.ainvoke(messages),
                timeout=LLM_TIMEOUT
            )

            result = parse_tool_arguments(response.content)
            action = result.get("action")

            if action == "final_answer":
                answer = result.get("answer", "")
                if not isinstance(answer, str):
                    answer = str(answer)

                return {
                    "ai_search_result": {
                        "status": "success",
                        "question": question,
                        "answer": answer,
                        "sources": collected_results
                    },
                    "errors": []
                }

            if action != "tool_call":
                # Fallback: treat unknown action as final answer if it has text
                return {
                    "ai_search_result": {
                        "status": "success",
                        "question": question,
                        "answer": str(response.content),
                        "sources": collected_results
                    },
                    "errors": []
                }

            server_name = result.get("server")
            tool_name = result.get("tool")
            arguments = result.get("arguments", {})

            if not isinstance(arguments, dict):
                arguments = {}

            # Infer server if omitted or mismatched
            matching_tool = next(
                (
                    tool for tool in available_tools
                    if tool["name"] == tool_name
                    and (not server_name or tool["server"] == server_name)
                ),
                None
            )

            if matching_tool is None:
                # Also check case-insensitive
                matching_tool = next(
                    (
                        tool for tool in available_tools
                        if tool["name"].lower() == str(tool_name).lower()
                    ),
                    None
                )

            if matching_tool is None:
                messages.append(
                    SystemMessage(
                        content=(
                            f"Tool '{tool_name}' is not recognized. "
                            f"Available tools: {[t['name'] for t in available_tools]}. "
                            "Please choose an available tool or provide a final_answer."
                        )
                    )
                )
                continue

            server_name = matching_tool["server"]
            tool_name = matching_tool["name"]

            print(
                f"[AI SEARCH] Calling {server_name}.{tool_name}",
                flush=True
            )

            tool_result = await asyncio.wait_for(
                call_mcp_tool(
                    server_name=server_name,
                    tool_name=tool_name,
                    arguments=arguments
                ),
                timeout=MCP_TIMEOUT
            )

            collected_results.append({
                "server": server_name,
                "tool": tool_name,
                "arguments": arguments,
                "result": tool_result
            })

            messages.append(
                SystemMessage(
                    content=(
                        f"MCP TOOL RESULT:\n"
                        f"{json.dumps(tool_result, default=str)}\n\n"
                        "Use this evidence to answer the original question. "
                        "Return a final_answer JSON object:\n"
                        '{"action": "final_answer", "answer": "Your answer"}'
                    )
                )
            )

        raise RuntimeError("Maximum MCP tool call limit reached")

    except asyncio.TimeoutError:
        error_message = "AI Search timed out"
        print(f"[AI SEARCH] {error_message}", flush=True)

        return {
            "ai_search_result": {
                "status": "error",
                "question": question,
                "answer": error_message,
                "sources": collected_results
            },
            "errors": [error_message]
        }

    except Exception as error:
        error_message = f"{type(error).__name__}: {str(error)}"
        print(f"[AI SEARCH] Failed: {error_message}", flush=True)

        return {
            "ai_search_result": {
                "status": "error",
                "question": question,
                "answer": (
                    "AI Search could not complete the request: "
                    f"{error_message}"
                ),
                "sources": collected_results
            },
            "errors": [
                f"AI Search Agent failed: {error_message}"
            ]
        }
