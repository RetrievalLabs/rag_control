---
title: Contributing Guide
description: How to contribute to rag_control
---

# Contributing to rag_control

We welcome contributions from the community! This guide explains how to contribute.

## Code of Conduct

We're committed to providing a welcoming and inspiring community for all.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported
2. Open a [GitHub issue](https://github.com/RetrievalLabs/rag_control/issues)
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs. actual behavior
   - Python version, OS, and relevant versions

### Suggesting Enhancements

1. Check if the feature has been suggested
2. Open a [GitHub issue](https://github.com/RetrievalLabs/rag_control/issues)
3. Include:
   - Clear description of the enhancement
   - Use cases and motivation
   - Possible implementation approach

### Submitting Pull Requests

**Important**: We only accept PRs from RetrievalLabs team members. Community feedback through issues is welcome!

For team members contributing code:

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes:
   - Follow code standards (see below)
   - Add tests for new functionality
   - Update documentation

3. Run quality checks:
   ```bash
   # Tests
   pytest --cov=rag_control

   # Type checking
   mypy --strict rag_control

   # Linting
   ruff check rag_control

   # Formatting
   black rag_control
   ```

4. Commit with clear messages:
   ```bash
   git commit -m "feat: add new policy enforcement rule"
   ```

5. Push and open a PR:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Standards

### Testing

- **Minimum coverage**: 80%
- **Target coverage**: 100%
- All new features must include tests

### Type Checking

- Must pass `mypy --strict`
- Use type hints for all functions
- No `any` types

### Formatting

- Must pass `black` formatting
- Must pass `ruff` linting

### Documentation

- Update README if adding features
- Update docstrings
- Add examples for complex features

## Commit Messages

Follow conventional commits:

```
feat: add new feature
fix: fix a bug
docs: update documentation
test: add tests
refactor: refactor code
chore: maintenance tasks
```

Example:

```
feat: implement streaming response support

Add support for streaming responses from LLM adapters.
Includes proper token counting and enforcement.

Fixes #123
```

## Documentation

### Adding to Docs

1. Add markdown file to `docs/docs/`
2. Update `docs/sidebars.js` to include new page
3. Build locally to verify:
   ```bash
   cd docs
   npm install
   npm start
   ```

### Documentation Standards

- Clear, concise language
- Code examples where appropriate
- Links to related documentation
- Explain the "why" not just the "what"

## Pull Request Review

Your PR will be reviewed for:

- ✅ Code quality and standards compliance
- ✅ Test coverage (80%+ required)
- ✅ Type safety (mypy strict)
- ✅ Documentation
- ✅ Design and architecture

## Release Process

Releases are managed by the RetrievalLabs team and follow semantic versioning:

- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes

## Questions?

- Check [Documentation](/)
- Open a [GitHub discussion](https://github.com/RetrievalLabs/rag_control/discussions)
- Review [Examples](https://github.com/RetrievalLabs/rag_control/tree/main/examples)

## License

By contributing, you agree that your contributions will be licensed under the same license as rag_control (RBRL).

## Acknowledgments

Thank you for contributing to rag_control and helping make it better!

---

See [LICENSE](https://github.com/RetrievalLabs/rag_control/blob/main/LICENSE) for full license terms.
