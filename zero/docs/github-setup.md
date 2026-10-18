# Adding Zero to a fork

This overlay contains only new files, so it does not replace the upstream fork's documentation or existing instructions.

1. Extract the package in the **root** of your fork checkout; preserve the directory structure.
2. Review `git status --short`, the new executable `zero/zeroctl.py`, and `.github/workflows/zero-toolkit.yml`.
3. Test `python3 -m unittest discover -s zero/tests -v` locally.
4. Add a link to `ZERO.md` near the beginning of your fork README if desired, without rewriting upstream pages.
5. Commit and push on a separate feature branch, then create a PR. Do not merge until test output and diffs have been reviewed.

Example:

```bash
git switch -c feat/zero-engineering-toolkit
# Extract the overlay archive at the repository root here.
python3 -m unittest discover -s zero/tests -v
git status --short
git add ZERO.md zero .github/workflows/zero-toolkit.yml
git commit -m 'feat: add Zero engineering and token-economy toolkit'
git push -u origin feat/zero-engineering-toolkit
```

This document is not proof that a remote branch or PR exists. Grant a GitHub integration explicit write access to your fork before requesting remote edits.
