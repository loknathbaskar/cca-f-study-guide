# Domain 5, Exercise 1: Context Compaction — Prose Summary vs. Structured Extraction

## What this demonstrates

A specific, falsifiable claim from the exam guide's own language:
*"Structured records, targeted retrieval, and explicit unresolved fields
are often safer than replacing an entire history with an unverified
prose summary."* Let's actually test it — including its likely
**weakness**, not just confirm it uncritically.

**The setup**: an 8-turn, fact-dense customer support conversation
containing:
- Multiple order IDs and dollar amounts
- A mid-conversation **promise** (a $12.99 fee waiver) — exactly the
  kind of "unresolved commitment" the exam language calls out
- One deliberately **incidental** detail unrelated to the main issue
  (the customer mentions an upcoming address change) — something a
  reasonable support-ticket schema author might not think to add a
  field for

**Two compaction methods, same conversation**: a free-text prose
summary, and a structured JSON extraction (order IDs, promises with
amount/fulfillment/timeline sub-fields, unresolved items) — the
structured schema has NO field for the incidental address-change detail.

**Then**: using ONLY the compacted output (not the original
conversation) as context, two follow-up questions:
- **Q1 (in-schema)**: the exact fee waiver amount and how it's returned
- **Q2 (out-of-schema)**: whether the customer mentioned their living
  situation changing

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 exercise1_compaction_strategies.py
```

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — ran correctly on the first attempt. The result refined the hypothesis rather than confirming it outright, documented below. | — | — |

## Real results

**Q1 (in-schema fact) — a TIE, not a structured win.** Both PROSE and
STRUCTURED answered with identical precision: $12.99, refund to original
payment method, 3-5 business days. **The hypothesis that prose risks
drifting or rounding a specific number was NOT confirmed** — prose
preserved it exactly. Worth being honest that this part of the
prediction was wrong.

**Q2 (out-of-schema, incidental fact) — a stark, total loss for
structured, confirmed cleanly.** PROSE fully and correctly recalled the
address-change detail. STRUCTURED didn't answer vaguely or hedge — it
explicitly stated *"the context provided does not contain any
information about the customer mentioning a change in their living
situation."* The fact wasn't degraded, it was **completely and silently
absent**, because no field existed to hold it — the extraction step
itself discarded it before the follow-up question was ever asked.

## Corrected conclusion

The real, evidenced lesson is sharper than "structured beats prose for
compaction" — that framing isn't well supported by this data, since
prose matched structured exactly on the in-schema fact. The actual
finding: **structured extraction's real advantage is guaranteed
retrievability for whatever fields you defined, at the total cost of
anything you didn't think to include a field for.** Prose has no such
hard ceiling (it retained the incidental detail for free) but also no
such floor guarantee (nothing forces it to reliably retain any
particular fact, even though it happened to here).

**This generalizes Domain 3's nullable-field and `"other"`-escape-hatch
findings to compaction specifically**: a rigid schema is exactly as good
as its author's foresight. The practical implication for real compaction
system design isn't "always use structured extraction" — it's a hybrid:
structured fields for facts you know matter (financial commitments, IDs,
deadlines), PLUS a free-text "anything else notable" field, so the
schema doesn't have a hard ceiling on what it can retain. Worth testing
that hybrid directly as a natural follow-up.

## Design principle worth defending in an exam-style answer

**Why would structured extraction lose the incidental fact, when it's
supposedly the "safer" compaction method?** Structure is only as
complete as the schema author's anticipation of what matters. A prose
summary has no such ceiling — it can capture anything the summarizing
model judges worth keeping, including things nobody thought to add a
field for. This is the real, honest trade-off: structure buys you
guaranteed retrievability on the fields you defined, at the cost of
anything outside those fields being silently dropped.

**Why did prose NOT lose precision on the specific dollar figure, contrary
to the initial hypothesis?** Worth taking this at face value rather than
explaining it away — a single test run showing prose can preserve a
specific number accurately doesn't mean it's reliable at scale or across
many compaction cycles (repeated summarization of summaries is a
different, likely riskier scenario this single test didn't cover). The
honest takeaway is "not confirmed to be a risk here," not "confirmed to
never be a risk."

## Next step
Exercise 2 — prompt caching: real cache hit/miss behavior and cost impact.
