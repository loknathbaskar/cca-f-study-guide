"""
mcp_client_demo.py — Domain 4, Concept 4: A real MCP client connecting to
order_server.py via stdio transport.

This is the CLIENT side of the architecture: it spawns the server as a
subprocess, speaks MCP over stdio, and exercises all three primitives —
listing what's available, then invoking each one, so you can see the
actual request/response shape for each rather than just reading about
the distinction.
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        # Use sys.executable, not a bare "python3" — a bare command name
        # resolves via PATH and can silently pick up a DIFFERENT Python
        # environment than the one running this client script (exactly
        # what happened here: the client correctly used this venv's mcp
        # 1.9.4, but a bare "python3" spawned the server using the
        # system Python's broken mcp 2.1.1 install instead).
        command=sys.executable,
        args=["order_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("=" * 70)
            print("DISCOVERY — what does this server expose?")
            print("=" * 70)

            tools = await session.list_tools()
            print(f"\nTOOLS ({len(tools.tools)}):")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")
                print(f"    schema: {t.inputSchema}")

            resources = await session.list_resources()
            print(f"\nRESOURCES ({len(resources.resources)}):")
            for r in resources.resources:
                print(f"  - {r.uri}: {r.name}")

            prompts = await session.list_prompts()
            print(f"\nPROMPTS ({len(prompts.prompts)}):")
            for p in prompts.prompts:
                print(f"  - {p.name}: {p.description}")
                print(f"    arguments: {p.arguments}")

            print("\n" + "=" * 70)
            print("INVOCATION — call each primitive once")
            print("=" * 70)

            print("\n--- Calling TOOL: get_order_status('4471') ---")
            tool_result = await session.call_tool("get_order_status", {"order_id": "4471"})
            for block in tool_result.content:
                print(f"  {block.text}")

            print("\n--- Reading RESOURCE: orders://all ---")
            resource_result = await session.read_resource("orders://all")
            for block in resource_result.contents:
                print(f"  {block.text}")

            print("\n--- Getting PROMPT: order_summary_prompt('8821') ---")
            prompt_result = await session.get_prompt("order_summary_prompt", {"order_id": "8821"})
            for msg in prompt_result.messages:
                print(f"  [{msg.role}] {msg.content.text}")


if __name__ == "__main__":
    asyncio.run(main())
