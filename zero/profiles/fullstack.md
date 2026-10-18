# Fullstack engineering profile

Combine frontend and backend engineering without assuming that one agent should rewrite both sides.

## End-to-end contract

- Define the user-visible scenario, API contract, error propagation, authz, persistence and rollback before cross-layer changes.
- Trace frontend state -> client request -> route/service -> database -> response -> rendering.
- Reuse existing modules. Do not change API schemas as an incidental side effect of UI work.
- Keep migrations additive where possible and ensure old clients remain functional through rollout.
- Run relevant frontend checks, backend checks, API contract tests and at least one cross-layer smoke test.
- Verify accessibility and security at their correct layers. Neither is interchangeable with a generic smoke test.

## Context budget

Map endpoint contracts and changed symbols, then open the smallest source slices required. Delegate only independent tasks with clear input/output contracts. Summarize findings with file paths and executed checks rather than transcripts of exploration.
