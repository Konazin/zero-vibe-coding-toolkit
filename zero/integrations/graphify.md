# Graphify: optional code knowledge graph

Project: https://github.com/Graphify-Labs/graphify

**Optional.** Useful in larger, unfamiliar or highly coupled repositories. For small projects, `rg`, `git grep` and `zeroctl context` are usually cheaper operationally.

## Install (only when authorized)

```bash
uv tool install graphifyy
# or: pipx install graphifyy
graphify --help
```

The package is `graphifyy`, executable is `graphify`. Check installed help/version before using any integration command. `graphify install` may change agent configuration and hooks; review diffs first.

## Local, code-only extraction

```bash
GRAPHIFY_NO_AUTO_REFRESH=1 graphify extract . --code-only --no-cluster
```

Verify supported flags in the pinned version. Code extraction is AST-based locally; documents and semantic extraction may invoke a model or a service. Keep `.graphifyignore` maintained. Exclude `.env*`, personal data, build output, dependencies, test fixtures with secrets and sensitive documents. Do not commit generated `graphify-out/` unless explicitly intended.

## Engineering loop

1. Confirm graph freshness and current commit before relying on it.
2. Ask for call paths, dependencies, public contract reachability or impacted modules.
3. Validate inferred edges in source code; a graph is a navigation index, not a correctness oracle.
4. Use focused source/test reads to verify the resulting hypothesis.
5. Rebuild or refresh after relevant changes, according to installed version's documented command.

An MCP server is optional for repeated queries. Use local stdio before HTTP; never expose the MCP to a public network by default.
