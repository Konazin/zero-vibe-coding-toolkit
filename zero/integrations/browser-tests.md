# Browser testing: opt-in frontend verification

A CLI/browser automation tool (Playwright, agent-browser or equivalent) can validate user journeys in a real browser when the project already has a working test environment.

- Test page load, keyboard access, error/empty/loading states, mobile/desktop layout, navigation and API failure handling.
- Use disposable test accounts, fixture data and a local/staging instance. Do not run destructive flows against production.
- Keep screenshots, traces and videos out of LLM context unless there is a specific diagnostic need.
- Preserve full failure artifacts locally; summarize pass/fail and relevant steps to the agent.
- Do not treat a visually correct screenshot as proof of accessibility, authorization or persisted state.

Install dependencies only when approved and compatible with the project's browser/test setup.
