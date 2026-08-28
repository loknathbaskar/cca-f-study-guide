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
