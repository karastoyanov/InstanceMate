# Contributing to InstanceMate

## Branching

Branch off `main` using one of these prefixes:

- `feat/` — new functionality
- `fix/` — bug fixes
- `chore/` — tooling, CI, dependencies, repo maintenance

Example: `feat/mcp-incident-lookup`, `fix/oauth-token-refresh`.

## Commit messages

This repo follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <description>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `ci`.

## Pull requests

- Every PR must link an issue (`Closes #123`) using the PR template.
- Fill out the PR template — summary, type of change, and description.
- PRs are merged via **squash merge only**; write your PR title as you'd like it to appear in `main`'s history.
- CI (lint + tests) must pass before merge.
- At least one maintainer approval is required.

## Never commit credentials or real instance data

Do not commit API keys, OAuth secrets, passwords, session tokens, or any data pulled from a real ServiceNow instance (record contents, URLs, logs with identifying info). Use `.env.example` placeholders and sanitized/synthetic data in tests, fixtures, and issue reports.

If you accidentally commit a secret, rotate it immediately and let a maintainer know — do not rely on force-pushing or history rewrites alone.
