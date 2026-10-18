# Zero Brain v0.2 validation evidence

Evidence is scoped to synthetic temporary vaults/repositories. No personal vault, ZeroCoding
checkout or client configuration was accessed or changed. No global dependencies installed.

Final command outcomes and measured local retrieval results are recorded below after execution.

## Executed checks

Environment: Linux, Python 3.12.14, Node.js 24.19.0.
Base: `9277d458de1c39c1b09e1acd50d9e25f3a29b1ea` (`feat/zero-engineering-toolkit`).

| Check | Outcome | Evidence |
| --- | --- | --- |
| `python3 -m unittest discover -s zero/tests -v` | PASS | 36 tests: all 12 unchanged v0.1 tests + 24 Brain tests; 3.644 seconds |
| `python3 -m py_compile zero/zeroctl.py zero/brain.py zero/brain_store.py zero/brain_capture.py` | PASS | Exit 0 |
| `python3 zero/zeroctl.py brain --help` | PASS | All five commands listed; exit 0 |
| `node --test scripts/validate-docs.test.mjs` | PASS | 9 validator regression tests |
| `node scripts/validate-docs.mjs` | PASS | 618 local links/anchors, destinations and JSON checks at execution |
| `node --test scripts/validate-harness.test.mjs` | PASS | 2 existing evaluator regression tests |
| `git diff --check` | PASS | Exit 0 |
| Python 3.10 and 3.13 locally | NOT RUN | Only Python 3.12 available for this run; workflow now covers 3.10/3.13 |
| Actual Codex/Claude sessions and personal vault | NOT RUN | Opt-in documentation only; no personal access or configuration edits |
| Provider token savings | NOT RUN | No model/provider was invoked |
| Generated Next.js app and ESLint runtime checks | NOT RUN | No application/template/runtime changes in this iteration |

Negative tests cover path escape, symlinks, missing/invalid metadata, unreadable/oversized
notes, absent Git sources, byte budgets, redaction, invalid approval, changed/deleted notes,
tampered drafts, unsafe draft destinations, recovery-copy preservation and malformed Markdown.
Read-only commands are checked against file snapshots, including unregistered invalid UTF-8
notes to prove they are not read. Capture tests assert no vault mutation before approval,
original-body retention, private artifact permissions and recovery content.

## Reproducible retrieval microbenchmark

Command: `python3 zero/tests/benchmark_brain.py` (exit 0).
The script creates/removes a synthetic temporary vault and invokes the real CLI 20 times.

| Measurement | Observed |
| --- | --- |
| Source note | 77,897 bytes; 1,000 decision lines plus heading |
| Retrieval budget proxy | 2,000 UTF-8 bytes |
| Retrieved records, including provenance | 1,940 bytes |
| Total stdout, including summary | 2,101 bytes |
| Median complete CLI process time | 46.50 ms |
| Maximum complete CLI process time | 54.87 ms |
| Omitted matches | Yes; `truncated: true` |

These are local byte and wall-clock observations, not billing tokens, accepted-task quality,
a cold-disk benchmark or a guarantee of end-to-end session savings. Repeat on the intended
machine before comparing latency. Retrieval still scans the single bounded registered note.

## Residual limits and recovery

SHA freshness does not detect uncommitted work. Matching source revisions do not validate
note claims. Secret detection is heuristic. Markdown verification is partial and never repairs
content. Human approval is an agent/user policy; a hash only binds content. A noncooperating
writer can race final replacement; use a quiet vault during approval. Existing notes have a
private backup before replacement. No live integration, independent reviewer or personal-data
migration was exercised. Full contracts: [Zero Brain](brain-v0.2.md).
