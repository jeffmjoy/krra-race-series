# GitHub Copilot Instructions for KRRA Race Series

## Project Overview
This is a Python application for automating race series scoring for the Kingston Road Runners Association. The project emphasizes code quality, type safety, and comprehensive testing.

## Python Version

- **Required:** Python 3.8+
- **Compatible:** Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- Always write code compatible with Python 3.8 as the minimum version

## Code Standards

### Type Hints
- **All functions must include type hints** for parameters and return values
- Use `from typing import ...` for Python 3.8 compatibility
- Mark the package as typed (we include `py.typed`)
- Example:
  ```python
  def calculate_points(place: int, total_finishers: int) -> int:
      return max(0, 100 - (place - 1))
  ```

### Testing Requirements

- **Write pytest tests for all new functionality**
- **Target: 90%+ code coverage** as a reasonable baseline for quality
- Test files should mirror source structure: `src/krra_race_series/scoring.py` → `tests/test_scoring.py`
- Use fixtures defined in `tests/conftest.py` for common test data
- Include edge cases and error conditions
- Example test structure:
  ```python
  def test_function_name():
      # Arrange
      input_data = ...
      # Act
      result = function_under_test(input_data)
      # Assert
      assert result == expected_value
  ```

### Code Style

- Follow Ruff linting rules (configured in `pyproject.toml`)
- Line length: 88 characters
- Use double quotes for strings
- Import order: standard library, third-party, local (handled by Ruff's isort)

### Data Structures

- Prefer dataclasses for structured data (see existing patterns in the codebase)
- Use `@dataclass` from the `dataclasses` module
- Make dataclasses frozen when appropriate for immutability

### Error Handling

- Raise specific exceptions with clear messages
- Document expected exceptions in docstrings
- Validate input data early in functions

### Documentation

- Use docstrings for public functions and classes
- Keep inline comments minimal and purposeful
- Update README.md when adding significant features

## Security

- **Always run Snyk scans on newly created code** (see `.github/instructions/snyk_rules.instructions.md`)
- Avoid hardcoding sensitive data (credentials, API keys, PII)
- Be mindful of member data privacy (names, emails, ages)

## File Organization

- Source code: `src/krra_race_series/`
- Tests: `tests/`
- Data files: `data/` (not committed to git when containing PII)
- Configuration: `config/` or root-level config files

## Common Patterns in This Project

- CSV-based data ingestion using `csv.DictReader`
- Dataclasses for domain models (Members, RaceResults, etc.)
- Separation of concerns: ingestion → matching → scoring → export
- CLI built with argparse in `cli.py`

## Before Committing

Pre-commit hooks will automatically run, but you can manually check:

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
mypy src/
pytest
```
