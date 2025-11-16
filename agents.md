# Agent Instructions for KRRA Race Series

## Virtual Environment Setup

This project uses a virtual environment at `.venv/`.

**First command in a new terminal:** If the terminal doesn't have the venv activated yet, run:

```bash
source .venv/bin/activate
```

**All subsequent commands** in that same terminal can be run directly without re-activating:
- `pytest` ✓
- `ruff check --fix src/ tests/` ✓
- `mypy src/` ✓
- `pip install package-name` ✓

The terminal persists the activation, so DO NOT prepend `source .venv/bin/activate &&` to every command.

### If virtual environment doesn't exist

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Common Development Workflows

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=krra_race_series --cov-report=term-missing
```

**Coverage Target:** Aim for 90%+ code coverage. This is a reasonable baseline that balances thoroughness with pragmatism.

### Linting and Formatting

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

### Type Checking

```bash
mypy src/
```

### Running the CLI

Using the Python module:

```bash
python -m krra_race_series.cli \
  --members data/members/members.csv \
  --races data/race_results/*.csv \
  --output data/output/results.csv
```

Or using the installed entry point:

```bash
krra-scoring --members data/members/members.csv --races data/race_results/*.csv --output data/output/results.csv
```

## Pre-commit Hooks

Pre-commit hooks are configured and should be installed:

```bash
pre-commit install
```

To manually run all hooks:

```bash
pre-commit run --all-files
```

## Security Scanning (Optional)

If you have Snyk installed, run security scans after generating or modifying code:

```bash
# Code scan for security issues in first-party code
snyk code test

# Dependency scan for vulnerabilities in third-party packages
snyk test
```

Fix any issues found and rescan until no new issues are detected.

## Project Structure Quick Reference

```text
krra-race-series/
├── src/krra_race_series/    # Main source code
│   ├── cli.py               # Command-line interface
│   ├── race_results.py      # Race result ingestion
│   ├── members.py           # Member management
│   ├── matching.py          # Finisher-to-member matching
│   ├── scoring.py           # Points calculation
│   └── export.py            # Results export
├── tests/                   # Test files (mirror src structure)
├── data/                    # Data files (CSV inputs/outputs)
│   ├── race_results/        # Race CSV files
│   ├── members/             # Member CSV files
│   └── output/              # Generated results
└── .venv/                   # Virtual environment (not in git)
```

## Installing New Dependencies

When adding a new package:

1. Install the package: `pip install package-name`
2. Add to `pyproject.toml`:
   - Runtime dependencies: add to `dependencies = [...]`
   - Dev dependencies: add to `[project.optional-dependencies]` under `dev = [...]`

## Troubleshooting

### Pre-commit hooks failing

→ Run `ruff check --fix` and `ruff format` to auto-fix most issues

### Command not found (pytest, ruff, etc.)

→ Activate venv once: `source .venv/bin/activate`, then retry

## Pre-commit Hook Behavior

The project uses pre-commit hooks that automatically run on each commit:

- Run Ruff linting and formatting
- Remove trailing whitespace
- Fix end-of-file issues
- Validate YAML/JSON/TOML
- Run mypy type checking

If hooks fail, fix the issues and commit again.
