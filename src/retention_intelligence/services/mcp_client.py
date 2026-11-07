import os
import sys
import asyncio
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PYTHON_EXECUTABLE = sys.executable

INITIALIZE_TIMEOUT = 20
DISCOVERY_TIMEOUT = 20
TOOL_EXECUTION_TIMEOUT = 60

MCP_SERVERS = {
    "postgres": "retention_intelligence.mcp_servers.postgres_server",
    "retention": "retention_intelligence.mcp_servers.retention_server"
}


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def log_full_exception(error: BaseException) -> None:
    log("[MCP] FULL EXCEPTION TRACEBACK:")
    traceback.print_exception(
        type(error),
        error,
        error.__traceback__,
        file=sys.stderr
    )


def _get_inprocess_server(server_name: str):
    try:
        if server_name == "postgres":
            from retention_intelligence.mcp_servers.postgres_server import mcp as pg_mcp
            return pg_mcp
        elif server_name == "retention":
            from retention_intelligence.mcp_servers.retention_server import mcp as ret_mcp
            return ret_mcp
    except Exception as exc:
        log(f"[MCP] Failed to load in-process {server_name} server: {exc}")
    return None


def get_server_parameters(server_name: str):
    from mcp import StdioServerParameters

    module_name = MCP_SERVERS.get(server_name)
    if not module_name:
        raise ValueError(f"Unknown MCP server: {server_name}")

    environment = os.environ.copy()
    source_path = str(PROJECT_ROOT / "src")
    existing_pythonpath = environment.get("PYTHONPATH", "")

    environment["PYTHONPATH"] = (
        source_path
        if not existing_pythonpath
        else source_path + os.pathsep + existing_pythonpath
    )
    environment["PYTHONUNBUFFERED"] = "1"

    return StdioServerParameters(
        command=PYTHON_EXECUTABLE,
        args=["-m", module_name],
        env=environment,
        cwd=str(PROJECT_ROOT)
    )


async def discover_mcp_tools(server_name: str) -> list[dict[str, Any]]:
    log(f"[MCP] Discovering tools: {server_name}")

    # 1. Fast in-process discovery
    server = _get_inprocess_server(server_name)
    if server is not None:
        try:
            tools = await server.list_tools()
            result = []
            for tool in tools:
                result.append({
                    "server": server_name,
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema
                })
            log(f"[MCP] Discovered {len(result)} tools from {server_name} (in-process)")
            return result
        except Exception as exc:
            log(f"[MCP] In-process tool discovery failed for {server_name}: {exc}")

    # 2. Fallback to stdio
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client

        server_parameters = get_server_parameters(server_name)
        async with stdio_client(server_parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=INITIALIZE_TIMEOUT)
                response = await asyncio.wait_for(session.list_tools(), timeout=DISCOVERY_TIMEOUT)
                tools = []
                for tool in response.tools:
                    tools.append({
                        "server": server_name,
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema
                    })
                return tools
    except BaseException as error:
        log_full_exception(error)
        raise


async def discover_all_mcp_tools() -> list[dict[str, Any]]:
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
    log(f"[MCP] Calling {server_name}.{tool_name}")

    # 1. Fast in-process execution
    server = _get_inprocess_server(server_name)
    if server is not None:
        try:
            result = await server.call_tool(tool_name, arguments)
            if isinstance(result, list):
                return [b.text for b in result if hasattr(b, "text")]
            elif hasattr(result, "text"):
                return [result.text]
            return result
        except Exception as exc:
            log(f"[MCP] In-process tool call failed for {server_name}.{tool_name}: {exc}")

    # 2. Fallback to stdio
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client

        server_parameters = get_server_parameters(server_name)
        async with stdio_client(server_parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=INITIALIZE_TIMEOUT)
                available_tools = await asyncio.wait_for(session.list_tools(), timeout=DISCOVERY_TIMEOUT)
                valid_tool_names = {tool.name for tool in available_tools.tools}

                if tool_name not in valid_tool_names:
                    raise ValueError(f"Tool '{tool_name}' not found on MCP server '{server_name}'")

                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments=arguments),
                    timeout=TOOL_EXECUTION_TIMEOUT
                )

                if result.isError:
                    error_messages = [
                        block.text for block in result.content if hasattr(block, "text")
                    ]
                    raise RuntimeError("; ".join(error_messages) or "MCP tool execution failed")

                if result.structuredContent is not None:
                    return result.structuredContent

                return [
                    block.text for block in result.content if hasattr(block, "text")
                ]
    except BaseException as error:
        log_full_exception(error)
        raise
