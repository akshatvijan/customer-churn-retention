
import json
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
    temperature=0
)


MAX_TOOL_CALLS = 5


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


def parse_tool_arguments(content: str) -> dict[str, Any]:

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        raise ValueError("Invalid JSON returned for MCP tool arguments")


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

    try:

        # Step 1: Discover available MCP tools
        available_tools = await discover_all_mcp_tools()

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

        # Step 2: Prepare messages
        messages = [
            SystemMessage(
                content=SYSTEM_PROMPT
            ),
            HumanMessage(
                content=f"""
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
"""
            )
        ]

        collected_results = []
        tool_call_count = 0

        # Step 3: Execute MCP tools
        while tool_call_count < MAX_TOOL_CALLS:

            response = await model.ainvoke(messages)

            content = response.content

            if not isinstance(content, str):
                raise ValueError("Unexpected Groq response format")

            result = parse_tool_arguments(content)

            action = result.get("action")

            if action == "final_answer":

                answer = result.get("answer", "")

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
                raise ValueError("Invalid AI Search action")

            server_name = result.get("server")
            tool_name = result.get("tool")
            arguments = result.get("arguments", {})

            if not isinstance(arguments, dict):
                raise ValueError("MCP tool arguments must be an object")

            # Validate selected server and tool
            matching_tool = next(
                (
                    tool for tool in available_tools
                    if tool["server"] == server_name
                    and tool["name"] == tool_name
                ),
                None
            )

            if matching_tool is None:
                raise ValueError("Selected MCP tool is not available")

            # Execute selected MCP tool
            tool_result = await call_mcp_tool(
                server_name=server_name,
                tool_name=tool_name,
                arguments=arguments
            )

            collected_results.append({
                "server": server_name,
                "tool": tool_name,
                "arguments": arguments,
                "result": tool_result
            })

            tool_call_count += 1

            # Step 4: Send tool result back to Groq
            messages.append(
                SystemMessage(
                    content=(
                        f"MCP TOOL RESULT:\n"
                        f"{json.dumps(tool_result, default=str)}\n\n"
                        "Use this evidence to answer the original question. "
                        "If another MCP tool is needed, return another "
                        "tool_call JSON. Otherwise return final_answer JSON."
                    )
                )
            )

        raise RuntimeError(
            "Maximum MCP tool call limit reached"
        )

    except Exception as error:

        return {
            "ai_search_result": {
                "status": "error",
                "question": question,
                "answer": (
                    "AI Search could not complete the request: "
                    f"{str(error)}"
                ),
                "sources": []
            },
            "errors": [
                f"AI Search Agent failed: {str(error)}"
            ]
        }
