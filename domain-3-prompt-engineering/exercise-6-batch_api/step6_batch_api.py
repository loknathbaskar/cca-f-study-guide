"""
step6_batch_api.py — Domain 3, Concept 6: The Message Batches API.

THREE THINGS TO UNDERSTAND, DEMONSTRATED CONCRETELY:

1. COST: batch requests run at 50% of standard synchronous pricing.
   Same model, same tokens, half the cost — the trade is turnaround time.

2. LATENCY: batches are asynchronous, with up to a 24-hour processing
   window (usually much faster in practice, but NOT guaranteed fast).
   This makes batch wrong for anything user-facing/real-time, and right
   for large-volume work where nobody's waiting synchronously — end-of-day
   reprocessing, backfilling historical records, bulk classification jobs.

3. THE MULTI-TURN LIMITATION (the one people miss): a batch request is
   ONE complete message exchange, submitted and resolved independently.
   If the model responds with a tool_use block, that's it for that
   request — there's no way to submit the tool_result and continue the
   SAME conversation within the batch. Each batch item is single-shot.
   Our Step 1 coordinator's retry-and-continue pattern, or a multi-turn
   agentic loop, fundamentally cannot happen inside one batch item — you'd
   need to submit a NEW batch (or a synchronous call) to continue.

This script submits all 6 tickets from Steps 1-5 as ONE batch, using the
EXPLICIT prompt + EXTRACT_TOOL schema from Step 3, polls until complete,
and reports the results plus a cost comparison against equivalent
synchronous calls.
"""

import os
import time
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

USE_REAL_API = bool(os.environ.get("ANTHROPIC_API_KEY"))

SAMPLE_TICKETS = [
    "My order #4471 hasn't arrived in 3 weeks. I've emailed twice with no response. This is unacceptable, I want a full refund immediately.",
    "Hi, quick question — does the blue sweater run small? Thinking about sizing up.",
    "the app crashed again while I was checking out. lost my whole cart. kind of annoying but whatever, I'll just redo it",
    "URGENT: I was charged twice for order #8821. Please fix this today or I'm disputing the charge with my bank.",
    "not sure if this is the right place but my package arrived damaged, box was crushed. not a huge deal, item still works, just wanted you to know",
    "I called your support line yesterday and the rep was incredibly rude and dismissive when I asked a simple question. I want someone to actually know this happened.",
]

EXPLICIT_SYSTEM = """You are a support ticket triager. Extract structured
data from each ticket using these exact thresholds for urgency — apply
them mechanically:

- HIGH: any of — explicit dispute/chargeback threat, repeated unresolved
  contact (2+ prior attempts mentioned), same-day deadline stated by customer
- MEDIUM: a real product/service problem (damage, bug, defect) with none
  of the HIGH signals present
- LOW: questions, preferences, or issues the customer themselves frames
  as minor/non-blocking, OR no explicit signal for a category at all

For refund_requested: use null unless a refund is explicitly mentioned —
do not infer a refund request from general dissatisfaction alone."""

EXTRACT_TOOL = {
    "name": "extract_ticket_data",
    "description": "Extract structured triage data from a support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_sentiment": {
                "type": "string",
                "enum": ["very_negative", "negative", "neutral", "positive"],
            },
            "issue_category": {
                "type": "string",
                "enum": [
                    "shipping_delay", "billing_error", "product_defect",
                    "product_question", "app_bug", "other"
                ],
            },
            "issue_category_detail": {"type": ["string", "null"]},
            "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
            "refund_requested": {"type": ["boolean", "null"]},
            "requires_escalation": {"type": "boolean"},
        },
        "required": [
            "customer_sentiment", "issue_category", "issue_category_detail",
            "urgency", "refund_requested", "requires_escalation"
        ]
    }
}


def submit_batch(client):
    requests = [
        Request(
            custom_id=f"ticket-{i}",
            params=MessageCreateParamsNonStreaming(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=EXPLICIT_SYSTEM,
                messages=[{"role": "user", "content": ticket}],
                tools=[EXTRACT_TOOL],
                tool_choice={"type": "tool", "name": "extract_ticket_data"},
            ),
        )
        for i, ticket in enumerate(SAMPLE_TICKETS, 1)
    ]
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch submitted: {batch.id}")
    print(f"Initial status: {batch.processing_status}")
    return batch


def poll_until_done(client, batch_id, max_wait_seconds=600, poll_interval=15):
    print(f"\nPolling every {poll_interval}s (max wait: {max_wait_seconds}s)...")
    print("NOTE: batches can legitimately take up to 24 hours. This demo")
    print("caps waiting at a few minutes for a live walkthrough — if it")
    print("doesn't finish in that window, check back later with:")
    print(f'  client.messages.batches.retrieve("{batch_id}")\n')

    waited = 0
    while waited < max_wait_seconds:
        batch = client.messages.batches.retrieve(batch_id)
        print(f"  [{waited}s] status: {batch.processing_status}, "
              f"counts: {batch.request_counts}")
        if batch.processing_status == "ended":
            return batch
        time.sleep(poll_interval)
        waited += poll_interval

    print(f"Not finished within {max_wait_seconds}s — this is normal, not an")
    print(f"error. Check back later with the batch ID above.")
    return None


def report_results(client, batch_id):
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    for result in client.messages.batches.results(batch_id):
        print(f"\n{result.custom_id}:")
        if result.result.type == "succeeded":
            msg = result.result.message
            tool_call = next((b for b in msg.content if b.type == "tool_use"), None)
            if tool_call:
                print(f"  {tool_call.input}")
            usage = msg.usage
            print(f"  tokens: in={usage.input_tokens}, out={usage.output_tokens}")
        else:
            print(f"  FAILED: {result.result.type}")


if __name__ == "__main__":
    if not USE_REAL_API:
        print("ANTHROPIC_API_KEY not set. The Batches API has no meaningful")
        print("mock mode — batching, polling, and async status are the")
        print("entire point, and there's nothing honest to simulate about")
        print("a 24-hour processing window. Set a real key to run this step.")
        raise SystemExit(0)

    client = anthropic.Anthropic()
    batch = submit_batch(client)
    finished = poll_until_done(client, batch.id)
    if finished:
        report_results(client, batch.id)
    else:
        print(f"\nRe-run report_results(client, '{batch.id}') later once")
        print("processing_status shows 'ended'.")

    print("\n" + "=" * 70)
    print("COMPARE: look at the total cost/token usage here against Step 3's")
    print("synchronous run of the same 6 tickets. Batch pricing is 50% of")
    print("standard rates for identical model/token usage — verify the")
    print("actual discount by comparing real numbers, not just trusting")
    print("the documented rate.")
    print("=" * 70)
