# Contributing to colabsh

Thank you for your interest in contributing to colabsh! This guide will help you
get started.

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

### Getting Started

```bash
# Clone the repository
git clone https://github.com/onuralpszr/colabsh.git
cd colabsh

# Install dependencies (including dev group)
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install
```

## Development Workflow

### Running Tests

```bash
# Run full test suite with coverage
uv run pytest

# Run a specific test file
uv run pytest tests/test_config.py

# Run tests without coverage
uv run pytest --no-cov
```

### Linting & Formatting

```bash
# Lint
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Format
uv run ruff format .

# Type check
uv run mypy src/
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run them manually:

```bash
uv run pre-commit run --all-files
```

## Commit Messages

This project follows
[Conventional Commits](https://www.conventionalcommits.org/). Changelog
generation with [git-cliff](https://git-cliff.org/) depends on this format.

### Format

```
<type>(<scope>): <description>
```

### Types

| Type       | Description                          |
| ---------- | ------------------------------------ |
| `feat`     | A new feature                        |
| `fix`      | A bug fix                            |
| `docs`     | Documentation changes                |
| `style`    | Code style changes (formatting, etc) |
| `refactor` | Code refactoring                     |
| `perf`     | Performance improvements             |
| `test`     | Adding or updating tests             |
| `chore`    | Maintenance tasks                    |
| `ci`       | CI/CD changes                        |

### Examples

```
feat(cli): add download command
fix(proxy): handle connection timeout
docs: update installation instructions
test(history): add edge case coverage
```

## Pull Requests

1. Fork the repository and create a branch from `main`.
2. Make your changes and ensure all tests pass.
3. Update documentation if your changes affect public APIs.
4. Write clear commit messages following the conventional commits format.
5. Open a pull request against `main`.

### PR Checklist

- [ ] Tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Type checking passes (`uv run mypy src/`)
- [ ] Code is formatted (`uv run ruff format --check .`)
- [ ] Commit messages follow conventional commits

## Project Structure

```
src/colabsh/
├── __init__.py
├── __about__.py       # Version
├── main.py            # CLI entry point (Click)
├── commands.py        # CLI command implementations
├── constants.py       # App-wide constants
├── history.py         # History CLI subcommand
└── core/
    ├── config.py      # Configuration management
    ├── server.py      # Background TCP server
    ├── proxy.py       # WebSocket proxy
    ├── output.py      # Output formatting
    ├── history.py     # History tracking
    ├── repl.py        # Interactive REPL
    └── qr.py          # QR code generation

tests/
├── conftest.py        # Shared fixtures
├── test_main.py       # CLI tests
├── test_config.py     # Config tests
├── test_output.py     # Output tests
├── test_history_core.py
└── test_history_cli.py
```

## License

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](LICENSE).
