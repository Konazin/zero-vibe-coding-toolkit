# Architecture and design review playbook

For high-risk or cross-module changes, separate architectural decisions from code generation.

## Input

Observed need, boundaries, quality attributes, existing ADRs, current runtime, deployment and compatibility constraints.

## Procedure

1. Reconstruct current boundaries from source/contracts and, optionally, a verified Graphify graph.
2. Define invariants, performance/security requirements, data ownership, APIs and failure models.
3. Compare a minimal change against two alternatives; quantify migration/deployment burden and likely testing cost.
4. Record a concise ADR with the chosen trade-off, rejected alternatives and reversibility.
5. Implement the smallest vertical slice and verify using integration tests.

**Avoid architecture theater:** do not add abstractions, events, microservices, queues, repositories or dependency injection only to make a diagram look impressive. Prefer an existing modular monolith where it meets scaling and ownership needs.
