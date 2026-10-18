# Zero Vibe Coding Toolkit

**Engineering first. Tokens second. Never trade correctness for compression.**

This is an additive, opt-in engineering layer for the original [Vibe Coding Toolkit](https://github.com/soumatheusgomes/vibe-coding-toolkit). It preserves upstream docs, prompts and templates while adding an auditable workflow for **Codex, Claude Code and other CLI coding agents**.

## Start here

Read **[zero/README.md](zero/README.md)** for the Zero edition and commands.

The Zero edition provides:

- **Read-first context:** bounded local source search to reduce accidental context explosions.
- **Controlled test output:** compact success reporting and actionable failure tails, with full replay on demand.
- **Engineering profiles:** frontend, backend and fullstack contracts; security, testing and release disciplines.
- **Graphify:** optional, local code dependency mapping before edits, without mandatory cloud/model use.
- **RTK:** optional third-party terminal-output reduction. Never implicitly enabled.
- **Benchmark:** real provider token counts **and** acceptance success. An improvement in tokens with failed tests is not a success.
- **Non-destructive onboarding:** preview changes before creating any project instructions; never overwrite existing `AGENTS.md`/`CLAUDE.md`.

## 3-command preview

```bash
python3 zero/zeroctl.py doctor /path/to/project
python3 zero/zeroctl.py init /path/to/project --profile fullstack
python3 zero/zeroctl.py context /path/to/project -q 'SomeSymbol' --scope src
```

For `init`, the default is dry run. Use `--apply` only after review. Zero does not install dependencies, configure credentials, modify git hooks or change LLM provider settings.

## Status and limitations

- The Zero CLI runs with Python 3.10+ and standard library only; test suite uses `unittest`.
- Context filtering and secret heuristics are **not** a confidentiality guarantee. Review content before sending it to a third-party model.
- RTK's compression claims refer to selected command output; Zero does not claim a fixed reduction in total tokens.
- Graphify relationships must be validated against code and tests, especially after commits.
- This layer does not replace the original toolkit, user authorization, professional code review, or real execution evidence.

## Attribution

This fork builds on the upstream Vibe Coding Toolkit under its MIT license. Optional RTK and Graphify are independently maintained projects; Zero does not vendor their binaries, code or trademarks.
