# Contributing to Vectaris

Thanks for your interest in contributing. This document covers the conventions
this project follows so that pull requests are easy to review and merge.

## Getting Set Up

1. Fork and clone the repository.
2. Run the bootstrap script:
   - macOS / Linux: `./run-local.sh`
   - Windows: `run-local.bat`
3. Or follow the manual instructions in [README.md](README.md).

## Branch & Commit Conventions

- Branch names: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`, `chore/<short-name>`.
- Commit messages: Conventional Commits format.
  - `feat(backend): add cost forecast endpoint`
  - `fix(frontend): handle empty agent list`
  - `chore(ci): cache npm modules`
- Keep commits focused. Squash WIP commits before opening a PR.

## Pull Requests

Before opening a PR, please make sure:

- [ ] Backend tests pass: `cd backend && pytest`
- [ ] Frontend lint passes: `cd frontend && npm run lint`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Documentation is updated for any new public behavior
- [ ] No secrets, API keys, or PII are committed

PRs that touch architecture or public APIs should link to or include an
ARCHITECTURE.md update.

## Code Style

| Area | Tooling |
|------|---------|
| Python | `ruff` (lint), `mypy --ignore-missing-imports` (types) |
| TypeScript | `eslint` with `@typescript-eslint` and `react-hooks` |
| Markdown | Soft wrap; tables for any structured information |

## Reporting Bugs

Open an issue using the bug template (see [ISSUES.md](ISSUES.md)) and include:

- Steps to reproduce
- Expected vs. actual behavior
- Backend / browser version
- Relevant logs (with `request_id` if available)

## Security Issues

Please **do not** open public issues for security vulnerabilities. Follow
[SECURITY.md](SECURITY.md) for the disclosure process.

## License

By contributing, you agree that your contributions will be licensed under
the MIT License (see [LICENSE](LICENSE)).
