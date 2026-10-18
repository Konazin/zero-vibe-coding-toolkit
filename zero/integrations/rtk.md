# RTK: optional terminal output compression

Project: https://github.com/rtk-ai/rtk

RTK is a separate public project, **not bundled or automatically installed** by Zero. Use a vetted installation method documented by its maintainers and verify binary provenance/version. Do not run opaque installer scripts through an agent without reviewing them.

## Adoption policy

- Compare output from a few known noisy commands with and without RTK first.
- Ensure exit codes, stack traces and stderr failures remain discoverable.
- Start with read-only commands, then expand to tests/build only after verifying failure reporting.
- Prefer official shell/agent integration when supported, rather than globally intercepting all processes with unknown wrappers.
- On unexplained failures or missing diagnostics, rerun the original command uncompressed.
- Track provider-reported tokens per completed task; RTK's claimed compression of *command output* is not equivalent to total session savings.

For projects lacking RTK, Zero's `gate` command provides a dependency-free alternative for explicit commands (not an RTK replacement).
