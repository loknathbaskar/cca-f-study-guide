"""
exercise3_tool_distribution.py — Domain 4, Concept 3: Distributing tools
across agents vs. giving one agent everything.

DIRECT FOLLOW-UP TO EXERCISE 1: we found tool NAME is a remarkably robust
routing signal in a clean 2-tool comparison — vague and even misleading
descriptions couldn't break it. This exercise asks the natural next
question: does that robustness hold up at SCALE, when one agent has 15
tools across 3 unrelated domains instead of 2 tools in one domain?

THE SETUP: 15 tools across 3 domains (e-commerce, HR, IT support), 5 per
domain. Two tools are a deliberate cross-domain near-collision:
  - update_payment_method (e-commerce) — update a customer's card on file
  - update_direct_deposit (HR) — update an employee's bank account for payroll
Both are fundamentally "update where my money goes" — genuinely capable
of colliding on a query like "I need to update my payment information."

TWO APPROACHES, same 6 test queries:
  A) MONOLITHIC — one agent, all 15 tools available at once, tool_choice=auto
  B) DISTRIBUTED — a lightweight router first classifies which of the 3
     domains the query belongs to (a forced choice among 3 router
     options), THEN only that domain's 5 tools are made available for
     the actual tool call — the cross-domain collision tool is never
     even a candidate at the second stage.
"""

from backend import call_claude, USE_REAL_API

# ---------- Tool definitions, 5 per domain ----------

ECOMMERCE_TOOLS = [
    {"name": "get_order_status", "description": "Get the status of a customer's order by order_id.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "cancel_order", "description": "Cancel a customer's order by order_id.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
    {"name": "issue_refund", "description": "Issue a refund for a customer's order.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}, "amount_cents": {"type": "integer"}}, "required": ["order_id", "amount_cents"]}},
    {"name": "update_payment_method", "description": "Update a customer's saved credit card on file for future purchases.",
     "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}},
    {"name": "track_shipment", "description": "Get real-time tracking info for a shipped order.",
     "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
]

HR_TOOLS = [
    {"name": "request_pto", "description": "Submit a paid time off request for an employee.",
     "input_schema": {"type": "object", "properties": {"employee_id": {"type": "string"}, "dates": {"type": "string"}}, "required": ["employee_id", "dates"]}},
    {"name": "update_direct_deposit", "description": "Update an employee's bank account information for payroll direct deposit.",
     "input_schema": {"type": "object", "properties": {"employee_id": {"type": "string"}}, "required": ["employee_id"]}},
    {"name": "get_pay_stub", "description": "Retrieve an employee's pay stub for a given pay period.",
     "input_schema": {"type": "object", "properties": {"employee_id": {"type": "string"}, "period": {"type": "string"}}, "required": ["employee_id", "period"]}},
    {"name": "enroll_benefits", "description": "Enroll an employee in a health/dental/vision benefits plan.",
     "input_schema": {"type": "object", "properties": {"employee_id": {"type": "string"}, "plan": {"type": "string"}}, "required": ["employee_id", "plan"]}},
    {"name": "update_emergency_contact", "description": "Update an employee's emergency contact information.",
     "input_schema": {"type": "object", "properties": {"employee_id": {"type": "string"}, "contact_name": {"type": "string"}}, "required": ["employee_id", "contact_name"]}},
]

IT_TOOLS = [
    {"name": "reset_password", "description": "Reset a user's company account password.",
     "input_schema": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}},
    {"name": "grant_vpn_access", "description": "Grant a user access to the company VPN.",
     "input_schema": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}},
    {"name": "report_device_lost", "description": "Report a company device (laptop, phone) as lost or stolen.",
     "input_schema": {"type": "object", "properties": {"user_id": {"type": "string"}, "device_type": {"type": "string"}}, "required": ["user_id", "device_type"]}},
    {"name": "request_software_install", "description": "Request installation of approved software on a company device.",
     "input_schema": {"type": "object", "properties": {"user_id": {"type": "string"}, "software_name": {"type": "string"}}, "required": ["user_id", "software_name"]}},
    {"name": "unlock_account", "description": "Unlock a user account that's been locked due to failed login attempts.",
     "input_schema": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}},
]

ALL_TOOLS = ECOMMERCE_TOOLS + HR_TOOLS + IT_TOOLS

ROUTER_TOOLS = [
    {"name": "route_to_ecommerce", "description": "Route to the e-commerce/orders specialist for anything about customer orders, shipping, refunds, or a customer's payment method on file for purchases.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "route_to_hr", "description": "Route to the HR specialist for anything about employee pay, payroll direct deposit, benefits, PTO, or employee records.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "route_to_it", "description": "Route to the IT support specialist for anything about passwords, accounts, VPN, or company devices.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
]

DOMAIN_TOOLS = {"route_to_ecommerce": ECOMMERCE_TOOLS, "route_to_hr": HR_TOOLS, "route_to_it": IT_TOOLS}

TEST_QUERIES = [
    # NOTE: every tool's schema REQUIRES an id field (employee_id, user_id,
    # customer_id). Earlier queries never supplied one, which likely
    # caused Claude to correctly withhold a tool call (it can't fill a
    # required field it wasn't given) and ask a clarifying question in
    # text instead — a reasonable behavior we were mislabeling as a
    # routing failure. Fixed by supplying a plausible ID in every query,
    # so this test isolates ROUTING specifically, not parameter-completeness.
    ("What's the status of order #4471?", "get_order_status"),
    ("I'm employee EMP-1001 and need to submit a PTO request for next Friday", "request_pto"),
    ("I'm user U-2002, my laptop was stolen and I need to report it", "report_device_lost"),
    ("I'm customer C-3003 and need to update my payment information", "update_payment_method"),
    ("I'm employee EMP-1001 and need to update where my paycheck gets deposited", "update_direct_deposit"),
    ("I'm user U-2002 and I'm locked out of my account, can you unlock it?", "unlock_account"),
]


def run_monolithic():
    print("=" * 70)
    print("APPROACH A: MONOLITHIC — one agent, all 15 tools at once")
    print("=" * 70)
    correct = 0
    for query, expected in TEST_QUERIES:
        result = call_claude(
            "You are a company assistant with access to e-commerce, HR, and IT tools.",
            query, tools=ALL_TOOLS,
        )
        tool_call = next((b for b in result.content if b.type == "tool_use"), None)
        if tool_call:
            called = tool_call.name
        else:
            called = "NO TOOL"
            text = "".join(b.text for b in result.content if b.type == "text")
            print(f"      (no tool called — text response was: \"{text[:150]}\")")
        is_correct = called == expected
        correct += is_correct
        print(f"  {'✓' if is_correct else '✗'} \"{query}\" -> expected {expected}, got {called}")
    print(f"\n  Score: {correct}/{len(TEST_QUERIES)}\n")
    return correct


def run_distributed():
    print("=" * 70)
    print("APPROACH B: DISTRIBUTED — router picks a domain first, then only")
    print("that domain's 5 tools are available for the real call")
    print("=" * 70)
    correct = 0
    for query, expected in TEST_QUERIES:
        route_result = call_claude(
            "You are a router. Determine which specialist should handle this request.",
            query, tools=ROUTER_TOOLS,
        )
        route_call = next((b for b in route_result.content if b.type == "tool_use"), None)
        if not route_call:
            print(f"  ✗ \"{query}\" -> router called no tool")
            continue

        domain_tools = DOMAIN_TOOLS[route_call.name]
        final_result = call_claude(
            "You are a specialist assistant for this domain only.",
            query, tools=domain_tools,
        )
        tool_call = next((b for b in final_result.content if b.type == "tool_use"), None)
        if tool_call:
            called = tool_call.name
        else:
            called = "NO TOOL"
            text = "".join(b.text for b in final_result.content if b.type == "text")
            print(f"      (no tool called — text response was: \"{text[:150]}\")")
        is_correct = called == expected
        correct += is_correct
        print(f"  {'✓' if is_correct else '✗'} \"{query}\" -> routed to {route_call.name}, expected {expected}, got {called}")
    print(f"\n  Score: {correct}/{len(TEST_QUERIES)}\n")
    return correct


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK'} mode\n")
    mono_score = run_monolithic()
    dist_score = run_distributed()

    print("=" * 70)
    print(f"MONOLITHIC (15 tools, 1 call): {mono_score}/6")
    print(f"DISTRIBUTED (router + 5 tools, 2 calls): {dist_score}/6")
    print("Did distribution improve accuracy specifically on the two")
    print("cross-domain 'payment/deposit' collision queries — at the cost")
    print("of double the API calls?")
    print("=" * 70)
