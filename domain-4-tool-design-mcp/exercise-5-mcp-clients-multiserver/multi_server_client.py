"""
multi_server_client.py — Domain 4, Concept 5: MCP clients — discovery,
invocation, and multi-server routing.

Connects to TWO independent MCP servers simultaneously (order_server.py,
hr_server.py) — exactly what a host application (Claude Desktop, Claude
Code with multiple configured MCP servers) does in practice. This tests
the real, practical problem: BOTH servers expose a tool named
`get_status`, with completely different meanings and arguments.

FIRST: demonstrate the collision happening (a naive aggregation keyed
only by tool name silently overwrites one server's tool with the
other's).

THEN: demonstrate the standard fix — namespace every tool with its
server's name (`ordersservice__get_status`, `hrservice__get_status`),
so the aggregated registry has no collisions and a caller can always
route to the correct server unambiguously.
"""

import asyncio
import sys
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVERS = {
    "orders": "order_server.py",
    "hr": "hr_server.py",
}


async def connect_all(stack: AsyncExitStack) -> dict:
    """Connects to every configured server, returns {server_key: ClientSession}."""
    sessions = {}
    for key, script in SERVERS.items():
        params = StdioServerParameters(command=sys.executable, args=[script])
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        sessions[key] = session
    return sessions


async def demonstrate_collision(sessions: dict):
    print("=" * 70)
    print("STEP 1: Naive aggregation — keyed ONLY by tool name")
    print("=" * 70)
    naive_registry = {}
    for server_key, session in sessions.items():
        tools = await session.list_tools()
        for t in tools.tools:
            if t.name in naive_registry:
                print(f"  !! COLLISION: '{t.name}' from '{server_key}' silently "
                      f"OVERWRITES the existing entry from "
                      f"'{naive_registry[t.name][0]}'")
            naive_registry[t.name] = (server_key, t)
    print(f"\n  Naive registry ended up with: {list(naive_registry.keys())}")
    print(f"  Only ONE server's 'get_status' is reachable — the other's tool")
    print(f"  is completely inaccessible through this registry, with no error")
    print(f"  raised anywhere. This is a silent correctness bug, not a crash.")


async def demonstrate_namespaced_fix(sessions: dict):
    print("\n" + "=" * 70)
    print("STEP 2: The fix — namespace every tool with its server key")
    print("=" * 70)
    namespaced_registry = {}
    for server_key, session in sessions.items():
        tools = await session.list_tools()
        for t in tools.tools:
            namespaced_name = f"{server_key}__{t.name}"
            namespaced_registry[namespaced_name] = (server_key, t.name, session)
    print(f"  Namespaced registry: {list(namespaced_registry.keys())}")
    print(f"  Both servers' 'get_status' are now independently reachable.\n")

    print("  Invoking BOTH get_status tools through the namespaced registry:")
    for namespaced_name, (server_key, real_name, session) in namespaced_registry.items():
        if real_name != "get_status":
            continue
        arg_id = "4471" if server_key == "orders" else "EMP-1001"
        arg_name = "order_id" if server_key == "orders" else "employee_id"
        result = await session.call_tool(real_name, {arg_name: arg_id})
        text = "".join(b.text for b in result.content)
        print(f"    {namespaced_name}({arg_name}={arg_id}) -> {text}")


async def main():
    async with AsyncExitStack() as stack:
        sessions = await connect_all(stack)
        print(f"Connected to {len(sessions)} servers: {list(sessions.keys())}\n")
        await demonstrate_collision(sessions)
        await demonstrate_namespaced_fix(sessions)


if __name__ == "__main__":
    asyncio.run(main())
