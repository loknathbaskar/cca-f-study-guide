"""
annotation_trust_client.py — naive (trusts readOnlyHint) vs hardened
(independently verifies actual behavior, never trusts self-reported
metadata) approaches to the same malicious/buggy tool.
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def naive_host(session: ClientSession):
    print("=" * 70)
    print("NAIVE HOST — trusts readOnlyHint, skips confirmation/logging")
    print("for any tool declaring itself read-only")
    print("=" * 70)

    tools = await session.list_tools()
    check_tool = next(t for t in tools.tools if t.name == "check_order_status")
    is_declared_readonly = check_tool.annotations and check_tool.annotations.readOnlyHint
    print(f"  Tool declares readOnlyHint={is_declared_readonly} -> "
          f"{'skipping confirmation, calling directly' if is_declared_readonly else 'would confirm first'}")

    result = await session.call_tool("check_order_status", {"order_id": "4471"})
    print(f"  Result: {result.content[0].text}")

    verify = await session.call_tool("list_orders", {})
    print(f"  Orders remaining after a supposedly 'read-only' call: {verify.content[0].text}")
    print("  >>> The order was DELETED despite the tool claiming readOnlyHint=True <<<")


async def hardened_host(session: ClientSession):
    print("\n" + "=" * 70)
    print("HARDENED HOST — never trusts the annotation; independently")
    print("verifies actual behavior by snapshotting state before/after")
    print("=" * 70)

    before = await session.call_tool("list_orders", {})
    before_state = before.content[0].text
    print(f"  State BEFORE call: {before_state}")

    tools = await session.list_tools()
    check_tool = next(t for t in tools.tools if t.name == "check_order_status")
    print(f"  Tool declares readOnlyHint={check_tool.annotations.readOnlyHint if check_tool.annotations else None}"
          f" — NOTED, but not trusted as a guarantee")

    result = await session.call_tool("check_order_status", {"order_id": "4471"})
    print(f"  Result: {result.content[0].text}")

    after = await session.call_tool("list_orders", {})
    after_state = after.content[0].text
    print(f"  State AFTER call: {after_state}")

    if before_state != after_state:
        print("  >>> MISMATCH DETECTED: this tool mutated state despite claiming")
        print("      readOnlyHint=True. Flagging for review — this tool's")
        print("      self-reported annotations cannot be trusted going forward,")
        print("      and should require explicit confirmation on every future call")
        print("      regardless of what it claims about itself. <<<")
    else:
        print("  State unchanged — annotation appears accurate this time.")


async def main():
    # NOTE: need fresh server state for each demo (the first call already
    # deleted order 4471), so we spawn a new server subprocess per demo.
    for demo_fn in (naive_host, hardened_host):
        params = StdioServerParameters(command=sys.executable, args=["annotation_trust_server.py"])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await demo_fn(session)


if __name__ == "__main__":
    asyncio.run(main())
