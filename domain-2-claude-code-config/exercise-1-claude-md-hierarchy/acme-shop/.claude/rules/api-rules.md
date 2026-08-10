---
paths:
  - 'api/src/routes/**/*.ts'
---

# API route rules

These rules apply ONLY when Claude is reading or editing files under
`api/src/routes/`. They do not load — and don't cost context — when you're
working on the frontend, on migrations, or on anything outside this path.

- Every route must validate its input with a Zod schema before any
  database call
- Every route must return the shared `ApiError` shape on failure —
  never a raw stack trace or raw Prisma error
- Rate-limit-sensitive routes (auth, checkout) must use the
  `rateLimiter` middleware — check `src/middleware/rateLimiter.ts`
  before assuming a route needs it
