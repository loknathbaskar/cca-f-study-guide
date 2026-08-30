"""
access_scoping_client.py — attempts a real path traversal exploit
against both the naive and hardened read_file tools.
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["access_scoping_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("=" * 70)
            print("Legitimate read — sandboxed file, should work on both")
            print("=" * 70)
            for tool in ("read_file_naive", "read_file_hardened"):
                result = await session.call_tool(tool, {"filename": "order-notes.txt"})
                print(f"  {tool}('order-notes.txt') -> {result.content[0].text.strip()}")

            print()
            print("=" * 70)
            print("PATH TRAVERSAL ATTEMPT — trying to escape the sandbox")
            print("=" * 70)
            traversal_path = "../secret.txt"
            for tool in ("read_file_naive", "read_file_hardened"):
                result = await session.call_tool(tool, {"filename": traversal_path})
                print(f"  {tool}('{traversal_path}') -> {result.content[0].text.strip()}")


if __name__ == "__main__":
    asyncio.run(main())
