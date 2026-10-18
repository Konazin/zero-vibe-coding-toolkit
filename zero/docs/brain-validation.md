# Zero Brain v0.2 validation evidence

Evidence is scoped to synthetic temporary vaults/repositories. No personal vault, ZeroCoding
checkout or client configuration was accessed or changed. No global dependencies installed.

Final command outcomes and measured local retrieval results are recorded below after execution.

## Corrective review evidence

The corrective review adds per-note capture locking, separate filesystem mtime/reference/verified commit reporting, Obsidian-style wikilink resolution with ambiguity notices, and header-free support for legacy notes. A two-process race test approves two captures against the same original note: exactly one succeeds and the other reports a stale base. They are never silently collapsed into one write.

## Executed checks

Environment: Linux, Node.js 24.19.0. CPython 3.10.22 and 3.13.16 were installed under /tmp for isolated version-specific test runs; Python 3.12.14 is also available in the host runtime.
Base: `9277d458de1c39c1b09e1acd50d9e25f3a29b1ea` (`feat/zero-engineering-toolkit`).

| Check | Outcome | Evidence |
| --- | --- | --- |
| CPython 3.10.22 unittest suite | PASS | 40 tests: 12 v0.1 and 28 Brain contracts; 4.921 seconds |
| CPython 3.13.16 unittest suite | PASS | Same 40 tests; 5.028 seconds |
| Concurrent capture regression | PASS | Two approved processes against same source; one commits, one explicit conflict |
| Legacy note regressions | PASS | status/verify work without metadata; capture retains original bytes and adds no header |
| Obsidian wikilink regressions | PASS | basename, folder path, aliases, headings, attachments and ambiguity |
| `python3 -m py_compile zero/zeroctl.py zero/brain.py zero/brain_store.py zero/brain_capture.py` | PASS | Exit 0 |
| `python3 zero/zeroctl.py brain --help` | PASS | All five commands listed; exit 0 |
| `node --test scripts/validate-docs.test.mjs` | PASS | 9 validator regression tests |
| `node scripts/validate-docs.mjs` | PASS | local links/anchors, destinations and JSON checks at execution |
| `node --test scripts/validate-harness.test.mjs` | PASS | 2 existing evaluator regression tests |
| `git diff --check` | PASS | Exit 0 |
| Python 3.12 additional run | NOT RUN | Full matrix requested and passed on 3.10 and 3.13 |
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

## v1 foundation evidence

The v1 extension adds private registry initialization/update, scoped project roots,
BM25 Markdown retrieval, task briefs, an explicitly approved rebuildable JSON index,
Obsidian dashboard preview/update, ADR listing, handoff draft/recovery, custom capture
targets, and read-only root-wide link/duplicate-passage checks. Integration tests use
temporary vaults and registries. This is a functional v1 foundation; known gaps are
listed in `brain-v1.md` and should be reviewed before calling it a complete personal
knowledge system.

Retrieval benchmark command: `python3 zero/tests/benchmark_brain_v1.py`.

| Measurement | Observed on this run |
| --- | --- |
| Runtime | CPython 3.12.14, Linux x86_64 |
| Synthetic questions | 2, 5 repeated process runs each |
| Expected source coverage | 100% on both fixture queries (4/4 expected sources) |
| Irrelevant retrieved sources | 0 |
| Median complete search process | 41.36 ms across 10 runs |
| Retrieved context | 326 and 294 UTF-8 bytes for the two cases |
| Omitted matches | 0 in these small fixtures |
| Provider token counts / task quality | NOT RUN; no provider was invoked |

This corpus has five notes, two hand-written queries and exact expected file paths.
It is a smoke benchmark, not evidence of general semantic quality, large-vault
performance, real token savings, or usefulness in the user's personal vault.
