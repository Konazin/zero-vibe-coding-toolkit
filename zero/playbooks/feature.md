# Feature engineering playbook

**Inputs:** acceptance criteria, current contracts, constraints, rollout, reversibility.

1. Write a scoped design: impacted modules, public APIs, persistence, permissions and failure states.
2. Map dependencies and integration points. Confirm ownership in code.
3. Split into atomic, testable increments. Delegate only independent pieces with defined interfaces.
4. Implement with tests and operational checks proportionate to risk.
5. Run frontend/backend/contract gates applicable to the feature.
6. Compare diff to acceptance criteria, record migration/rollback and remaining risk.

For medium/high-risk work, review design assumptions before large edits. Do not let the planning process become a substitute for implementing and testing.
