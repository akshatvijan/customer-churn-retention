
import json

from retention_intelligence.agents.state import RetentionState
from retention_intelligence.services.mcp_client import call_mcp_tool


def normalize_mcp_response(result):

    # MCP returned a list containing JSON text
    if isinstance(result, list):

        if not result:
            raise ValueError("MCP returned an empty response")

        normalized_items = []

        for item in result:

            if isinstance(item, dict):
                normalized_items.append(item)

            elif isinstance(item, str):

                try:
                    parsed = json.loads(item)
                    normalized_items.append(parsed)

                except json.JSONDecodeError:
                    continue

        if not normalized_items:
            raise ValueError(
                f"Could not parse MCP response: {result}"
            )

        # Find the actual customer profile response
        for item in normalized_items:

            if item.get("status") in ("success", "not_found"):
                return item

        raise ValueError(
            f"No valid status found in MCP response: {normalized_items}"
        )

    # MCP directly returned a dictionary
    if isinstance(result, dict):
        return result

    raise ValueError(
        f"Unsupported MCP response type: {type(result).__name__}"
    )


async def customer_profile_agent(state: RetentionState):

    customer_id = state.get("customer_id")
    source = state.get("source")

    print("\n========== CUSTOMER PROFILE DEBUG ==========")
    print("Requested customer ID:", customer_id)
    print("Source:", source)

    if not customer_id:
        return {
            "customer_data": {},
            "errors": ["Customer ID is missing"]
        }

    customer_id = str(customer_id).strip()

    if source not in ("olist", "telco"):
        return {
            "customer_data": {},
            "errors": ["Invalid customer source"]
        }

    try:

        print("Calling PostgreSQL MCP...")

        raw_result = await call_mcp_tool(
            server_name="postgres",
            tool_name="get_customer_profile",
            arguments={
                "source": source,
                "customer_id": customer_id
            }
        )

        print("\nRAW MCP RESPONSE:")
        print(repr(raw_result))

        # Normalize MCP response
        result = normalize_mcp_response(raw_result)

        print("\nNORMALIZED MCP RESPONSE:")
        print(result)

        if result.get("status") == "not_found":
            raise ValueError(
                f"{source.capitalize()} customer not found: {customer_id}"
            )

        if result.get("status") != "success":
            raise ValueError(
                result.get("message", "Customer retrieval failed")
            )

        customer_data = result.get("customer_data", {})

        if not isinstance(customer_data, dict) or not customer_data:
            raise ValueError(
                "Customer data is missing from MCP response"
            )

        returned_customer_id = str(
            customer_data.get("customer_id", "")
        ).strip()

        if returned_customer_id != customer_id:
            raise ValueError(
                f"Customer ID mismatch. Requested: {customer_id}, "
                f"Received: {returned_customer_id}"
            )

        print("\nCUSTOMER PROFILE SUCCESSFULLY RETRIEVED:")
        print(customer_data)
        print("============================================\n")

        return {
            "customer_data": customer_data,
            "errors": []
        }

    except Exception as error:

        error_message = (
            f"{type(error).__name__}: {str(error)}"
        )

        print("\nCUSTOMER PROFILE ERROR:")
        print(error_message)
        print("============================================\n")

        return {
            "customer_data": {},
            "errors": [
                f"Customer Profile Agent failed: {error_message}"
            ]
        }
