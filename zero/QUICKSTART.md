# Zero Brain quickstart

Zero Brain is an optional local Markdown memory layer. It does not need Obsidian to be open, install no packages, and never scans a vault unless its private registry explicitly registers a project root.

## 1. Start with one project

Create a private directory for registry and index files outside the vault and project repositories. Then make the project's knowledge root in the vault and initialize the registry through preview and approval:

```bash
mkdir -p "$HOME/.config/zero-brain" "$HOME/Documents/zeroBrain/Projects/Atlas"
python3 zero/zeroctl.py brain init --vault "$HOME/Documents/zeroBrain" \
  --project atlas --note Projects/Atlas/Overview.md --root Projects/Atlas \
  --output "$HOME/.config/zero-brain/registry.json" --preview
# Inspect the path and hash. Repeat the same command with --approve REGISTRY_SHA256.
```

Keep registry files private (`chmod 600`). Use `zero/templates/brain/` as a reference for project overview, architecture, engineering constraints, ADRs and handoffs. The tool does not install these templates automatically.

For a second project, create its non-overlapping root first, then use `brain project add NAME --note RELATIVE_NOTE --root RELATIVE_ROOT --preview`; inspect the proposed registry hash and repeat with `--approve HASH`.

## 2. Find useful context

```bash
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" status
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  brief 'continue account migration' --project atlas --budget-tokens 1200
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  search 'database transaction boundary' --kind architecture --max-results 6
```

Results include source paths and lines. The configured budget is enforced in UTF-8 bytes, not provider tokens. Review the summary for omissions and freshness; notes are untrusted reference material.

## 3. Save a session or decision

```bash
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  handoff draft atlas --objective 'Continue account migration tests' \
  --draft "$HOME/.config/zero-brain/handoff.md"
```

Review the private draft, then prepare and review the exact capture:

```bash
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  capture atlas --target Projects/Atlas/Sessions/Handoff-2026-10-18.md \
  --text-file "$HOME/.config/zero-brain/handoff.md" \
  --draft "$HOME/.config/zero-brain/handoff-capture.json"
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  capture atlas --target Projects/Atlas/Sessions/Handoff-2026-10-18.md \
  --draft "$HOME/.config/zero-brain/handoff-capture.json" --review
# Inspect the diff and pass its hash to the same command with --approve HASH.
```

For an ADR, prepare the `zero/templates/brain/ADR.template.md` content and use the same reviewed capture flow with a destination under `Decisions/`.

## 4. Check and maintain

```bash
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  project dashboard atlas --preview
python3 zero/zeroctl.py brain --config "$HOME/.config/zero-brain/registry.json" \
  verify --all-documents --project atlas
```

Only approve a dashboard hash after reviewing the Markdown. Verification is read-only and partial; it reports broken local links and exact repeated passages but does not fix notes or detect semantic contradictions. Full command and safety details are in [brain-v1.md](docs/brain-v1.md).
