# Claude Certified Architect (CCA-F) — Study Guide & Hands-On Exercises

Personal prep notes and runnable exercises for the **Claude Certified Architect – Foundations**
exam. Organized by the 5 official exam domains. Each exercise is real, runnable code (not
slides) — most run in "mock mode" out of the box (no API key needed) and switch to real
Claude API calls automatically if `ANTHROPIC_API_KEY` is set.

## Exam overview

Scenario-based, multiple choice, 4 of 6 possible scenarios drawn per attempt:
Customer Support Agent, Code Generation w/ Claude Code, Multi-Agent Research System,
Developer Productivity Tools, Claude Code in CI/CD, Structured Data Extraction.

## Domains & weights

| # | Domain | Weight | Folder |
|---|--------|--------|--------|
| 1 | Agentic Architecture & Orchestration | 27% | `domain-1-agentic-architecture/` |
| 2 | Claude Code Configuration & Workflows | 20% | `domain-2-claude-code-config/` |
| 3 | Prompt Engineering & Structured Output | 20% | `domain-3-prompt-engineering/` |
| 4 | Tool Design & MCP Integration | 18% | `domain-4-tool-design-mcp/` |
| 5 | Context Management & Reliability | 15% | `domain-5-context-reliability/` |

## How this repo is organized

Each domain folder contains:
- `README.md` — concept notes, key terms, common exam traps
- `exercise-N-<name>/` — one folder per hands-on exercise, each with its own code + `NOTES.md`
  documenting what the exercise teaches and what bugs/gotchas came up while building it

## Status

- [x] Domain 1 — Exercise 1: Multi-Agent Research System (coordinator/subagent pipeline, retries, escalation)
- [ ] Domain 2 — CLAUDE.md hierarchy, `.claude/rules/`, custom skills
- [ ] Domain 3 — Structured output, few-shot prompting, validation-retry loops
- [ ] Domain 4 — MCP tool descriptions, structured error responses
- [ ] Domain 5 — Context compression, scratchpad patterns, escalation design

## Running exercises

Each exercise folder is self-contained. From inside it:
```bash
pip install -r requirements.txt   # if present
python3 demo.py
```
Set `export ANTHROPIC_API_KEY=sk-...` first if you want real API calls instead of mock mode.

## License

Feel free to reuse/fork for your own CCA-F prep.
