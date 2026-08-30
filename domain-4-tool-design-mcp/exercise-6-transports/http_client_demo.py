"""
http_client_demo.py — Domain 4, Concept 6: Two SEPARATE clients
connecting to the SAME running StreamableHTTP server instance.

THE POINT: with stdio, running this same "two clients" experiment would
spawn TWO separate server subprocesses — each with its OWN _call_count,
starting fresh at 0 for each. With StreamableHTTP, both clients connect
to the ONE already-running server process over the network, sharing the
same in-memory state. The call counter proves this directly: if it goes
1, 2, 3... across BOTH clients rather than resetting between them,
that's concrete evidence of one shared server instance, not two
independent ones.

Run http_order_server.py in a separate process FIRST, then run this.
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SERVER_URL = "http://127.0.0.1:8123/mcp"


async def run_client(client_label: str, order_id: str):
    async with streamablehttp_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_order_status", {"order_id": order_id})
            text = "".join(b.text for b in result.content)
            print(f"  [{client_label}] {text}")


async def main():
    print("=" * 70)
    print("Client A connects, calls the tool once")
    print("=" * 70)
    await run_client("Client A", "4471")

    print()
    print("=" * 70)
    print("Client B connects SEPARATELY (different session), calls the tool")
    print("=" * 70)
    await run_client("Client B", "8821")

    print()
    print("=" * 70)
    print("Client A connects a SECOND time (new session again)")
    print("=" * 70)
    await run_client("Client A (again)", "4471")

    print()
    print("If the call counter kept incrementing across all three calls")
    print("(rather than resetting to #1 each time), that proves all three")
    print("connected to the SAME persistent server process — impossible")
    print("with stdio, where each client spawns its own fresh subprocess.")


if __name__ == "__main__":
    asyncio.run(main())
