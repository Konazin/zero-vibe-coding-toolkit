# Agent harness evaluation

The base toolkit already contains deterministic harness fixtures and evaluation documentation. Reuse them rather than inventing a new benchmark that rewards a specific agent's wording.

## Contract

- Freeze scenario, reference commit, permissions and test execution environment.
- Include correct behavior, contract violation, malicious/inaccurate instruction, stale handoff and file-scope boundaries.
- Instruct the candidate agent to fix the behavior, but never show it hidden test outputs.
- Keep the evaluator independent. Do not edit fixtures to make the solution pass.
- Report actual exit status, unit/contract tests and human-review findings.
- Compare the **same** task with and without economy profile and record total provider tokens, attempts, and accepted outcome.

If the reduced-context agent misses a contract or a security bug, it lost. Even if token counts were lower.

Upstream references: `docs/07-harness-evaluation.md`, `scripts/validate-harness.mjs`, `templates/harness-evaluation/`.
