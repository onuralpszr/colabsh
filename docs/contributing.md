---
tags:
  - Development
  - Guide
---

# Contributing

Thank you for your interest in contributing to colabsh!

## Development setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

### Getting started

```bash
git clone https://github.com/onuralpszr/colabsh.git
cd colabsh
uv sync --group dev
uv run pre-commit install
```

## Development workflow

### Running tests

!!! example "Test commands"

    === "Full suite"

        ```bash
        uv run pytest
        ```

    === "Specific file"

        ```bash
        uv run pytest tests/test_config.py
        ```

    === "Without coverage"

        ```bash
        uv run pytest --no-cov
        ```

### Linting and formatting

!!! example "Quality commands"

    === "Lint"

        ```bash
        uv run ruff check .
        ```

    === "Lint + fix"

        ```bash
        uv run ruff check --fix .
        ```

    === "Format"

        ```bash
        uv run ruff format .
        ```

    === "Type check"

        ```bash
        uv run mypy src/
        ```

### Pre-commit hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
uv run pre-commit run --all-files
```

## Commit messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Changelog generation with [git-cliff](https://git-cliff.org/) depends on this format.

!!! info "Format"

    ```
    <type>(<scope>): <description>
    ```

??? abstract "Commit types"

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

!!! example "Examples"

    ```
    feat(cli): add download command
    fix(proxy): handle connection timeout
    docs: update installation instructions
    test(history): add edge case coverage
    ```

## Pull requests

1. Fork the repository and create a branch from `main`
2. Make your changes and ensure all tests pass
3. Update documentation if your changes affect public APIs
4. Write clear commit messages following conventional commits
5. Open a pull request against `main`

!!! success "PR checklist"

    - [x] Tests pass (`uv run pytest`)
    - [x] Linting passes (`uv run ruff check .`)
    - [x] Type checking passes (`uv run mypy src/`)
    - [x] Code is formatted (`uv run ruff format --check .`)
    - [x] Commit messages follow conventional commits

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](https://github.com/onuralpszr/colabsh/blob/main/LICENSE).
