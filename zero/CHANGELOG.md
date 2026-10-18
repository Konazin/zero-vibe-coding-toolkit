# Changelog

## 1.0.0 review candidate

- Added explicitly registered project roots, private registry initialization and reviewed project registration.
- Added deterministic BM25 search and task briefs with project, knowledge-type, section, date and output-budget filters.
- Added an optional rebuildable private index with source hashes and staleness checks.
- Added Obsidian-compatible architecture/engineering/ADR/handoff templates and an approved project dashboard.
- Added handoff drafting/recovery, ADR listing, approved capture destinations and bounded `verify --all-documents` checks.
- Kept the existing v0.2 commands and Python 3.10+ standard-library runtime.
- Added temporary-vault regression tests and a synthetic retrieval benchmark.

This is a review candidate, not evidence of semantic retrieval, provider-token savings, contradiction detection, or validation against a personal vault. See [known limits](docs/brain-v1.md#limits) and [validation evidence](docs/brain-validation.md).
