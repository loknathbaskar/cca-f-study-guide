---
paths:
  - 'api/tests/**/*.ts'
  - 'frontend/**/*.test.tsx'
---

# Testing rules

Applies across BOTH services (note two path patterns above) — this is the
right place for a rule that's narrow in *when* it applies but shared across
directories, so it doesn't have to be duplicated in both `api/CLAUDE.md` and
`frontend/CLAUDE.md`.

- Test names describe behavior, not implementation:
  `"rejects checkout when cart is empty"`, not `"test checkout function"`
- No snapshot tests for anything that touches money calculations —
  assert exact expected values instead
- Mock external services (payment provider, email) — never hit them in tests
