# Four Enforcement Mechanisms in Claude Code — What Each Actually Guarantees

A recurring exam theme: knowing *which* mechanism to reach for isn't about
which one is "best" — it's about matching the mechanism to how strong a
guarantee you actually need. These four look similar on the surface (they
all "control what Claude does") but sit on very different points of a
reliability spectrum.

---

## 1. CLAUDE.md / `.claude/rules/*.md` — Natural language, interpreted

**What it is:** Instructions written in plain English (or any language),
loaded into context, that the model reads and reasons about like any other
part of its prompt.

**What it actually guarantees:** Nothing, technically. It's not code — it's
context the model interprets. In practice it's followed the large majority
of the time, especially with clear, specific wording. But "usually
followed" and "guaranteed" are different properties.

**Two distinct ways it can fail — worth telling apart:**
- **Compliance failure**: the model sees the rule, understands it, and
  doesn't follow it (rare with clear wording, more likely under adversarial
  pressure or genuine ambiguity)
- **Loading-timing failure**: the model never even had the rule in context
  yet when the relevant action happened. Path-scoped rules load reactively —
  triggered by touching a matching file — which means if the sensitive
  file is the very first thing touched in a session, the rule can't have
  loaded before that first action. We demonstrated this directly: a
  `paths: ['**/*']` rule failed to prevent a `.env` read specifically
  because `.env` was the first file touched in that session, with nothing
  earlier to have triggered the rule's load.

**Use it for:** guidance that should generally be followed but where a hard
block would sometimes be wrong — style conventions, "prefer X approach,"
architectural preferences. Anything where you want the model reasoning
about the instruction, not blindly obeying it regardless of context.

**Don't use it alone for:** anything where "usually" isn't good enough.

---

## 2. `PreToolUse` (and other) hooks — Enforced, code-level

**What it is:** A shell command that runs automatically before (or after,
depending on the event) a matching tool call, receiving structured JSON on
stdin describing exactly what's about to happen. It can inspect that JSON
and exit with a blocking code (2, for `PreToolUse`) to stop the call
entirely.

**What it actually guarantees:** A real technical guarantee, not an
interpreted suggestion. It's not "context that has to load in time" — it's
a gate every matching tool call passes through, checked fresh on every
single call. This is exactly why it closed the gap the natural-language
rule couldn't: there's no race between "has the rule loaded yet" and "has
the action happened yet," because the hook isn't a loading problem at all.

**Its own limits, worth knowing:**
- Only as good as the script you write — a hook checking the wrong field,
  or with a bug, provides a false sense of security
- Some hook events (like `InstructionsLoaded`) are explicitly
  observational only — no decision control, exit code ignored. Know which
  events can block and which can't before relying on one.
- A hook needs to actually be correctly registered — we found a real case
  where a hook silently failed to register because its config file was in
  the wrong directory, with no error surfaced anywhere obvious. Verify
  registration (`/hooks`) don't just assume a file existing means it's active.

**Use it for:** anything that must never be skipped, regardless of
phrasing, insistence, or session state — secrets access, destructive
commands (`terraform apply` against production, `git push --force` to
main), compliance-mandated checks.

---

## 3. `allowed-tools` (skill/subagent scoping) — Pre-approval, not a hard wall

**What it is:** Frontmatter on a skill or a subagent's `tools:` field
listing which tools it's permitted to use.

**What it actually guarantees:** Narrower than it sounds. Current Claude
Code treats this more as a **pre-approval mechanism** — it determines
whether a tool call happens without a permission prompt — rather than an
unconditional technical wall that makes the excluded tools physically
impossible to invoke under any circumstance. Treat it as an
experimental/soft safety boundary, not a substitute for a hook when the
guarantee needs to be airtight.

**What it's genuinely good for:** least-privilege design as a default
posture. A deploy skill with no legitimate reason to edit source shouldn't
have Write/Edit available — restricting the tool set is good practice and
meaningfully reduces the *surface area* for something going wrong, even if
it's not an ironclad guarantee. A read-only subagent (like our
`security-reviewer`) genuinely cannot construct a fix itself when scoped to
`Read, Grep, Glob` — there's no write path available to it at all in
practice, which is a real and useful constraint even if the underlying
mechanism is "pre-approval" rather than "hard block."

**Don't rely on it alone for:** a guarantee that must never be violated
under any framing or pressure — pair it with a hook if the stakes are that
high.

---

## 4. Hard limits (`--max-turns`, `MAX_RETRIES`, timeouts) — Bounds, not adaptive ceilings

**What it is:** A numeric cap on iterations, retries, or time, enforced by
the harness (Claude Code CLI, or your own orchestration code) rather than
by the model.

**What it actually guarantees:** Exactly what it says — a hard stop at N,
full stop. No silent extension, no adaptive "well it needed a bit more so
I'll allow 2 extra." If a task genuinely needs 5 turns and you cap it at 3,
it stops at 3, incomplete, every time. This is deliberate: the entire
purpose is bounding cost/time/blast-radius, which necessarily means it
will sometimes cut off a task that could have used more room. That's the
tradeoff, not a defect to route around automatically.

**Same pattern, two places we've now seen it:**
- `MAX_RETRIES = 2` in the Domain 1 coordinator — caps retry attempts
  before escalating to a human, rather than retrying forever
- `--max-turns 3` in the Domain 2 CI script — caps agentic turns in a
  headless call, rather than letting a single CI job run unbounded

**Use it for:** anything where unbounded cost, time, or iteration is itself
the risk you're managing — not primarily a correctness/safety mechanism
like the other three, but a resource/blast-radius control.

---

## Quick decision guide

| Question | Reach for |
|---|---|
| "Should generally happen, but judgment matters" | CLAUDE.md / rules |
| "Must never happen, no exceptions, regardless of phrasing" | `PreToolUse` hook |
| "This component shouldn't normally need this tool" | `allowed-tools` scoping |
| "This could run away in cost/time/iterations if unchecked" | Hard limit (`--max-turns`, retry cap) |

## The one-sentence version worth remembering

**Rules are advice the model reasons about; hooks are gates every call must
pass; tool scoping is a soft default posture; hard limits bound runaway
cost, not correctness.** Picking the wrong one for the stakes involved is
the actual failure mode being tested — not knowing that each mechanism
exists.
