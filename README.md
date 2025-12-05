# KRRA Race Series Scoring System

[![CI](https://github.com/jeffmjoy/krra-race-series/actions/workflows/ci.yml/badge.svg)](https://github.com/jeffmjoy/krra-race-series/actions/workflows/ci.yml)
[![CodeQL](https://github.com/jeffmjoy/krra-race-series/actions/workflows/codeql.yml/badge.svg)](https://github.com/jeffmjoy/krra-race-series/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/jeffmjoy/krra-race-series/graph/badge.svg)](https://codecov.io/gh/jeffmjoy/krra-race-series)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://github.com/python/mypy)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A proof-of-concept application for automating the Kingston Road Runners Association (KRRA) race series scoring.

> [!NOTE]
> This is an early-stage proof-of-concept project under active development.

## Overview

This project automates the process of:

- Ingesting race result files (CSV format)
- Loading KRRA member lists
- Matching race finishers with members
- Applying a points system based on finishing position
- Calculating age-graded performance percentages
- Generating cumulative series totals
- Exporting results to CSV

## Key Features

- 📊 CSV-based race result ingestion
- 🔗 Automated finisher-to-member matching
- 🏆 Points-based scoring system
- 🎯 Age-graded performance rankings (WMA 2020 factors)
- 📈 Series totals and standings
- 💾 CSV export with summary and detailed formats
- 🖥️ Command-line interface

## Getting Started

### Installation

1. Create a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

2. Install the package with development dependencies:

    ```bash
    pip install -e ".[dev]"
    ```

3. Set up pre-commit hooks (recommended):

    ```bash
    pre-commit install
    ```

    This will automatically run code quality checks before each commit.

### Usage

Run the CLI to process race results:

```bash
python -m krra_race_series.cli \
  --members data/members/members.csv \
  --races data/race_results/race1.csv data/race_results/race2.csv \
  --output data/output
```

This generates category standings files (e.g., `M_overall.csv`, `F_30-39.csv`) and an `age_graded.csv` file with combined gender rankings based on age-graded performance.

#### Age-Graded Rankings

The age-graded rankings use World Masters Athletics (WMA) 2020 age-grading factors to compare performances across ages and genders.

To generate only specific categories:

```bash
python -m krra_race_series.cli \
  --members data/members/members.csv \
  --races data/race_results/*.csv \
  --output data/output \
  --categories "M_overall,F_overall,age_graded"
```

To use a different year of age-grading factors:

```bash
python -m krra_race_series.cli \
  --members data/members/members.csv \
  --races data/race_results/*.csv \
  --output data/output \
  --age-grading-year 2020
```

## Data Formats

### Members CSV Format

```csv
member_id,first_name,last_name,email,age,gender
M001,John,Doe,john@example.com,35,M
M002,Jane,Smith,jane@example.com,28,F
```

### Race Results CSV Format

```csv
place,name,time,age,gender,bib_number
1,John Doe,18:23,35,M,101
2,Jane Smith,19:45,28,F,102
```

## Project Structure

```text
krra-race-series/
├── src/krra_race_series/    # Main package source code
├── tests/                   # Test files
└── data/                    # Sample data files for testing
```

See [pyproject.toml](pyproject.toml) for full package configuration and dependencies.

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project uses Ruff for linting and formatting (replaces Black, flake8, isort, and more).

Format and lint code with:

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

Or simply save files in VS Code (auto-format is enabled).

### Python Version Management

The project includes automated monitoring of Python version EOL (End-of-Life) status:

- **Automated checks** run monthly via GitHub Actions
- **Alerts** when the minimum Python version is EOL or approaching EOL
- **Recommendations** for upgrading to newer stable versions

To manually check Python EOL status:

```bash
python .github/scripts/check_python_eol.py
```

See [docs/PYTHON_VERSION_MANAGEMENT.md](docs/PYTHON_VERSION_MANAGEMENT.md) for details.

### Pre-commit Hooks

Pre-commit hooks are configured to automatically run checks before committing:

- Ruff linting and formatting
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Type checking with mypy

After running `pre-commit install` during setup, these checks will run automatically on every commit.

**Maintenance:** Run `pre-commit autoupdate` monthly to update hook versions.

## Contributing

This is currently a proof-of-concept project. If you'd like to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Ensure all tests pass and code is properly formatted
5. Submit a pull request

Please ensure your code:

- Includes type hints
- Has test coverage (target 90%+)
- Passes Ruff linting and formatting
- Passes mypy type checking

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Kingston Road Runners Association - [www.krra.org](https://www.krra.org)

## Acknowledgments

Built for the Kingston Road Runners Association race series scoring automation.
