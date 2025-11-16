# KRRA Race Series Scoring System

A proof-of-concept application for automating the Kingston Road Runners Association (KRRA) race series scoring.

## Overview

This project automates the process of:

- Ingesting race result files (CSV format)
- Loading KRRA member lists
- Matching race finishers with members
- Applying a points system based on finishing position
- Generating cumulative series totals
- Exporting results to CSV

## Project Structure

```text
krra-race-series/
├── src/krra_race_series/    # Main package
│   ├── __init__.py
│   ├── race_results.py      # Race results ingestion
│   ├── members.py           # Member management
│   ├── matching.py          # Finisher-to-member matching
│   ├── scoring.py           # Points calculation
│   ├── export.py            # Results export
│   └── cli.py               # Command-line interface
├── tests/                   # Test files
├── data/                    # Data files
│   ├── race_results/        # Race CSV files
│   ├── members/             # Member CSV files
│   └── output/              # Generated results
├── config/                  # Configuration files
└── README.md
```

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
  --output data/output/series_results.csv
```

For detailed results with individual race breakdowns:

```bash
python -m krra_race_series.cli \
  --members data/members/members.csv \
  --races data/race_results/*.csv \
  --output data/output/detailed_results.csv \
  --detailed
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

## Features

- CSV-based race result ingestion and member list management
- Name-based matching of race finishers to KRRA members
- Points-based scoring system
- Series totals and standings
- CSV export with summary and detailed formats
- Command-line interface

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

### Pre-commit Hooks

Pre-commit hooks are configured to automatically run checks before committing:

- Ruff linting and formatting
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Type checking with mypy

After running `pre-commit install` during setup, these checks will run automatically on every commit.

**Maintenance:** Run `pre-commit autoupdate` monthly to update hook versions.

## License

MIT License (or your preferred license)

## Contact

Kingston Road Runners Association
