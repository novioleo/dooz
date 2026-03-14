# Contributor Guide

Thank you for your interest in contributing to dooz!

## How to Contribute

### Reporting Bugs

1. Search existing issues to avoid duplicates
2. Use the bug report template
3. Include reproduction steps and environment details

### Suggesting Features

1. Open a discussion first to gauge interest
2. Use the feature request template
3. Explain the use case and expected behavior

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following our code standards
4. Write tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

## Code Standards

All code must follow:

- **Modular Design** — Single responsibility, clear interfaces
- **Functional Approach** — Pure functions, immutability
- **Error Handling** — Graceful errors with context
- **Security** — No hardcoded secrets

See `.opencode/context/core/standards/code-quality.md` for details.

## Development Setup

See the root [README.md](../README.md) for setup instructions.

## Commit Messages

Use conventional commits:

```
feat: add new device discovery algorithm
fix: resolve brain election race condition
docs: update API documentation
refactor: simplify message transport logic
test: add unit tests for discovery service
```

## Review Process

1. Maintainers review within 48 hours
2. Address feedback promptly
3. Once approved, a maintainer will merge

## Code of Conduct

Be respectful and inclusive. See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## Questions?

Open a discussion or join our community chat.
