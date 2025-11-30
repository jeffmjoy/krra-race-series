# Agent Instructions for KRRA Race Series

## Virtual Environment Setup

This project uses a virtual environment at `.venv/`.

### Each new terminal session requires one-time activation

Before running Python development commands (`pytest`, `ruff`, `mypy`, `pip`, etc.) in a new terminal, activate the venv:

```bash
source .venv/bin/activate
```

**After activation in that terminal session:** All subsequent commands can be run directly without re-activating:

- `pytest` ✓
- `ruff check --fix src/ tests/` ✓
- `mypy src/` ✓
- `pip install package-name` ✓
- `pre-commit run --all-files` ✓
- `krra-scoring --help` ✓

**Best practice for terminal commands:**

- For the first Python command in a new terminal: `source .venv/bin/activate && command`
- For subsequent commands in the same terminal: run commands directly (venv persists)
- DO NOT prepend activation to every command once the terminal has been activated

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
ruff check --fix src/ tests/ .github/scripts/
ruff format src/ tests/ .github/scripts/
```

### Type Checking

```bash
mypy src/ .github/scripts/
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

## Security Scanning

### Repository-level Scanning

Snyk automatically scans the repository via the Snyk GitHub App on PRs and pushes.

### Local Development Scanning (Recommended)

During development, use Snyk MCP tools to scan newly created or modified code:

- The Snyk MCP integration provides `snyk_code_scan` and `snyk_sca_scan` tools
- These are automatically invoked per the instructions in `.github/instructions/snyk_rules.instructions.md`
- Fix any issues found and rescan until no new issues are detected

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
