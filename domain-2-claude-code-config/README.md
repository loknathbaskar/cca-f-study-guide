# Domain 2: Claude Code Configuration & Workflows (20%)

## Core concepts

- **CLAUDE.md hierarchy**: root (repo-wide, cross-cutting) → subdirectory
  CLAUDE.md files (more specific, add to/override root) → user-level
  `~/.claude/CLAUDE.md` (personal, applies across all your projects, never
  shared). More specific instructions layer on top of broader ones.
- **`.claude/rules/*.md`**: path-scoped instructions with YAML frontmatter
  (`paths: [...]`). Only load into context when Claude is working with a
  matching file — unlike CLAUDE.md, which loads every session regardless
  of relevance. This is the key lever for keeping context lean in a large repo.
- **Skills (`.claude/skills/<name>/SKILL.md`)**: on-demand playbooks, only
  `description` loads by default; full body loads when invoked. Key
  frontmatter fields:
  - `context: fork` — runs the skill in an isolated subagent context so its
    intermediate output (logs, exploration) doesn't pollute the main session
  - `allowed-tools` — pre-approves specific tools for the skill (currently a
    pre-approval mechanism, not a hard block — treat as an experimental
    safety boundary, not a substitute for hooks on anything security-critical)
  - `model` — override which model runs the skill (e.g. `haiku` for cheap,
    routine forked tasks)
  - `disable-model-invocation` — skill only runs via explicit `/name`, never
    auto-triggered by Claude's own judgment
- **Auto memory**: Claude's own notes written from corrections/preferences
  during a session — distinct from CLAUDE.md, which you write explicitly.
  Conservative by design; not every session produces new auto memory.
- **Hooks**: the enforcement layer above natural language. CLAUDE.md and
  rules are *interpreted* by the model — usually followed, not guaranteed.
  Hooks are event-triggered scripts that run regardless of what the model
  decides, for anything where "usually follows the rule" isn't good enough.
- **CI/CD integration**: `-p` (print/non-interactive mode) with
  `--output-format json` for scripting Claude Code into pipelines.

## Common exam traps

- Putting narrow, occasionally-relevant instructions in the root CLAUDE.md
  instead of a path-scoped rule — this burns context on every session
  regardless of what's being worked on.
- Duplicating a rule that's shared across services into multiple CLAUDE.md
  files instead of one path-scoped rule with multiple path patterns.
- Assuming a CLAUDE.md instruction will be reliably enforced 100% of the
  time — it's natural language the model interprets, not a hard constraint.
  Anything that must never be skipped belongs in a hook.
- Leaving `allowed-tools` unset on a skill that should be least-privilege
  (e.g. a deploy skill that has no legitimate reason to edit source).
- Using `context: fork` on a skill whose reasoning process is itself useful
  to see inline — fork is for skills with noisy intermediate output where
  only the final result matters, not a default for every skill.

## Exercises

### Exercise 1 — CLAUDE.md Hierarchy + Path-Scoped Rules + Forked Skill
Built a realistic two-service repo (`acme-shop/`) with a root CLAUDE.md,
service-level CLAUDE.md files, two path-scoped rules (one single-service,
one shared across services via multiple path patterns), and a `deploy-preview`
skill using `context: fork` + `allowed-tools` restriction. Debugged a real
settings-file placement issue and confirmed the full hierarchy via the
`InstructionsLoaded` hook — see the exercise's `NOTES.md` for the full
debugging trail (genuinely useful reading, not just a clean success story).

### Exercise 2 — Subagents + Hooks vs. Natural-Language Rules
Built a `security-reviewer` Claude Code subagent (distinct from Domain 1's
multi-agent architecture pattern — this is Claude Code's own delegation
mechanism). Core exercise: the same rule ("never touch .env files")
expressed two ways — a natural-language `.claude/rules/` file and an
enforced `PreToolUse` hook — with a documented test procedure for actually
observing where natural language breaks down under insistent prompting and
where the hook holds regardless.

### Exercise 3 — Plan Mode vs. Direct Execution + CI/CD
Decision framework for when plan mode's overhead is worth it vs. friction,
plus a real GitHub Actions workflow using `-p`/`--output-format json` for
automated PR review — with least-privilege `--allowedTools`, exit-code
handling that degrades gracefully instead of blocking the pipeline, and
per-run cost/usage logging. Includes a local test script for faster
iteration before wiring into actual CI.

**Try each exercise yourself:** every exercise folder has its own `NOTES.md`
with a "try it yourself" section and a results table to fill in — don't
just read these, run them and record what actually happens on your version.

### Status
- [x] CLAUDE.md hierarchy, path-scoped rules, skill frontmatter (Ex. 1)
- [x] Commands/skills/subagents, hooks vs. natural language (Ex. 2)
- [x] Plan mode vs. direct execution, CI/CD flags (Ex. 3)
- [ ] MCP servers in Claude Code workflows (`.mcp.json`) — deferred to
      Domain 4, where MCP is covered in depth
