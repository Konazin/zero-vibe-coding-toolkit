# Empirical evaluation protocol

Do not advertise an arbitrary reduction in tokens as an outcome. Compare **identical tasks** with two controlled configurations.

1. Select at least 10 representative tasks: frontend errors, backend bugs, security fixes, architecture investigation, UI smoke and refactoring.
2. Freeze model, client version, repo snapshot, dependencies, test harness and acceptance criteria.
3. Run baseline (toolkit disabled) and candidate (toolkit enabled) independently; avoid cross-run learning and cached context asymmetry.
4. Capture provider-reported input/output tokens, time, attempts, passed acceptance tests, reviewer defects, and human rework.
5. Fill `zero/examples/benchmark.schema-example.json` with **real measurements**, then run `python3 zero/zeroctl.py metrics your-results.json`.
6. Report matched task quality, acceptance ratio and total tokens per successful outcome. Reject savings claims when quality regresses.

A `metrics` exit status of 2 means quality regression or invalid input, not a successful benchmark. The example JSON is synthetic and must not be presented as a real result.
