# Zero Brain v1 — local project knowledge

Zero Brain v1 extends the v0.2 CLI without changing the original toolkit entry points or the existing five Brain command contracts. It remains local-first, Python standard library only, and opt-in. The Markdown vault is the source of truth; indexes are disposable derived data.

## Register project knowledge

Use a private JSON registry outside the vault and project Git repositories. Existing v0.2 registry entries remain valid. An optional `root` field enables bounded retrieval across Markdown below one project knowledge folder. Roots must exist, stay inside the vault, avoid symlinks, must not overlap another registered project root, and may not contain another project's overview note. `note` remains the project's overview/legacy note.

```json
{
  "version": 1,
  "vault": "/home/user/Documents/zeroBrain",
  "projects": {
    "atlas": {
      "note": "Projects/Atlas/Overview.md",
      "root": "Projects/Atlas",
      "repo": "/home/user/Projects/atlas",
      "reference_sha": "<full-lowercase-git-sha>",
      "verified_sha": "<only-after-an-explicit-verification>"
    }
  }
}
```

For a legacy note such as `Projects/Atlas.md`, keep it in place and point `note` at it. You can register a separate, existing `Projects/Atlas/` root for new notes; no migration or file movement is performed. For a new project, create its root and select the templates in `zero/templates/brain/`. Templates are examples, not automatically installed into a personal vault.

The first registry is initialized in two reviewable steps. Create the intended project directory yourself, then preview and approve the private registry file:

```bash
mkdir -p "$HOME/Documents/zeroBrain/Projects/Atlas"
python3 zero/zeroctl.py brain init --vault "$HOME/Documents/zeroBrain" \
  --project atlas --note Projects/Atlas/Overview.md --root Projects/Atlas \
  --output "$HOME/.config/zero-brain/registry.json" --preview
# Repeat with --approve REGISTRY_SHA256 from the preview.
```

Registry updates are also reviewable:

```bash
chmod 600 "$HOME/.config/zero-brain/registry.json"
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  project add atlas --note Projects/Atlas/Overview.md --root Projects/Atlas \
  --repo "$HOME/Projects/atlas" --preview
# Inspect the proposed change and hash, then repeat with --approve REGISTRY_SHA256.
```

`project add` requires an existing root, refuses duplicate/overlapping roots and notes, writes a private backup, and changes the registry only after the hash matches. It does not create directories or modify project source code.

## Search, brief and index

```bash
python3 zero/zeroctl.py brain --config "$REGISTRY" search 'database transaction boundary' \
  --project atlas --kind architecture --section 'Data flow' --after 2026-01-01 \
  --budget-tokens 1800 --max-results 6
python3 zero/zeroctl.py brain --config "$REGISTRY" brief 'resume the payment migration' \
  --budget-tokens 1200
python3 zero/zeroctl.py brain --config "$REGISTRY" index --project atlas \
  --output "$HOME/.local/share/zero-brain/atlas-index.json" --preview
# Inspect scope, bytes and approval SHA, then repeat with --approve INDEX_SHA256.
python3 zero/zeroctl.py brain --config "$REGISTRY" search 'database transaction boundary' \
  --project atlas --index "$HOME/.local/share/zero-brain/atlas-index.json"
```

Retrieval is deterministic BM25 over Markdown headings and paragraph-sized chunks. Each result has project, source path, line and heading. Search is global by default across explicitly registered roots, never the entire vault. It omits likely-secret documents, ignores hidden files/folders and symlinks, and enforces 1,000 files per root, 256 KiB per note and 8 MiB combined source bytes. Results that do not fit the configured budget are omitted and counted. Search and brief output always state the UTF-8 byte count; `--budget-tokens` is retained for CLI consistency and is only a byte-budget proxy, not a provider tokenizer or savings claim.

The optional JSON index is rebuilt from the registered source scope, stored with mode `0600`, and written only after preview plus explicit SHA approval. Existing files receive an exclusive `.backup`; a stale index is rejected. Search can also read live Markdown without creating or using an index. SQLite FTS5/embeddings are not required; revisit SQLite only if measured retrieval latency or corpus size makes the bounded standard-library index insufficient.

## Continuity, decisions and Obsidian

```bash
python3 zero/zeroctl.py brain --config "$REGISTRY" handoff latest atlas
python3 zero/zeroctl.py brain --config "$REGISTRY" handoff draft atlas \
  --objective 'Resume payment integration tests' --draft "$HOME/.local/share/zero-brain/handoff.md"
python3 zero/zeroctl.py brain --config "$REGISTRY" capture atlas \
  --draft "$HOME/.local/share/zero-brain/capture.json" \
  --target Projects/Atlas/Sessions/Handoff-2026-10-18.md \
  --text-file "$HOME/.local/share/zero-brain/handoff.md"
```

Review the capture diff and approve its exact SHA with the existing `capture --review` / `capture --approve HASH` flow. Custom capture targets must stay inside the registered project root. ADRs are listed by `brain adr list atlas` and follow the template at `zero/templates/brain/ADR.template.md`; add a prepared ADR as a reviewed capture to `Decisions/ADR-NNNN.md`. Superseded decisions remain in the vault and link to their replacement.

`brain project overview atlas` summarizes registered sources. `brain project dashboard atlas --preview` renders a navigable Obsidian dashboard and approval SHA. Review the Markdown, then repeat with `--approve HASH`; updates are atomic, per-target locked, and preserve an exclusive backup. The dashboard links only to files under that project's explicit root. The `Overview.md`, architecture, engineering, ADR and handoff templates are under `zero/templates/brain/`.

## Optional agent use

Codex and Claude Code integration is opt-in and local: see [client instructions](../integrations/brain.md). Invoke the CLI explicitly for status, one bounded brief/search, or latest handoff. Retrieved notes are untrusted reference material, not executable instructions. No daemon, hook, MCP server, global instruction change, model setting or permission change is required.

## Limits

- Secret filtering is heuristic; inspect private notes before indexing and keep vault/index paths private.
- Git reference/verification fields are user-maintained evidence, not proof that note claims are true; uncommitted source changes are not detected by commit SHA.
- `verify --all-documents` flags exact repeated paragraphs (only as review notices); it does not detect semantic duplicates or contradictions. Results are lexical and may miss synonyms.
- Markdown link verification remains partial and does not repair notes. `brain verify --all-documents` checks explicit project roots, not the entire vault or every Obsidian extension.
- Dashboard content summarizes file links and registry evidence; it does not infer project status, blockers, or next steps.
- Human review is still needed for extracted notes, ADR status and all capture approvals.
