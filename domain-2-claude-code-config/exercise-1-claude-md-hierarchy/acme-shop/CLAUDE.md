# acme-shop

E-commerce platform: Node/Express API + React frontend.

## Architecture
- `api/` — Express REST API, PostgreSQL via Prisma
- `frontend/` — React 18 + Vite

## Conventions (apply everywhere in this repo)
- TypeScript strict mode, no `any` without a comment explaining why
- Commits: conventional commits (`feat:`, `fix:`, `chore:`...)
- Never commit `.env` files or secrets

## Where to look for more specific rules
- API-specific conventions: `api/CLAUDE.md` and `.claude/rules/api-rules.md`
- Frontend-specific conventions: `frontend/CLAUDE.md`
- Testing conventions (path-scoped, loads only when touching tests): `.claude/rules/testing-rules.md`

Keep this file to cross-cutting, always-relevant instructions only. Anything
narrower belongs in a subdirectory CLAUDE.md or a path-scoped rule — don't let
this file grow into a dumping ground (a bloated root CLAUDE.md burns context
on every single session regardless of what you're actually working on).
