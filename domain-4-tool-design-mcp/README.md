# Domain 4: Tool Design & MCP Integration (18%)

## Core concepts
- Tool descriptions must be unambiguous — near-duplicate tools cause misrouting (see Domain 1 Exercise 1 bug log for a live example).
- Structured error responses: `errorCategory`, `isRetryable`, human-readable `message`.
- Distributing tools across multiple agents vs. giving one agent everything.
- MCP server configuration (`.mcp.json`), MCP primitives: tools, resources, prompts.

## Exercises (planned)
- [ ] Write two near-duplicate tool descriptions, test whether Claude picks the right one, then disambiguate
- [ ] Add structured error responses with `errorCategory` + `isRetryable` to a tool
- [ ] Configure a real `.mcp.json` and connect an MCP server
