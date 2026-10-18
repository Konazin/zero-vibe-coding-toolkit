# Backend delivery: a practical gate matrix

## Before edits

Define request/response schema, authorization boundaries, persistence invariants and failure semantics. Trace controller/route -> service -> repository and emitted events. Identify callers and migration compatibility.

## During implementation

- Validate inputs and enforce object-level authorization server-side.
- Avoid hidden database writes and N+1 queries in new endpoints.
- Put transactions around the required atomic operation, not arbitrary layers.
- Make retries and deduplication deliberate; do not assume idempotence.
- Preserve precision for money/tax/financial calculations.
- Document deployment order and rollback for schema changes.

## Gates, depending on actual stack

```bash
# Spring Boot Maven, only when Maven wrapper exists:
./mvnw test
# Spring Boot Gradle, only when Gradle wrapper exists:
./gradlew test
# Python, only when pytest is configured:
python3 -m pytest -q
# Node, only when package scripts exist:
npm test
```

At least one negative authorization test for protected resources and one failure-path test for changed endpoints. Integration tests should verify actual persistence behavior rather than mocking everything. Mark unsupported checks NOT RUN.
