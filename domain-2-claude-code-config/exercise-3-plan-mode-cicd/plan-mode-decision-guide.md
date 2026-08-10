# Plan Mode vs. Direct Execution — Decision Framework

## What plan mode actually is (mechanically)

Not a prompt instruction — a **permission mode** enforced at the system
level. In plan mode, Claude Code can read files, run read-only exploratory
commands, and write a plan document, but **cannot** write/edit files or run
state-changing commands, at all, until you approve the plan. This is a hard
constraint, not a request Claude is honoring.

Activate: `Shift+Tab` (cycle modes), `/plan` prefix, or
`claude --permission-mode plan`. Can switch modes mid-conversation.

## Decision framework

**Use plan mode when:**
- Large-scale or structural changes (refactor touching many files, service
  boundary changes, module reorganization)
- Multiple valid approaches exist and the choice has real tradeoffs
- Architectural decisions with downstream consequences (API contracts,
  data model changes)
- You genuinely don't know yet what the change should touch

**Use direct execution when:**
- The change is well-scoped and the correct approach is already known
  (single-file bug fix with a clear stack trace, a config value update,
  a well-understood conditional)
- There's no design decision to make — only an implementation to type out

**The overhead is real and worth naming honestly:** plan mode adds a
review step, which is friction on simple tasks. The tradeoff is: planning
overhead is minutes, rework from a wrong direct-execution attempt on a
complex task can be much more. Match the mode to the task, don't default
to one for everything.

## Exam-relevant nuance

Plan mode and permission mode (auto-accept, per-tool approval, etc.) are
**different axes** — plan mode controls *what Claude investigates and
whether it can act at all*; permission mode controls *how much autonomy
Claude has once it's allowed to act*. A common pattern: plan mode to design,
then switch to auto-accept to execute the approved plan without per-step
interruption.

## Try it yourself

```bash
cd acme-shop
claude --permission-mode plan
```
Give it a genuinely ambiguous, multi-file task (e.g. "add rate limiting to
the checkout API — figure out where it should live and how it should be
configured"). Observe:
1. It explores and proposes a plan without touching any files
2. You can edit the plan (`Ctrl+G`) before accepting
3. Only after acceptance does it write anything

Then try the same exercise with a trivial, well-scoped task in plan mode
and note how much the review step actually added — this is the "friction
vs. value" tradeoff to internalize, not just recite.
