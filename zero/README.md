# Zero engineering layer

Portable, opt-in workflows that optimize for **correct, reviewed, tested software per token**. Python 3.10+ is sufficient for the included CLI. Original toolkit entry points remain intact.

## Install and use

In your fork checkout:

```bash
python3 zero/zeroctl.py --help
python3 -m unittest discover -s zero/tests -v
```

To bring Zero instructions into an **existing project** without breaking its conventions:

```bash
PROJECT="$HOME/Projects/ZeroCoding" # change to actual path
python3 zero/zeroctl.py doctor "$PROJECT"
python3 zero/zeroctl.py init "$PROJECT" --profile backend
python3 zero/zeroctl.py init "$PROJECT" --profile backend --apply
```

`init` never overwrites files. When an existing AGENTS.md is present, review `.zero/ZERO_RULES.md` and merge into existing instructions manually. CLAUDE.md is created only if absent and imports AGENTS.md. Per-project profile lives in `.zero/PROFILE.md`. This is not a plugin marketplace installer.

**Fast, bounded investigation:**

```bash
python3 zero/zeroctl.py context "$PROJECT" -q 'ConfigManager' --scope src --budget-bytes 12000
```

Reads likely source files and prints `path:line` snippets, bounded to a byte budget. Honors Git tracking/ignore rules when possible and skips common secrets and generated directories. Secret heuristics are not security guarantees. Unfamiliar modules can benefit from Graphify; see integration below.

**Quality gate with explicit command:**

```bash
python3 zero/zeroctl.py gate "$PROJECT" -- python3 -m pytest -q
python3 zero/zeroctl.py gate --full "$PROJECT" -- python3 -m pytest -q
```

Run the exact supported project command. On success, print a compact summary. On failure, show a bounded tail and preserve the command's exit status. `--full` displays all output for diagnosis. Bash pipe-based truncation (`| tail`) often hides real failure status and is intentionally avoided. No command is auto-detected or automatically executed.

**Compare actual token data:**

```bash
python3 zero/zeroctl.py metrics zero/examples/benchmark.schema-example.json
```

Replace example numbers with provider-reported input/output tokens and acceptance-test results from matched tasks; this example is synthetic. An observed quality regression yields exit code 2. See [benchmark protocol](docs/benchmark.md).

## Zero Brain v0.2

Optional local Markdown memory extends the existing CLI with `brain status`, `recall`,
`capture`, `switch` and `verify`. Use an explicit private registry; capture requires
preparation, diff review and approval before writing. No personal notes are bundled.
See the [command and safety contract](docs/brain-v0.2.md),
[optional Codex/Claude integration](integrations/brain.md) and
[validation evidence](docs/brain-validation.md).

## Engineering modules

| Module | What to use |
| --- | --- |
| [Frontend](profiles/frontend.md) | Accessibility, Vue/React state, responsive UI, error states, smoke and build |
| [Backend](profiles/backend.md) | Spring/Python/Node APIs, permissions, persistence, schema and contract tests |
| [Fullstack](profiles/fullstack.md) | Cross-layer contracts, rollout and full journey |
| [Engineering](policies/engineering.md) | Reproduction, smallest change, risk-adjusted gates and evidence |
| [Security](policies/security.md) | Authz, secrets, threat modeling, least privilege |
| [Token economy](policies/token-economy.md) | Retrieval budgets, output strategy, delegation thresholds |
| [Graphify](integrations/graphify.md) | Optional AST-based knowledge graph and impact queries |
| [RTK](integrations/rtk.md) | Optional, verified third-party command output proxy |
| [Context7](integrations/context7.md) | Optional versioned API reference with minimal retrieval |
| [Browser smoke](integrations/browser-tests.md) | Optional browser-based behavior and accessibility checks |
| [Feature](playbooks/feature.md) | Scoped design through rollout |
| [Bugfix](playbooks/bugfix.md) | Reproduction, regression and diagnostic loop |
| [Review](playbooks/review.md) | Independent review with evidence |
| [Architecture](playbooks/architecture.md) | ADRs, constraints, and trade-off analysis |
| [Harness evaluation](playbooks/harness-evaluation.md) | Deterministic agent behavior and budget evaluation |
| [Frontend delivery](playbooks/frontend-delivery.md) | Concrete gates and accessibility checklist |
| [Backend delivery](playbooks/backend-delivery.md) | Concrete gates and security/transaction checklist |

## Architecture

Three layers deliberately stay separate:

1. **Agent instructions:** minimal `AGENTS.md`, imported into `CLAUDE.md`. The agent knows policies without loading every guide.
2. **On-demand procedures:** profiles, playbooks and Graphify indexes are loaded only for relevant task types.
3. **Deterministic evidence:** `zeroctl` verifies structure, limits exploration, executes explicit quality commands and compares provider measurements.

No automatic subagents, always-on MCPs, hidden hooks, cloud embeddings, global model overrides or blocking git hooks. Optional integrations require user approval and independent version verification.

## What quality means

- **PASS:** exact command was executed, its exit code was 0, and it verifies the stated behavior.
- **FAIL:** command failed or an acceptance criterion was violated. Preserve diagnostic output.
- **NOT RUN:** command could not run, is not configured, or behavior was not checked. Never promote this to PASS.

Quality gates should be proportionate to risk: a CSS typo and a database schema migration are not the same kind of change.

## Safety and contribution

Never pipe unreviewed remote install scripts to a shell. Avoid sending private files to external LLMs. This layer is additive and should not modify upstream files while syncing the original toolkit. CI runs only local Zero unit tests; validation of generated apps, model behavior and external integrations requires separate execution.
