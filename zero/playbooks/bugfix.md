# Bugfix playbook

**Input:** observed behavior, reproduction environment, expected behavior, minimal failing case.

1. Locate symbol, call sites and tests, preferably with `zeroctl context PROJECT -q SYMBOL` or a fresh Graphify graph.
2. Reproduce before changing code, where feasible. Record test/command and the actual failure.
3. Isolate defect without changing unrelated contracts.
4. Add regression case; include negative test when auth/data/errors are involved.
5. Run focused checks, then affected integration/smoke checks using `zeroctl gate`.
6. Review the actual diff. Record PASS/FAIL/NOT RUN and unresolved risks.

Small defects do not require parallel agents or lengthy architectural memos. If investigation reveals system-level risk, escalate to a short plan and separate review.
