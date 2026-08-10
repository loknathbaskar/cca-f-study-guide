# Domain 3: Prompt Engineering & Structured Output (20%)

## Core concepts
- Explicit, categorical criteria over vague instructions ("flag if X, Y, or Z" not "be careful").
- Few-shot examples for ambiguous edge cases.
- `tool_use` with JSON schemas for structured output; nullable fields to avoid hallucinated values.
- Validation-retry loops: validate output against schema, re-prompt with the specific validation error on failure.
- Message Batches API for large-scale/batch processing.
- Multi-pass review architectures (e.g. draft pass + critique pass).

## Exercises (planned)
- [ ] Build a structured extraction pipeline with a JSON schema + nullable fields
- [ ] Add a validation-retry loop that feeds the schema error back to Claude
- [ ] Compare a vague prompt vs. an explicit-criteria prompt on the same ambiguous input
- [ ] Batch-process a set of documents with the Message Batches API
