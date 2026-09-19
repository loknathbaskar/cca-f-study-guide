"""
exercise2_prompt_caching.py — Domain 5, Concept 2: Prompt caching — real
cache write, cache hit, and a deliberately broken cache, with real usage
data and real cost computed from confirmed current pricing.

THREE REAL CALLS, same large static system prompt (a product policy doc,
long enough to safely exceed the caching minimum token threshold):

  CALL 1 — first call with cache_control on the system prompt. Expect a
  CACHE WRITE (usage.cache_creation_input_tokens > 0), billed at a
  premium (~1.25x base input price) since this is the first time this
  content is cached.

  CALL 2 — identical system prompt, called again shortly after. Expect a
  CACHE HIT (usage.cache_read_input_tokens > 0), billed at a steep
  discount (~0.1x base input price) — this is the actual cost savings
  prompt caching exists for.

  CALL 3 — THE ANTI-PATTERN TEST: same system prompt, but with a live
  timestamp string injected into it (something a real system might do
  without realizing the consequence). Prediction: this breaks the cache
  entirely, since the cached prefix must be byte-identical up to the
  cache_control marker — even a single changed character invalidates it.
  Expect this call to show a fresh CACHE WRITE again, not a hit, proving
  the "timestamps silently kill your cache hit rate" claim directly
  rather than just citing it.
"""

import os
from datetime import datetime

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("This exercise requires ANTHROPIC_API_KEY — cache behavior and")
    print("real usage/cost data are exactly what's being tested, no")
    print("meaningful mock exists for actual cache state.")
    raise SystemExit(0)

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# A long, static "product policy" system prompt — the FIRST version of
# this document was only ~470 tokens, well under the 1024-token minimum
# required for Claude models to cache anything at all (confirmed by all
# three calls showing cache_creation_input_tokens=0 AND
# cache_read_input_tokens=0 — caching never engaged, not even a write).
# This version is substantially expanded to safely clear that threshold.
BASE_POLICY_DOC = """
You are a customer support assistant for Acme Outdoor Gear. You have
access to the following complete policy documentation:

RETURN POLICY: Items may be returned within 30 days of purchase with
original receipt. Items must be unused and in original packaging.
Footwear must not show signs of outdoor wear. Custom or personalized
items are final sale. Sale items marked "final sale" cannot be returned.
Electronics (GPS devices, headlamps with electronics) have a 15-day
return window instead of 30 due to rapid depreciation. Returns initiated
after 30 days but within 45 days may be accepted at store manager
discretion for store credit only, minus a 15% restocking fee. Returns
of items purchased using a promotional discount code will be refunded
at the discounted price actually paid, not the item's regular list
price. If an item was part of a buy-one-get-one promotion and only one
item is returned, the discount applied to the promotion will be
recalculated and deducted from the refund amount.

SHIPPING POLICY: Standard shipping takes 5-7 business days. Expedited
shipping (2-3 business days) is available for an additional $12.99.
Overnight shipping is available for orders placed before 2pm EST for an
additional $34.99. Free standard shipping applies to orders over $75.
International shipping is available to Canada and Mexico only, taking
10-14 business days, with customs fees the responsibility of the
recipient. Orders shipping to Alaska, Hawaii, and US territories add
2-3 additional business days to all shipping methods and are not
eligible for the free-shipping-over-$75 threshold due to elevated
carrier costs. Split shipments (when items ship from different
warehouses) do not incur additional shipping charges beyond what was
originally quoted, even if this results in multiple packages arriving
on different days. Signature-required delivery is automatically applied
to orders over $300 and cannot be waived by the customer for security
reasons.

WARRANTY POLICY: All hard goods (tents, backpacks, sleeping bags) carry
a lifetime warranty against manufacturing defects, not general wear and
tear. Footwear carries a 1-year warranty. Electronics carry a
manufacturer's standard warranty (typically 1-2 years depending on
brand) since these are third-party manufactured products we resell.
Warranty claims require proof of purchase and, for hard goods claims
made more than 2 years after purchase, photographic evidence of the
defect prior to issuing a replacement. Warranty coverage is void if the
product has been modified from its original manufactured state,
including aftermarket waterproofing treatments, third-party repairs, or
structural modifications. Products purchased through unauthorized
third-party resellers (not our website, retail stores, or authorized
partners) are not eligible for warranty service regardless of proof of
purchase.

LOYALTY PROGRAM: Members earn 1 point per dollar spent. 100 points =
$5 off a future purchase. Points expire after 24 months of account
inactivity. Birthday month members receive a 15% discount code
automatically. Members receive early access to sale events 24 hours
before the general public. Points earned from a purchase are not
credited to the account until the return window for that purchase has
closed (30 days), to prevent point accumulation from items that are
later returned. Referral bonuses (500 points per successful referral)
are credited only after the referred customer's first order ships and
passes the standard return window without being returned in full.

PRICE MATCH POLICY: We match any authorized retailer's price within 14
days of purchase, excluding clearance, flash sales, and Black Friday/
Cyber Monday pricing. Price match requests must include a link or
screenshot of the competitor's listing showing the item in stock at
the lower price. Price matches are limited to identical SKUs, sizes,
and colors — a similar item from a different product line does not
qualify even if functionally comparable. Price match refunds are issued
as store credit, not a refund to the original payment method, unless
the customer explicitly requests otherwise and the original payment
method is still valid.

DAMAGED ITEM POLICY: Items damaged in transit must be reported within
48 hours of delivery with photos of the damage and packaging. We will
issue a replacement or full refund at the customer's preference, and
cover return shipping costs for the damaged item. If the same item is
reported damaged in transit more than twice within a 12-month period
for the same customer, the third and subsequent claims require a
signed affidavit before a replacement or refund is issued, as a fraud
prevention measure.

GIFT CARD POLICY: Gift cards do not expire and carry no maintenance
fees. Gift cards cannot be redeemed for cash except where required by
state law. Lost or stolen gift cards can be deactivated and reissued
only if the original purchase receipt or order confirmation email is
provided. Gift card balances cannot be combined or transferred between
accounts.

PRICE ADJUSTMENT POLICY: If an item's price drops within 7 days of a
customer's purchase, we will issue a one-time price adjustment refund
for the difference, provided the item was not purchased using any
promotional or discount code. Price adjustments are not available on
clearance items, which are priced to sell through and not eligible for
further reductions.
""".strip()


def make_call(system_content: str, user_message: str, label: str):
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": system_content,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )
    usage = response.usage
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    print(f"--- {label} ---")
    print(f"  input_tokens={usage.input_tokens}, "
          f"cache_creation_input_tokens={cache_write}, "
          f"cache_read_input_tokens={cache_read}")
    if cache_read > 0:
        print(f"  >>> CACHE HIT — {cache_read} tokens read from cache <<<")
    elif cache_write > 0:
        print(f"  >>> CACHE WRITE — {cache_write} tokens written to cache (first time or cache miss) <<<")
    return usage


if __name__ == "__main__":
    # Rough sanity check BEFORE spending any API calls: Claude models
    # need >=1024 tokens in the cacheable prefix or caching won't engage
    # at all (this is exactly what broke the first version of this
    # script — see the bugs log). ~4 chars/token is a rough English-text
    # estimate, not exact, but enough to catch an obviously-too-short
    # document before wasting a call finding out the hard way.
    rough_token_estimate = len(BASE_POLICY_DOC) / 4
    print(f"Policy doc: {len(BASE_POLICY_DOC)} chars, ~{rough_token_estimate:.0f} tokens (rough estimate)")
    if rough_token_estimate < 1024:
        print("WARNING: this is likely under the 1024-token minimum for caching to engage at all.")
    print()

    print("=" * 70)
    print("CALL 1 — first call, expect a CACHE WRITE")
    print("=" * 70)
    usage1 = make_call(BASE_POLICY_DOC, "What's your return policy on footwear?", "Call 1")

    print()
    print("=" * 70)
    print("CALL 2 — identical system prompt, expect a CACHE HIT")
    print("=" * 70)
    usage2 = make_call(BASE_POLICY_DOC, "What's your warranty policy on tents?", "Call 2")

    print()
    print("=" * 70)
    print("CALL 3 — THE ANTI-PATTERN: same policy doc, but with a live")
    print("timestamp injected. Does this break the cache?")
    print("=" * 70)
    poisoned_doc = f"Current time: {datetime.now().isoformat()}\n\n{BASE_POLICY_DOC}"
    usage3 = make_call(poisoned_doc, "What's your shipping policy for international orders?", "Call 3 (timestamp injected)")

    print()
    print("=" * 70)
    print("COST COMPARISON (Sonnet 4.6 rates: base $3/MTok, cache write")
    print("~1.25x base, cache read ~0.1x base)")
    print("=" * 70)
    BASE_RATE = 3.0
    WRITE_RATE = 3.75
    READ_RATE = 0.30
    for label, usage in [("Call 1", usage1), ("Call 2", usage2), ("Call 3", usage3)]:
        cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        base_tokens = usage.input_tokens
        cost = (base_tokens / 1_000_000 * BASE_RATE) + \
               (cache_write / 1_000_000 * WRITE_RATE) + \
               (cache_read / 1_000_000 * READ_RATE)
        print(f"  {label}: ${cost:.6f}")
    print()
    print("Did Call 2 cost dramatically less than Call 1 (the cache hit")
    print("discount)? Did Call 3 cost roughly the SAME as Call 1 (proving")
    print("the timestamp really did break the cache and force a full")
    print("re-write), rather than benefiting from the cache at all?")
