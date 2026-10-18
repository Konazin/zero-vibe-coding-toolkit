# Independent review playbook

Reviewer receives the problem statement, acceptance criteria, diff and test evidence. Do not blindly inherit the implementer's assertion of PASS.

Check correctness, authorization, error handling, state transitions, persistence, concurrency, accessibility, API compatibility, test validity and unrelated churn as applicable.

Provide findings ranked P0 (critical) to P3 (minor). Include exact file/symbol and a concrete failure scenario. Do not invent bugs or ask for unrelated architecture cleanup. Report important uncertainty and unrun verification separately. Prefer review-only mode; do not modify files unless explicitly tasked.
