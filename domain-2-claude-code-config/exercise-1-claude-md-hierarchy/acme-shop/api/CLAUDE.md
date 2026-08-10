# api/ — Express API service

This file adds to (does not replace) the root `CLAUDE.md`. More specific
instructions here take precedence for anything under `api/`.

## Stack specifics
- Express 4, Prisma ORM, PostgreSQL
- Auth: JWT via `src/middleware/auth.ts`

## Conventions specific to this service
- Every route handler must validate input with a Zod schema before touching
  the database — see `src/routes/*.ts` for the pattern
- Never return raw Prisma errors to the client; map them to the shared
  `ApiError` shape in `src/errors.ts`

## Testing
- Run `npm test` from this directory, not the repo root
- See `.claude/rules/testing-rules.md` (repo root) for test-writing conventions
  that apply across both `api/` and `frontend/`
