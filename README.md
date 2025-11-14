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
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Install the package in development mode:

    ```bash
    pip install -e .
    ```

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

## Current Features

- ✅ CSV-based race result ingestion
- ✅ CSV-based member list management
- ✅ Exact name matching for finisher-to-member association
- ✅ Configurable points system (default: 100 pts for 1st, decreasing by 1)
- ✅ Cumulative series totals
- ✅ CSV export (summary and detailed formats)
- ✅ Command-line interface

## Future Enhancements

- [ ] Web scraping for race results
- [ ] Integration with timing software
- [ ] Fuzzy name matching with confidence levels
- [ ] Support for name variations (Jeff vs. Jeffrey)
- [ ] HTML output format
- [ ] Web dashboard
- [ ] Age group scoring
- [ ] Gender-based divisions
- [ ] Database backend
- [ ] REST API

### Development/Tooling

- [ ] See if any of the below are redundant or conflicting
- [ ] Configure Copilot settings for things like auto-approved commands
- [ ] Consider setting up agents.md, copilot-instructions.md, or similar
- [ ] Configure editor to strip trailing whitespace on save
- [ ] Add `.editorconfig` file for consistent formatting
- [ ] Set up pre-commit hooks (e.g., `pre-commit` framework)
- [ ] Add `ruff` or `flake8` linter to catch whitespace issues
- [ ] Configure Black/Ruff to handle trailing whitespace
- [ ] Add linting step to CI/CD pipeline

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. Format code with:

```bash
black src/ tests/
```

## License

MIT License (or your preferred license)

## Contact

Kingston Road Runners Association
