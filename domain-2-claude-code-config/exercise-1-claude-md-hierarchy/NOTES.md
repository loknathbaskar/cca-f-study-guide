# Exercise 1: CLAUDE.md Hierarchy, Path-Scoped Rules, and a Forked-Context Skill

Maps to **Domain 2: Claude Code Configuration & Workflows (20%)**.

## What this exercise builds

A realistic two-service repo (`acme-shop/`) demonstrating:

1. **CLAUDE.md hierarchy** — root `CLAUDE.md` (cross-cutting) + `api/CLAUDE.md`
   and `frontend/CLAUDE.md` (service-specific, more specific overrides/adds to
   the root)
2. **Path-scoped rules** (`.claude/rules/*.md`) — `api-rules.md` loads only
   when touching `api/src/routes/**`; `testing-rules.md` loads only when
   touching test files, across *both* services via two path patterns
3. **A skill with `context: fork`** — `deploy-preview` runs in an isolated
   subagent so verbose build output doesn't pollute the main session, and
   uses `allowed-tools` to restrict it to `Bash, Read` only (no write/edit
   access — a deploy skill has no legitimate reason to modify source)

## How to actually test this in your own VSCode

This exercise is config, not runnable code — the way to verify it is to
install Claude Code and observe its behavior in this sample repo:

```bash
npm install -g @anthropic-ai/claude-code
cd acme-shop
claude
```

Then inside the Claude Code session, try:
- `/context` — confirm which CLAUDE.md files loaded
- Ask it to edit `api/src/routes/checkout.ts` — confirm `api-rules.md`
  becomes relevant (it should reference Zod validation / ApiError / rate
  limiting without you repeating those constraints)
- Ask it to edit `frontend/src/CartButton.test.tsx` — confirm the testing
  rule applies here too, via its second path pattern
- Try invoking `/deploy-preview` — observe that it runs isolated (forked
  context) rather than dumping build logs into your main conversation

## Design decisions worth defending in an exam-style answer

- **Why does the root CLAUDE.md explicitly point to the more specific
  files instead of just listing everything itself?** Keeps the root file
  small (it loads on every single session regardless of what you're doing),
  and avoids duplicating content that's only relevant sometimes.

- **Why is `testing-rules.md` a single rule with two path patterns instead
  of two separate rules, one per service?** The rule content (test-naming,
  no snapshot tests for money, mock external services) is identical across
  both services — duplicating it in `api/CLAUDE.md` and `frontend/CLAUDE.md`
  would mean updating it twice every time it changes.

- **Why `context: fork` specifically for `deploy-preview` and not, say,
  a code-review skill?** Fork is worth it when a skill's *intermediate*
  output (build logs, exploration noise) is large and not itself useful to
  keep in the main conversation — only the final result matters. A skill
  whose reasoning process IS useful to see inline shouldn't fork.

- **Why restrict `allowed-tools` on this skill instead of leaving it
  unrestricted?** Least-privilege: a deploy skill's job is build + ship,
  not edit source. Restricting the tool set is a safety boundary, not
  friction — note allowed-tools is currently a pre-approval / experimental
  mechanism, not a hard technical block, so it complements but doesn't
  replace stricter enforcement (hooks) for anything security-critical.

## Bugs / gotchas log

| Issue | Cause | Fix |
|---|---|---|
| `/memory` didn't show `api/CLAUDE.md` or `.claude/rules/api-rules.md` as loaded, even though the terminal output showed them loading when Claude read `checkout.ts` | `/memory` appears to primarily list/edit the memory files discovered **at session start** (root + user-level CLAUDE.md) — it's not a live, turn-by-turn log of files pulled in **on-demand** mid-session for subdirectory CLAUDE.md / path-scoped rules. | Confirmed via the `InstructionsLoaded` hook below — see next row for how that hook itself needed debugging first. |
| `InstructionsLoaded` hook showed "no hooks configured for this event" in `/hooks`, even though `.claude/settings.json` was valid JSON and `/status` listed "Shared project settings" as loaded | The actual `settings.json` had been placed at `acme-shop/settings.json` (top level) instead of `acme-shop/.claude/settings.json`. Claude Code only reads project settings from inside the `.claude/` subdirectory — a stray top-level `settings.json` is silently inert, never read, never errors. `/status` showing "Shared project settings" was true for a *different* valid settings file already in the hierarchy, not the one we'd actually edited — its presence in Setting sources doesn't guarantee the specific hook you just added is the one that's active if more than one settings file is in play. | Move the file to `acme-shop/.claude/settings.json`. Confirmed fixed via `/hooks`, which showed the event, matcher, type, exact command, and source path once correctly placed — that's the definitive way to check one specific hook is registered, more reliable than `/status`'s file-level summary. |

## Verifying what's actually loaded (not just `/context` or `/memory`)

This turned out to be a real gap worth documenting rather than a mistake:
`/context` gives an aggregate token count by category; `/memory` reflects the
files discovered at session start well, but doesn't reliably reflect
subdirectory CLAUDE.md / path-scoped rules loaded on-demand mid-session.

**Three ways to actually confirm, in order of reliability:**

1. **Ask Claude directly, mid-session:**
   > "List the exact CLAUDE.md and rules files you currently have loaded,
   > verbatim, with their file paths."

   This forces it to report from its actual context rather than you
   inferring from a UI element whose live-update semantics aren't fully
   pinned down.

2. **Set up an `InstructionsLoaded` hook** — purpose-built for this. It fires
   every time a CLAUDE.md or `.claude/rules/*.md` file loads into context
   (session-start or on-demand), logging exactly which file, why (`load_reason`),
   and from which layer (`memory_type`). It has **no decision control** — it
   can't block or modify a load, and its exit code is ignored — it's purely
   observational, meant for audit/debugging exactly this kind of question.

   Like all Claude Code hooks, it receives JSON on **stdin** (not environment
   variables — an earlier version of this note incorrectly assumed an env var).
   Example payload:
   ```json
   {
     "session_id": "abc123",
     "cwd": "/Users/you/acme-shop",
     "hook_event_name": "InstructionsLoaded",
     "file_path": "/Users/you/acme-shop/api/CLAUDE.md",
     "memory_type": "Project",
     "load_reason": "session_start"
   }
   ```

   `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "InstructionsLoaded": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "jq -r '\"\\(now | strftime(\"%Y-%m-%dT%H:%M:%SZ\")) loaded: \\(.file_path) (reason: \\(.load_reason), type: \\(.memory_type))\"' >> .claude/instructions-loaded.log"
             }
           ]
         }
       ]
     }
   }
   ```
   Tail `.claude/instructions-loaded.log` after asking Claude to read a file
   in `api/` — you should see `api/CLAUDE.md` and
   `.claude/rules/api-rules.md` appear with a load reason distinct from
   `session_start`, only after that read, not at launch.

3. **Rule out a version bug.** Run `claude --version` and compare against
   current release notes if steps 1–2 disagree with each other — subdirectory
   CLAUDE.md loading has had real, tracked bugs in some releases
   (anthropics/claude-code#2571, #3103), not just documentation/UI ambiguity.

**Exam-relevant takeaway:** don't assume a UI/CLI status command is
ground truth for what's in context — for anything you need to be *certain*
about (security-sensitive rules, compliance requirements), verify with a
hook-based log or direct inspection, not a convenience command. This is the
same "natural language vs. enforced" theme from hooks vs. CLAUDE.md — even
*verifying* state benefits from a programmatic source of truth over an
interpreted/summarized one.

## Follow-up exercises (not yet done)
- [ ] Add a `.claude/rules/` file scoped to database migration files with a
      stricter rule (e.g. "never write a destructive migration without an
      explicit rollback script")
- [ ] Convert a natural-language-only rule into a `PreToolUse` hook and
      compare reliability — does Claude ever skip the natural-language rule
      under load, and does the hook catch what it misses?
- [ ] Try `/init` in a repo with existing Cursor rules (`.cursor/rules/`) and
      observe what it pulls into the generated `CLAUDE.md`
- [ ] Wire up the `InstructionsLoaded` hook above for real and confirm the
      log output matches what `/memory` does and doesn't show