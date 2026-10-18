# Token economy without quality loss

The optimization target is **successful, regression-free task completion per token**, not the shortest response. Compression that removes errors can increase total cost.

## Four levers

1. **Retrieval:** inspect filenames, symbols and relevant slices before broad reads. Use `zeroctl context` with a scope and output budget. Use Graphify for dependency exploration if a maintained graph exists.
2. **Tool output:** prefer RTK for supported noisy commands after checking its behavior. `zeroctl gate` prints minimal PASS, bounded error output on FAIL; rerun `--full` for complete diagnostics.
3. **Interaction:** short status, precise evidence. Avoid repeated restatement of project instructions, speculative designs, filler, and subagents for straightforward work.
4. **Reuse:** store short decisions and validated commands in project docs; periodically remove stale context. Cache only non-sensitive, versioned artifacts.

## Escalation rule

Start with limited context. Escalate if evidence is insufficient, contradiction appears, or tests fail. Never truncate a stack trace before identifying the root cause. Do not omit required security, accessibility or cross-layer tests.

## Benchmark discipline

Compare the same task corpus, model, versions, environment, quality gates and number of retries. Record provider-reported input and output tokens, completion success, test failures and human rework. Analyze cost per accepted change. The toolkit itself makes no guaranteed percentage savings.

## Confidentiality

`context` applies a denylist and redacts possible assignments, but this is **not** a DLP boundary. Always review data before sending it to an external model. Do not submit secrets or private customer data to Graphify cloud/MCP without authorization.
