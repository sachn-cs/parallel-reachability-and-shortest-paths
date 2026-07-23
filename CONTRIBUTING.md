# Contributing to PRSPNSD

Thank you for considering contributing to PRSPNSD! This document outlines the
process for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Branch Naming](#branch-naming)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Running Tests](#running-tests)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/parallel-reachability-and-shortest-paths.git
   cd parallel-reachability-and-shortest-paths
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/sachncs/parallel-reachability-and-shortest-paths.git
   ```

## Development Setup

### Prerequisites

- Python >= 3.9
- pip or a similar package manager

### Installation

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Verify installation
pytest
```

### Code Quality Tools

This project uses:

- **ruff** for linting and formatting
- **mypy** for static type checking
- **pytest** for testing

Run all checks before submitting a PR:

```bash
ruff check reachq tests scripts
mypy reachq
pytest
```

## Branch Naming

Use descriptive branch names with the following prefixes:

| Prefix | Purpose |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes |
| `refactor/` | Code refactoring |
| `test/` | Adding or updating tests |
| `chore/` | Maintenance tasks |

Examples:
- `feat/add-parallel-bfs`
- `fix/shortcut-set-edge-case`
- `docs/update-api-reference`

## Commit Conventions

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semi-colons, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Examples

```
feat(graph): add weighted graph support
fix(hopset): correct distance calculation for edge case
docs(api): update function signatures
refactor(reachability): simplify BFS implementation
test(shortcut_set): add invariant checking tests
chore(ci): update GitHub Actions workflow
```

### Scopes

- `graph` - Graph data structures
- `reachability` - BFS and reachability algorithms
- `shortest-paths` - Dijkstra and shortest path algorithms
- `shortcut-set` - Shortcut set construction
- `hopset` - Hopset construction
- `transitive-closure` - Matrix-based TC
- `generators` - Graph generators
- `serialization` - JSON serialization
- `work-depth` - Work/depth simulation
- `invariants` - Invariant checkers
- `cli` - Command-line interface
- `ci` - CI/CD configuration

## Pull Request Process

### Before Submitting

1. Ensure your code passes all checks:
   ```bash
   ruff check reachq tests scripts
   mypy reachq
   pytest
   ```
2. Update documentation if needed.
3. Add an entry to `CHANGELOG.md` under `[Unreleased]`.
4. Rebase on the latest `main` branch.

### PR Title

Use the same convention as commit messages:
```
feat(reachability): add parallel BFS with shortcut edges
```

### PR Description

Include:
- **Summary**: What does this PR do?
- **Related Issue**: Link to the issue (if applicable).
- **Changes**: Bullet list of changes.
- **Testing**: How was this tested?
- **Checklist**: See below.

### Checklist

- [ ] Code follows the project's coding standards
- [ ] Tests pass locally (`pytest`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy reachq`)
- [ ] Documentation is updated (if applicable)
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow Conventional Commits

## Coding Standards

### General

- Python >= 3.9 compatible
- Use type hints on all public functions
- Follow Google-style docstrings (enforced by ruff)
- Maximum line length: 100 characters

### Graph Algorithms

- Accept `random_seed` parameters for reproducibility
- Use `random.Random` instances (not global `random`)
- Document asymptotic complexity in docstrings
- Mark theoretical assumptions with `ASSUMPTION` comments

### Testing

- Write tests for all new public functions
- Use `pytest` markers: `@pytest.mark.slow` for expensive tests
- Include both positive and negative test cases
- Test edge cases (empty graphs, single vertex, etc.)

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=reachq --cov-report=term-missing

# Skip slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/test_reachability.py

# Run with verbose output
pytest -v
```

## Documentation

- Update `docs/` when adding new modules or functions
- Keep `README.md` focused on getting started quickly
- Add examples for new public APIs
- Document any breaking changes in `CHANGELOG.md`

## Questions?

Open an issue with the label `question` if you need help getting started.
