# Domain 3, Exercise 1 — Step 1: Explicit Criteria vs. Vague Instructions

## What this demonstrates

Two prompts, same 5 support tickets, run twice each:
- **Vague**: "Rate urgency. Be conservative about escalating unnecessarily."
- **Explicit**: concrete rules mapping specific stated signals to specific levels

**Mock-mode result**: tickets 3 and 5 (genuine boundary cases — a bug
report the customer shrugs off, damage the customer calls "not a huge
deal") flipped between Run 1 and Run 2 under the vague prompt, while
staying identical under the explicit prompt both times.

## Real API results (verified — not mock)

Ran twice against the real API. The pattern that emerged is more precise
than "vague prompts are randomly inconsistent" — worth understanding
exactly, since it's more exam-relevant than a vague "add more detail to
your prompts" takeaway.

**Consistent both runs, both prompts:** Ticket 1 (HIGH), Ticket 2 (LOW).
**Consistent both runs, but only under EXPLICIT — VAGUE also happened to
agree both times:** Ticket 5 stayed LOW under vague both runs — this did
**not** reproduce the mock's predicted flip. Worth being honest that the
mock's specific assumption about which tickets would flip didn't fully
match real behavior.

**Real inconsistency — Ticket 3** (recurring app crash, customer shrugs
it off): vague said "Medium" in Run 1, then **"Low-Medium"** in Run 2 — not
even a defined category, a hedge between two buckets. This is more
informative than a clean flip: without discrete, named categories, the
model has no stable place to land, and the instability shows up in the
output format itself, not just the final answer. Explicit said LOW both
times, with the same reasoning ("customer's own framing overrides the
defect signal") both runs.

**The most exam-relevant finding — Ticket 4** (duplicate charge + explicit
"I'm disputing the charge with my bank"): this isn't run-to-run
inconsistency at all — vague said **"Medium" both times**, consistently.
The problem is *what* it was consistent about: its own reasoning explicitly
said *"don't let the threatening tone inflate the urgency beyond what's
warranted"* and called the dispute threat *"a pressure tactic."* The
explicit prompt said **HIGH both times**, because the stated rule is "any
explicit dispute/chargeback threat = HIGH," full stop — no room for the
model to editorialize about whether the customer really means it.

**This is arguably a more important failure mode than random
inconsistency**: a vague prompt doesn't just risk different answers on
different runs — it lets the model substitute its own judgment about what
"really" warrants urgency for the business's actual stated policy,
*consistently*. A company that wants "any dispute threat gets escalated
immediately, no second-guessing" (a defensible policy — chargebacks are
costly, and triage speed matters more than assessing whether the threat
is credible) gets quietly undermined by a model deciding some threats
don't count.

**Bottom line, from real data:** the explicit prompt was consistent across
all 5 tickets, both runs, citing the same specific signals every time.
Vague failed two different ways — genuine boundary indecision (ticket 3,
producing an undefined output label) and consistent policy misalignment
(ticket 4, the model's own risk philosophy silently overriding stated
business rules).

## Why this matters for the exam

"Be careful," "be conservative," "use good judgment," "avoid X unless
clearly Y" — all leave the actual decision boundary unstated. The fix
isn't "try harder to write a good vague instruction" — it's replacing the
vague concept with categorical, checkable rules: specific signals →
specific outputs, with an explicit default for the no-signal case ("If no
explicit signal, default to LOW").

## What to notice about the explicit prompt's structure

- Each threshold lists **specific, checkable signals** ("explicit
  dispute/chargeback threat," "2+ prior attempts mentioned"), not
  restated vague concepts ("seems really urgent")
- It has an **explicit default** for the no-signal case — vague prompts
  often omit this, leaving what "conservative" means for a truly
  ambiguous case totally undefined
- It explicitly tells the model to apply rules "mechanically," reducing
  the model's own judgment call to interpreting the ticket against
  stated criteria, not inventing new criteria

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| Mock backend's predicted inconsistency pattern (tickets 3 & 5 both flipping) didn't match real API behavior (only ticket 3 flipped; ticket 4 showed a different, arguably more important failure mode instead) | The mock was hand-written to simulate a plausible-sounding version of the phenomenon, not derived from real observed data | Documented real results separately and explicitly flagged where the mock's assumptions were wrong — don't treat a mock's simulated behavior as a stand-in for verified findings once real data is available |

## Next step
Step 2 — few-shot examples targeting boundary cases specifically (not
happy-path examples), to see whether examples alone can substitute for or
complement explicit rules.

---

# Step 2: Few-Shot Prompting with Targeted Boundary Cases

## What this demonstrates

Step 1 found two distinct failure modes in the vague prompt:
1. **Ticket 3** — indecision, producing an undefined "Low-Medium" label
2. **Ticket 4** — the model's own risk judgment overriding an explicit
   dispute-threat signal, consistently

Step 2 adds 3 few-shot examples **deliberately constructed as near-misses
of tickets 3 and 4** — not generic or happy-path examples. Example 2
specifically teaches "casual tone doesn't override an explicit dispute
signal" (the exact lesson ticket 4 needed). Example 3 teaches "a real
recurring bug stays at its warranted level, tone aside" (the exact lesson
ticket 3 needed).

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 step2_few_shot.py
```

Compare all three conditions specifically on tickets 3 and 4:
- Does VAGUE+FEW-SHOT fix ticket 4 (does it now say HIGH, matching
  EXPLICIT, instead of the vague prompt's "Medium" with editorializing
  reasoning)?
- Does VAGUE+FEW-SHOT fix ticket 3's indecision (does it commit to a
  defined category instead of hedging)?
- Run it 2-3 times — does few-shot achieve the same run-to-run
  consistency EXPLICIT showed, or does some variability remain?

## The real question this answers

**Can 2-4 well-chosen examples substitute for writing out explicit rules?**
Record your honest answer once you've run it for real — this is a
genuinely open question worth having real data on rather than assuming
either "examples are just as good" or "rules are always necessary."

## Design principle worth defending in an exam-style answer

**Why target near-misses of known failure cases instead of generic
examples?** A few-shot set of 3 random happy-path examples (a clearly
LOW question, a clearly HIGH emergency, a clearly MEDIUM bug) teaches the
model almost nothing it didn't already know — it already gets easy cases
right. The value of few-shot is entirely concentrated in examples that
resolve genuine ambiguity — which means you have to already know (or
discover, like we did in Step 1) where the model's decision boundary
actually sits before you can write examples that move it.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| Real run couldn't be evaluated — output was truncated at 150 chars, cutting off the actual `Urgency:` verdict for longer responses | `run_condition()` printed `text[:150]`, which was fine for short mock responses but cut off real API responses (which include reasoning) before reaching the conclusion | Print full response text |
| **Example 3 in the few-shot prompt contradicted our own stated EXPLICIT policy** — it labeled a recurring-but-customer-says-not-blocking bug as MEDIUM, while the actual EXPLICIT ruleset ("LOW: issues customer frames as minor/non-blocking") would classify the same ticket as LOW. This means the few-shot examples were teaching a rule inconsistent with the baseline they were meant to approximate. | Written without re-checking the new example against the actual EXPLICIT threshold definitions already established in Step 1 — treated "recurring = escalate" as an intuitive add-on rule without verifying it against the source of truth | Rewrote Example 3 to match the actual policy: customer's own minor/non-blocking framing determines the category regardless of recurrence, since recurrence isn't a listed HIGH/MEDIUM signal in the stated rules — only dispute threats, repeated *unresolved contact*, and deadlines are |

**Worth internalizing as its own lesson**: writing few-shot examples that
sound reasonable in isolation isn't enough — every example needs to be
checked against the actual stated policy/rules, or you risk teaching the
model something that actively conflicts with your own criteria. This is
a real, first-hand instance of exactly the kind of mistake careless
few-shot design produces in production.

## Real results (verified, after fixing the truncation bug and Example 3)

**Ticket 3** (recurring bug, customer downplays it):
- VAGUE: still "Low-Medium" — same undefined hedge as every prior run, unfixed
- VAGUE+FEW-SHOT: clean "LOW", reasoning explicitly states "repeated bug
  occurrences alone don't elevate urgency per policy" — near-verbatim the
  corrected Example 3's lesson
- EXPLICIT: "LOW" — matches few-shot exactly

**Ticket 4** (dispute threat stated with attitude):
- VAGUE: "Medium-High" this run — a *third* distinct label across three
  real runs (Step 1 got "Medium" twice, this run got "Medium-High").
  Reasoning still explicitly discounts the threat as "a common pressure
  tactic," same systematic issue as Step 1, now also demonstrating further
  run-to-run instability on top of it
- VAGUE+FEW-SHOT: clean "HIGH", explicitly citing "Explicit
  dispute/chargeback threat" as a found signal — directly reflecting
  Example 2's lesson
- EXPLICIT: "HIGH" — matches few-shot exactly

**Conclusion: once the examples were corrected to actually align with
stated policy, 3 targeted few-shot examples brought the vague prompt's
behavior into full agreement with the explicit-rules prompt on both known
failure cases** — while the vague prompt alone kept failing the same two
ways, run after run.

**The essential caveat**: this worked specifically *because we already
knew where the failure modes were*, from Step 1's diagnosed real data.
Few-shot isn't a generic improvement lever — it's targeted patching of
known ambiguity. Writing examples blind, without first knowing the actual
decision boundary, risks exactly what our first version of Example 3 did:
confidently teaching something that contradicts your own stated policy.
The diagnostic work (Step 1) had to happen before the fix (Step 2) could
be targeted correctly — this is worth remembering as a general workflow,
not just specific to this exercise.

---

# Step 3: Structured Output via `tool_use` — Structure Guaranteed, Semantics Not

## What this demonstrates

Two lessons, one exercise:

**Lesson A — the central claim of this concept, tested directly:** does
wrapping the VAGUE prompt in a `tool_use` JSON schema fix its
miscalibration on ticket 4, or does the schema just force whatever answer
the model would have given anyway into a valid shape? We reuse the exact
VAGUE and EXPLICIT prompts' underlying logic from Steps 1-2, now forced
through `EXTRACT_TOOL`'s schema via `tool_choice: {"type": "tool", ...}`.

**Prediction to verify against real data**: the schema should NOT fix
ticket 3/4's miscalibration — it should just produce a validly-shaped
JSON object with the same wrong `urgency` value VAGUE always gave. If
that's what happens, it's strong, direct evidence for "structure and
correctness are independent" rather than just an assertion to take on faith.

**Lesson B — two schema design choices that matter:**
- `refund_requested` is `["boolean", "null"]`, not just `boolean`. A
  non-nullable boolean forces a guess on every ticket that never mentions
  a refund at all — null is the honest answer for "not stated," and a
  schema that doesn't allow it forces hallucination by construction.
- `issue_category` has an `"other"` value plus a paired
  `issue_category_detail` free-text field. Without an escape hatch, a
  ticket that doesn't cleanly fit any category gets force-fit into the
  closest wrong one — the enum's own design can silently distort results.

## Try it yourself

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 step3_tool_use_schema.py
```

Check specifically:
1. **Tickets 3 and 4**: does VAGUE+schema still show the miscalibration
   (medium/hedged urgency, discounting the dispute signal) despite valid
   JSON structure? Compare directly against EXPLICIT+schema.
2. **`refund_requested` across all 5 tickets**: does it correctly return
   `null` for every ticket that never mentions a refund, or does the
   model guess `true`/`false` anyway despite the schema allowing null?
3. **`issue_category`**: does any ticket get force-fit into a category
   that doesn't quite match, or does `"other"` + detail get used
   appropriately when warranted?

## Design principle worth defending in an exam-style answer

**Why is `refund_requested: null` a better design than defaulting to
`false`?** `false` claims something definite happened (the customer was
asked and declined, or explicitly has no refund need) — but "never
mentioned" and "explicitly declined" are different facts with different
downstream handling. Collapsing them into the same `false` value discards
real information and risks the extraction pipeline confidently asserting
something the ticket never said.

## Real results (verified) — the miscalibration relocated, not disappeared

**Ticket 3**: VAGUE+schema gave `urgency: "medium"`, EXPLICIT+schema gave
`"low"`. Same underlying miscalibration as the free-text version — the
schema forced a committed answer (no more "Low-Medium" hedge) but the
committed answer was still wrong relative to policy. Structure removed
the ability to hedge, not the underlying error.

**Ticket 4 — the important, non-obvious result**: `urgency` was
**correctly** `"high"` under VAGUE+schema this time, unlike every free-text
run (which said Medium or Medium-High). But `refund_requested` came back
`True` under VAGUE+schema — **ticket 4's text never mentions a refund at
all**, only a dispute threat. EXPLICIT+schema correctly returned `null`,
guided by an explicit instruction VAGUE lacked ("do not infer a refund
request from general dissatisfaction alone").

**The underlying vagueness problem didn't disappear — it moved to a
different field.** Forcing structure seems to have reduced the
urgency-discounting reasoning we saw in free text (there's no room to
write "well, it's probably just a pressure tactic" before filling in a
field), but the same undisciplined judgment surfaced instead as a
hallucinated refund inference — `True` guessed from general "customer
upset about money" vibes rather than an actual stated request.

**Ticket 5 confirms the pattern**: VAGUE+schema returned
`refund_requested: False` (not `null`) for a ticket that never mentions a
refund at all. `False` asserts "explicitly declined" — a fact the ticket
never states. EXPLICIT+schema correctly returned `null`.

**This is the cleanest real evidence for the core lesson**: making a field
nullable in the schema only makes honesty *possible*, it doesn't make the
model *use* null instead of guessing — that required an explicit
instruction telling it not to infer. A nullable field paired with a vague
prompt still hallucinates; it just hallucinates into a technically-valid
enum value instead of a wrong free-text sentence, which is arguably more
dangerous since it's easy to trust structured output more than prose by
default.

**Gap to note**: none of the 5 sample tickets triggered `"other"` —
everything fit a named category under both conditions, so this run never
actually exercised the escape-hatch design. A follow-up ticket that
doesn't cleanly fit any category would be needed to test whether it
correctly falls through to `"other"` + `issue_category_detail`, or gets
force-fit into the nearest wrong bucket instead.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| None — this step's real run worked correctly on the first try; the interesting result was in the DATA (miscalibration relocating between fields), not a bug in the exercise itself | — | — |

## Next step
Step 4 — `tool_choice`: auto vs. any vs. forced, and when each is the
right call.