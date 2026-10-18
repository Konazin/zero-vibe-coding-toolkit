# Software engineering policy

**Goal:** maximize verified correct changes per unit of time and tokens, not maximize code written.

## Change protocol

1. State current behavior, target behavior, scope, risks and what would disprove the proposed fix.
2. Locate owners/consumers via focused search or graph. Identify source-of-truth contracts.
3. Reproduce the bug or establish a failing test if feasible; do not manufacture a failure.
4. Implement the smallest coherent change with correct layering and error handling.
5. Run tests that demonstrate the touched behavior; add negative and regression cases proportional to risk.
6. Inspect the diff for unrelated churn, security, API and migration changes.
7. Report PASS/FAIL/NOT RUN, exact commands, residual risks and user-visible effects.

## Risk levels

- Low: small local cosmetic/text edit. Focused check and review, no ceremony.
- Medium: component logic or isolated business behavior. Focused tests, lint/type checks, affected contract tests.
- High: authentication, billing, migrations, public APIs, concurrency, data loss, permissions. Explicit plan, negative tests, independent review, and rollback analysis.

No automatic branch, commit, push, destructive command, dependency install, new MCP, or provider change. Ask for authorization when needed. Agents are not a replacement for engineers reviewing the design.
