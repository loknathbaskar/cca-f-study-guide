---
paths:
  - '**/*'
---

# Secrets handling (natural-language version — see hook comparison in NOTES.md)

- Never read the contents of `.env` files
- Never write to or edit `.env` files
- Never include values from `.env` in commit messages, logs, or output

**This rule is intentionally left in place alongside the `PreToolUse` hook**
(`.claude/settings.json`) as a deliberate comparison point for this exercise —
see `NOTES.md` for what actually happens when each is tested under pressure
(e.g. an explicit, insistent instruction to read the file anyway).
