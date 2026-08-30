"""
exercise2_error_idempotency.py — Domain 4, Concept 2: Tool error handling
— structured error responses, idempotency, and partial success.

THREE SEPARATE TESTS, each requiring a real multi-turn tool conversation
(Claude calls a tool -> we return a crafted tool_result -> Claude reacts
-> we observe what it does next). This is a different harness than
Domain 3's single-shot tool_use calls.

TEST A — Structured errors change behavior appropriately: a tool returns
one of three structured error shapes (not_found / rate_limited+retryable
/ permission_denied+not-retryable). Does Claude's next action differ
correctly per error — retry only the retryable one, not retry the
permission error, report not_found accurately?

TEST B — Partial success is preserved, not flattened: a batch
cancel_orders call returns 3 succeeded + 2 failed (different reasons per
failure). Does Claude's final summary to the user accurately reflect the
partial nature — specific order IDs and reasons — or does it round up to
"all cancelled" / down to "failed"?

TEST C — Idempotency key reuse on retry: a charge_customer call times out
(simulated). Claude is told to retry. Does it reuse the SAME
idempotency_key from the first attempt, or generate a new one? Reusing
the same key is what actually prevents a duplicate charge in a real
payment system — a new key on retry defeats the entire purpose of having
one.
"""

import json
import uuid
from backend import USE_REAL_API

if USE_REAL_API:
    import anthropic
    _client = anthropic.Anthropic()

MODEL = "claude-sonnet-4-6"

CANCEL_ORDERS_TOOL = {
    "name": "cancel_orders",
    "description": "Cancel one or more orders by order_id. May partially succeed — some orders may be cancellable while others are not.",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_ids": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["order_ids"]
    }
}

CHARGE_CUSTOMER_TOOL = {
    "name": "charge_customer",
    "description": "Charge a customer's saved payment method. Requires an idempotency_key — reusing the SAME key on a retry of the same logical charge prevents duplicate charges if the first attempt's result was unclear (e.g. a timeout).",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "amount_cents": {"type": "integer"},
            "idempotency_key": {"type": "string", "description": "A unique key for this logical charge attempt. MUST be reused on retry of the same charge."},
        },
        "required": ["customer_id", "amount_cents", "idempotency_key"]
    }
}


def run_conversation(system, user_message, tools, tool_executor, max_turns=4, label=""):
    """Runs a real (or mock) multi-turn tool conversation, executing tool
    calls locally via tool_executor(name, input) -> structured result dict."""
    print(f"\n--- {label} ---")
    messages = [{"role": "user", "content": user_message}]
    tool_call_log = []

    for turn in range(max_turns):
        if USE_REAL_API:
            response = _client.messages.create(
                model=MODEL, max_tokens=1024, system=system,
                messages=messages, tools=tools,
            )
        else:
            response = tool_executor.mock_claude_turn(messages, tools)

        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            final_text = "".join(b.text for b in response.content if b.type == "text")
            print(f"  FINAL RESPONSE: {final_text}")
            return final_text, tool_call_log

        tool_results = []
        for tu in tool_uses:
            tool_call_log.append((tu.name, tu.input))
            print(f"  [turn {turn+1}] Claude called {tu.name}({tu.input})")
            result = tool_executor(tu.name, tu.input)
            print(f"  [turn {turn+1}] Tool returned: {result}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(result),
            })
        messages.append({"role": "user", "content": tool_results})

    print("  (max turns reached without a final text response)")
    return None, tool_call_log


# ---------- TEST A: structured errors ----------

def test_a_executor(name, input_):
    order_id = input_.get("order_id", "")
    if order_id == "ERR_NOTFOUND":
        return {"error": {"category": "not_found", "isRetryable": False,
                           "message": f"Order {order_id} does not exist."}}
    if order_id == "ERR_RATELIMIT":
        return {"error": {"category": "rate_limited", "isRetryable": True,
                           "message": "Rate limit exceeded. Retry after backoff."}}
    if order_id == "ERR_PERMISSION":
        return {"error": {"category": "permission_denied", "isRetryable": False,
                           "message": "You do not have permission to cancel this order."}}
    return {"success": True, "order_id": order_id, "status": "cancelled"}


def run_test_a():
    print("=" * 70)
    print("TEST A: Structured errors — does behavior differ correctly per error type?")
    print("=" * 70)
    single_order_tool = {
        "name": "cancel_order",
        "description": "Cancel a single order by order_id.",
        "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}
    }
    for order_id, scenario in [("ERR_NOTFOUND", "not found, non-retryable"),
                                 ("ERR_RATELIMIT", "rate limited, RETRYABLE"),
                                 ("ERR_PERMISSION", "permission denied, non-retryable")]:
        run_conversation(
            "You are a support assistant with access to order cancellation tools.",
            f"Please cancel order {order_id} for the customer.",
            [single_order_tool], test_a_executor,
            label=f"Scenario: {scenario}",
        )


# ---------- TEST B: partial success ----------

def test_b_executor(name, input_):
    order_ids = input_["order_ids"]
    results = []
    for oid in order_ids:
        if oid in ("ORD-2", "ORD-4"):
            reason = "already shipped" if oid == "ORD-2" else "order not found"
            results.append({"order_id": oid, "success": False, "reason": reason})
        else:
            results.append({"order_id": oid, "success": True})
    return {"results": results}


def run_test_b():
    print("=" * 70)
    print("TEST B: Partial success — does the final summary preserve specifics?")
    print("(3 succeed, 2 fail for DIFFERENT reasons — check the final text)")
    print("=" * 70)
    run_conversation(
        "You are a support assistant with access to order cancellation tools.",
        "Please cancel these orders: ORD-1, ORD-2, ORD-3, ORD-4, ORD-5",
        [CANCEL_ORDERS_TOOL], test_b_executor,
        label="Batch cancel with mixed results",
    )


# ---------- TEST C: idempotency key reuse ----------

_charge_attempts = {"count": 0, "keys_seen": []}

def test_c_executor(name, input_):
    _charge_attempts["count"] += 1
    _charge_attempts["keys_seen"].append(input_.get("idempotency_key"))
    if _charge_attempts["count"] == 1:
        return {"error": {"category": "timeout", "isRetryable": True,
                           "message": "Request timed out — charge status unknown, safe to retry with the SAME idempotency_key."}}
    return {"success": True, "charge_id": "ch_abc123", "amount_cents": input_.get("amount_cents")}


def run_test_c():
    print("=" * 70)
    print("TEST C: Idempotency — does retry reuse the SAME key?")
    print("=" * 70)
    _, log = run_conversation(
        "You are a billing assistant with access to a charge_customer tool. "
        "If a charge times out, it is safe to retry — but you MUST reuse the "
        "exact same idempotency_key on retry, never generate a new one, or "
        "the customer may be charged twice.",
        "Charge customer CUST-999 for 2500 cents ($25.00).",
        [CHARGE_CUSTOMER_TOOL], test_c_executor,
        label="Charge with a simulated timeout on first attempt",
    )
    keys = [inp.get("idempotency_key") for n, inp in log if n == "charge_customer"]
    print(f"\n  Idempotency keys used across attempts: {keys}")
    if len(keys) >= 2:
        if keys[0] == keys[1]:
            print("  >>> CORRECT: same key reused on retry <<<")
        else:
            print("  >>> BUG: a NEW key was generated on retry — this would risk a duplicate charge in a real system <<<")


if __name__ == "__main__":
    print(f"Running in {'REAL API' if USE_REAL_API else 'MOCK — see note below'} mode\n")
    if not USE_REAL_API:
        print("NOTE: multi-turn tool conversations have no meaningful mock in")
        print("this exercise — simulating realistic multi-turn model behavior")
        print("by hand would just be scripting the expected answer. Set a real")
        print("ANTHROPIC_API_KEY to run this one.\n")
        raise SystemExit(0)

    run_test_a()
    run_test_b()
    run_test_c()
