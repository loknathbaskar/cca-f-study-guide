"""
exercise1_tool_description_routing.py — Domain 4, Concept 1: Tool
descriptions as routing mechanisms.

THE CORE IDEA: Claude picks which tool to call based ONLY on the tool's
name, description, and schema — it never sees the implementation. This
means tool descriptions ARE the routing logic. Ambiguous or overlapping
descriptions between near-duplicate tools cause misrouting, exactly like
Domain 1's search_agent/analyze_agent bug — except this time the
"agents" are real tools passed in one API call, and we're testing
Claude's own tool selection directly, not a hand-written mock router.

THE SETUP: 5 customer-service tools. Two of them are a deliberate
near-duplicate pair:
  - search_orders: meant for system-wide order search (across ALL
    customers, filtered by criteria)
  - get_customer_orders: meant for a SINGLE customer's order history

In the AMBIGUOUS version, both descriptions are vague enough to overlap.
In the CLEAR version, each description explicitly states its scope and
explicitly references the other tool to disambiguate ("use X instead if
Y").

5 test queries, 2 of which specifically probe the ambiguous pair.
"""

from backend import call_claude, USE_REAL_API

# ---------- Two tool sets: same 5 tools, different description quality ----------

def build_tools(mode: str):
    """mode: 'ambiguous', 'clear', or 'misleading'"""
    if mode == "ambiguous":
        search_orders_desc = "Search for orders."
        get_customer_orders_desc = "Get orders for a customer."
        search_orders_params = {"param1": {"type": ["string", "null"]}, "param2": {"type": ["string", "null"]}}
        get_customer_orders_params = {"param1": {"type": "string"}}
    elif mode == "misleading":
        # Swapped/collision descriptions — each one uses language that
        # actually belongs to the OTHER tool, mirroring Domain 1's
        # search_agent/analyze_agent bug (where analyze_agent's own
        # prompt happened to contain the word "search"). Names and
        # schemas stay fully informative — this isolates whether
        # MISLEADING description text can override otherwise-clear
        # signals, a different and more realistic failure mode than mere
        # vagueness.
        search_orders_desc = (
            "Retrieve a specific customer's order records from their "
            "account history."
        )
        get_customer_orders_desc = (
            "Search and filter order records across the entire database "
            "by criteria such as status or date."
        )
        search_orders_params = {"status_filter": {"type": ["string", "null"]}, "date_range": {"type": ["string", "null"]}}
        get_customer_orders_params = {"customer_id": {"type": "string"}}
    else:  # clear
        search_orders_desc = (
            "Search across ALL orders in the entire system, filtered by "
            "criteria like status, date range, or product — NOT scoped to "
            "a single customer. If you already know which customer and "
            "want only their orders, use get_customer_orders instead."
        )
        get_customer_orders_desc = (
            "Get the complete order history for ONE specific customer, "
            "given their customer_id. Use this when the request is about "
            "a particular customer's orders. Use search_orders instead if "
            "the request is a system-wide filter not tied to one customer."
        )
        search_orders_params = {"status_filter": {"type": ["string", "null"]}, "date_range": {"type": ["string", "null"]}}
        get_customer_orders_params = {"customer_id": {"type": "string"}}

    return [
        {
            "name": "search_customer",
            "description": "Search for a customer by name or email to find their customer_id.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        },
        {
            "name": "get_order_status",
            "description": "Get the current status of a single, specific order by its order_id.",
            "input_schema": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"]
            }
        },
        {
            "name": "search_orders",
            "description": search_orders_desc,
            "input_schema": {
                "type": "object",
                "properties": search_orders_params,
                "required": list(search_orders_params.keys())
            }
        },
        {
            "name": "get_customer_orders",
            "description": get_customer_orders_desc,
            "input_schema": {
                "type": "object",
                "properties": get_customer_orders_params,
                "required": list(get_customer_orders_params.keys())
            }
        },
        {
            "name": "update_order",
            "description": "Update a field (e.g. shipping address, quantity) on a single existing order by order_id.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "field": {"type": "string"},
                    "new_value": {"type": "string"},
                },
                "required": ["order_id", "field", "new_value"]
            }
        },
    ]


SYSTEM = "You are a customer service assistant. Use the available tools to help with requests."

TEST_QUERIES = [
    # (query, expected_tool, why)
    # NOTE: these queries are deliberately NEUTRAL about scope — no "across
    # the store" or "placed by customer" language that would let the model
    # disambiguate from the query alone. This forces reliance on the TOOL
    # DESCRIPTIONS themselves to route correctly, which is the actual thing
    # this exercise is trying to isolate. (An earlier version of these
    # queries contained strong scope language of their own, meaning both
    # AMBIGUOUS and CLEAR description sets scored 5/5 — the query wording
    # was doing all the disambiguating work, not the tool descriptions.
    # Fixed by removing that language so descriptions actually have to
    # carry the routing decision.)
    ("Pull up orders for 12345", "get_customer_orders",
     "12345 reads as a customer_id in context, but nothing marks this as system-wide vs. single-customer explicitly"),
    ("I need to see orders with a delayed status", "search_orders",
     "no customer mentioned at all, but also no explicit 'across the store' signal — genuinely ambiguous without relying on the tool descriptions"),
    ("What's the status of order #9981?", "get_order_status", "unambiguous single-order lookup"),
    ("Look up the customer named Maria Lopez", "search_customer", "unambiguous customer lookup"),
    ("Change the shipping address on order #4471 to 123 Main St", "update_order", "unambiguous update"),
]


def run_test(mode: str):
    labels = {
        "ambiguous": "AMBIGUOUS descriptions (vague, uninformative)",
        "clear": "CLEAR, disambiguated descriptions",
        "misleading": "MISLEADING descriptions (swapped/collision, but names+schemas informative)",
    }
    print("=" * 70)
    print(labels[mode])
    print("=" * 70)
    tools = build_tools(mode)
    correct = 0
    for query, expected, why in TEST_QUERIES:
        result = call_claude(SYSTEM, query, tools=tools, tool_choice={"type": "auto"})
        tool_call = next((b for b in result.content if b.type == "tool_use"), None)
        called = tool_call.name if tool_call else "NO TOOL CALLED"
        is_correct = called == expected
        correct += is_correct
        marker = "✓" if is_correct else "✗"
        print(f"  {marker} \"{query}\"")
        print(f"      expected: {expected} ({why})")
        print(f"      got:      {called}")
    print(f"\n  Score: {correct}/{len(TEST_QUERIES)}")
    print()
    return correct


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")
    ambiguous_score = run_test("ambiguous")
    clear_score = run_test("clear")
    misleading_score = run_test("misleading")

    print("=" * 70)
    print(f"AMBIGUOUS: {ambiguous_score}/5   |   CLEAR: {clear_score}/5   |   MISLEADING: {misleading_score}/5")
    print("Does MISLEADING (swapped keywords, but informative names/schemas)")
    print("cause failures that vague-but-neutral descriptions didn't?")
    print("=" * 70)
