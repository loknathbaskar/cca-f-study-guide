"""
http_order_server.py — Domain 4, Concept 6: StreamableHTTP transport.

Same order data/tool as Exercise 4's order_server.py, but run over
StreamableHTTP instead of stdio. Key architectural difference this
exercise demonstrates concretely: stdio spawns a NEW subprocess per
client (one server instance per client, no shared state possible across
clients) — StreamableHTTP runs ONE persistent server process that
MULTIPLE clients can connect to simultaneously over the network, sharing
the same in-memory state.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("OrderServiceHTTP", host="127.0.0.1", port=8123)

ORDERS = {
    "4471": {"status": "delayed", "customer": "Jane Smith"},
    "8821": {"status": "duplicate_charge_flagged", "customer": "Sam Lee"},
}

# Mutable counter, shared across ALL clients connecting to this ONE
# running process — this is the concrete thing stdio cannot do, since
# stdio gives every client its own separate subprocess with its own
# separate memory.
_call_count = {"total": 0}


@mcp.tool()
def get_order_status(order_id: str) -> str:
    """Get the current status of an order by its order_id."""
    _call_count["total"] += 1
    order = ORDERS.get(order_id)
    if not order:
        return f"No order found with ID {order_id}. (call #{_call_count['total']} on this server instance)"
    return f"Order {order_id}: status={order['status']}, customer={order['customer']} (call #{_call_count['total']} on this server instance)"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
