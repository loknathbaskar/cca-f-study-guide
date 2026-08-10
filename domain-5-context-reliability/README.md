# Domain 5: Context Management & Reliability (15%)

## Core concepts
- Preserving critical facts across long conversations (compression, scratchpad files).
- Escalation patterns: when to hand off to a human vs. push through with a partial result.
- Error propagation in multi-agent setups (see Domain 1 Exercise 1 — same underlying pattern).
- Managing context while exploring large codebases (targeted reads, not full-file dumps).

## Exercises (planned)
- [ ] Build a scratchpad-file pattern for a long-running session
- [ ] Design an escalation policy matrix (error type -> retry / degrade / escalate)
- [ ] Simulate context-overflow and test a compression strategy
