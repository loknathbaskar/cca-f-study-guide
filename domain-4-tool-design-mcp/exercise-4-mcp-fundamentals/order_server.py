"""
order_server.py — Domain 4, Concept 4: A real MCP server, demonstrating
all three MCP primitives.

This is a genuine, runnable MCP server (using FastMCP, now part of the
official `mcp` SDK) — not a simulation. It exposes:

  1. A TOOL — get_order_status(order_id): has a clear invocation, takes
     parameters, returns a result. Tools are for ACTIONS/QUERIES the
     model explicitly decides to call.

  2. A RESOURCE — orders://all: read-only, URI-addressable data the
     client can fetch WITHOUT the model deciding to "call" anything —
     more like a file the host can pull in as context proactively.

  3. A PROMPT — order_summary_prompt(order_id): a reusable, parameterized
     template the HOST application can surface (e.g. as a slash command),
     not something the model decides to invoke mid-conversation the way
     it does a tool.

RULE OF THUMB (from current best practice): if it has side effects or
is explicitly invoked for an action, it's a Tool. If it's read-only data
pulled in as context, it's a Resource. If it's a reusable, parameterized
message template surfaced by the host, it's a Prompt.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("OrderService")

# Fake order data — reusing the customer-service theme from Domains 1-4
ORDERS = {
    "4471": {"status": "delayed", "customer": "Jane Smith", "items": ["Blue Sweater"], "days_late": 21},
    "8821": {"status": "duplicate_charge_flagged", "customer": "Sam Lee", "items": ["Wireless Mouse"], "days_late": 0},
    "9981": {"status": "shipped", "customer": "Maria Lopez", "items": ["Desk Lamp"], "days_late": 0},
}


@mcp.tool()
def get_order_status(order_id: str) -> str:
    """Get the current status of an order by its order_id."""
    order = ORDERS.get(order_id)
    if not order:
        return f"No order found with ID {order_id}."
    return f"Order {order_id}: status={order['status']}, customer={order['customer']}, items={order['items']}"


@mcp.resource("orders://all")
def all_orders() -> str:
    """A read-only snapshot of every order in the system, as context."""
    lines = [f"{oid}: {data['status']} ({data['customer']})" for oid, data in ORDERS.items()]
    return "\n".join(lines)


@mcp.prompt()
def order_summary_prompt(order_id: str) -> str:
    """A reusable prompt template for summarizing a specific order for a customer."""
    order = ORDERS.get(order_id, {})
    return (
        f"Write a brief, friendly customer-facing summary of order {order_id}. "
        f"Status: {order.get('status', 'unknown')}. "
        f"Do not mention internal system field names — translate them into "
        f"plain language a customer would understand."
    )


if __name__ == "__main__":
    mcp.run()
