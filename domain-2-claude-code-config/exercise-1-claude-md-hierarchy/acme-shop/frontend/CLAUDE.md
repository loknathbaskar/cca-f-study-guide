# frontend/ — React app

Adds to the root `CLAUDE.md` for anything under `frontend/`.

## Stack specifics
- React 18, Vite, Tailwind
- State: React Query for server state, no Redux

## Conventions specific to this service
- Components are function components with hooks only — no class components
- Co-locate a component's test file next to it (`Button.tsx` + `Button.test.tsx`)
