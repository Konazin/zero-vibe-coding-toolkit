# Frontend engineering profile

Use for Vue 3/Vite/Tailwind, React/Next, and browser-facing applications. Prefer the existing framework and design system. Never introduce a UI library merely because an agent knows it.

## Design contract

- Define user states first: initial, loading, empty, success, validation, network failure, and unauthorized.
- Preserve keyboard access, focus flow, semantic markup, readable contrast, and reduced-motion preferences.
- Keep UI state local when practical. Do not create global stores for trivial component state.
- Reuse existing tokens, spacing scales, components, routing, error boundaries, and API clients.
- Test responsive layouts at the project's supported viewport sizes. Screenshots prove appearance, not semantics or behavior.
- Treat frontend authorization checks as UX only; enforce access in the backend.

## Delivery gates

- Typecheck and lint as supported; unit/component tests for behavior, E2E browser smoke for critical journeys, production build.
- Verify at least one error state, keyboard behavior, and responsive behavior for changed UI.
- Avoid shipping stale mock data or tests that assert only component rendering.
- Detect bundle/performance regressions when modifying routes or dependencies.

## Context budget

Read target component and its public interface first, then consumers, stores, styles and tests. Query Graphify for ownership and call paths when available. Avoid dumping full src trees, bundler output, minified files, or screenshots as default context.
