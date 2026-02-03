# Contributing

Thanks for your interest in OND-ART CI Pack.

## Quick start

1) Fork the repo and create a feature branch.
2) Install deps and run tests:

```bash
python -m pip install -e .[test]
python -m pytest
```

3) Keep changes focused and update docs/examples when needed.
4) Open a PR with a clear description and any test results.

## Guidelines

- This repo is **diagnostic-only** (no security claims).
- Keep JSON schema changes backward-aware when possible.
- Prefer small, reviewable PRs.

## Reporting issues

Please include:
- What you expected vs what happened
- Steps to reproduce (or a sample report)
- Environment details (Python version, OS)
