
import os
import sys

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PYTHON_EXECUTABLE = sys.executable


MCP_SERVERS = {
    "postgres": "retention_intelligence.mcp_servers.postgres_server",
    "retention": "retention_intelligence.mcp_servers.retention_server"
}


def get_server_parameters(server_name: str) -> StdioServerParameters:
    """
    Build configuration for the selected MCP server.
    """

    module_name = MCP_SERVERS.get(server_name)

    if not module_name:
        raise ValueError(
            f"Unknown MCP server: {server_name}"
        )

    environment = os.environ.copy()

    source_path = str(PROJECT_ROOT / "src")

    existing_pythonpath = environment.get("PYTHONPATH", "")

    environment["PYTHONPATH"] = (
        source_path
        if not existing_pythonpath
        else source_path + os.pathsep + existing_pythonpath
    )

    return StdioServerParameters(
        command=PYTHON_EXECUTABLE,
        args=["-m", module_name],
        env=environment,
        cwd=str(PROJECT_ROOT)
    )


async def discover_mcp_tools(
    server_name: str
) -> list[dict[str, Any]]:
    """
    Discover available tools from an MCP server.
    """

    server_parameters = get_server_parameters(server_name)

    async with stdio_client(server_parameters) as (
        read_stream,
        write_stream
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            response = await session.list_tools()

            tools = []

            for tool in response.tools:
                tools.append({
                    "server": server_name,
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema
                })

            return tools


async def discover_all_mcp_tools() -> list[dict[str, Any]]:
    """
    Discover tools from both PostgreSQL and Retention MCP servers.
    """

    all_tools = []

    for server_name in MCP_SERVERS:

        tools = await discover_mcp_tools(server_name)

        all_tools.extend(tools)

    return all_tools


async def call_mcp_tool(
    server_name: str,
    tool_name: str,
    arguments: dict[str, Any]
) -> Any:
    """
    Execute a tool on the selected MCP server.
    """

    server_parameters = get_server_parameters(server_name)

    async with stdio_client(server_parameters) as (
        read_stream,
        write_stream
    ):
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            available_tools = await session.list_tools()

            valid_tool_names = {
                tool.name for tool in available_tools.tools
            }

            if tool_name not in valid_tool_names:
                raise ValueError(
                    f"Tool '{tool_name}' not found "
                    f"on MCP server '{server_name}'"
                )

            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )

            if result.isError:
                error_messages = [
                    block.text
                    for block in result.content
                    if hasattr(block, "text")
                ]

                raise RuntimeError(
                    "; ".join(error_messages)
                    or "MCP tool execution failed"
                )

            if result.structuredContent is not None:
                return result.structuredContent

            return [
                block.text
                for block in result.content
                if hasattr(block, "text")
            ]
