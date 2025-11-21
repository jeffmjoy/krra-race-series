# Python Version Management

This document describes the automated Python version EOL checking system.

## Overview

The project includes an automated workflow that monitors Python version End-of-Life (EOL) status and alerts when it's time to update the minimum Python version.

## How It Works

### Automated Checks

The workflow runs:

- **Monthly**: On the 1st of each month at 9:00 UTC
- **On Pull Requests**: When `pyproject.toml` or the workflow file is modified
- **Manually**: Via GitHub Actions "Run workflow" button

### What It Checks

1. **EOL Status**: Identifies if the minimum Python version is already EOL
2. **Approaching EOL**: Warns when supported versions will EOL within 6 months
3. **Latest Stable**: Recommends the newest stable Python version
4. **Action Items**: Provides a checklist of files to update

### When Upgrades Are Recommended

The script provides recommendations in three scenarios:

1. **Critical (Exits with error)**: When the minimum Python version is **already EOL** or will be within 6 months
2. **Advisory (Informational)**: When a newer stable Python version is available, even if the current minimum is still supported
3. **Best Practice**: The script always shows the latest stable version so you can plan proactive upgrades

**Example**: The repo may require Python 3.10+ (EOL: October 2026). While Python 3.10 is still supported, the script recommends considering Python 3.13 (the latest stable) for better performance, security patches, and extended support until 2029.

### Automated Actions

When the monthly check runs or when triggered manually:

- A detailed report is generated showing Python version status
- A GitHub Issue is **always** created or updated (for both critical EOL warnings and advisory recommendations)
- Issue labels indicate severity:
  - **Critical** (EOL or approaching EOL): `python-version-update`, `dependencies`, `priority-high`
  - **Advisory** (newer version available): `python-version-update`, `dependencies`, `advisory`
- Issue title changes based on severity:
  - **⚠️ Python Version Update Required** - Immediate action needed
  - **ℹ️ Python Version Update Available** - Optional upgrade recommendation
- Subsequent runs update the existing issue rather than creating duplicates
- You can close the issue if you choose not to upgrade (e.g., for advisory recommendations)

**How it works**:

- The workflow checks for existing open issues with the `python-version-update` label
- If an issue exists: Adds a timestamped comment with the latest report and updates title/labels if severity changed
- If none exists: Creates a new issue with appropriate severity (critical or advisory)
- Only one Python version issue will be open at a time
- Closed issues will be recreated on the next run if the situation hasn't changed

## Manual Usage

You can run the EOL check script locally:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the check
python .github/scripts/check_python_eol.py
```

The script will:

- Fetch the latest Python EOL data from [endoflife.date](https://endoflife.date/python)
- Parse `pyproject.toml` for the minimum version
- Generate a report with recommendations
- Exit with code 1 if action is needed, 0 if all versions are current

**Note**: When run in GitHub Actions, the script generates `python-version-report.txt` in the repository root. This file is used by the workflow to create GitHub Issues but is **not** committed to git (it's temporary). When run locally, the file is created in the current directory for review.

## Understanding the Report

### Report Sections

1. **⚠️ End-of-Life Versions**: Python versions that are already EOL
2. **⏰ Approaching End-of-Life**: Versions that will EOL within 6 months
3. **✅ Latest Stable Version**: The newest recommended Python version
4. **📋 Recommendations**: Suggested actions based on findings
5. **🔧 Action Items**: Checklist of files to update

### Example Report

```markdown
# Python Version EOL Status Report

**Report Date:** 2025-11-19
**Project Requirement:** `>=3.9,<4.0`
**Minimum Version:** Python 3.9

## ⚠️ End-of-Life Versions

- **Python 3.10** (latest: 3.9.25)
  - EOL Date: 2025-10-31
  - Days past EOL: 19 days

## ✅ Latest Stable Version

**Python 3.13** (latest patch: 3.13.1)
- EOL Date: 2029-10-31

## 📋 Recommendations

1. **Immediately update minimum Python version**
   - Update `requires-python` to `>=3.13`
   - Update CI/CD workflows to test Python 3.13
```

## Updating Python Version

When you need to update the minimum Python version:

1. **Update `pyproject.toml`**:

   ```toml
   requires-python = ">=3.13,<4.0"
   ```

2. **Update instruction files**:
   - `.github/copilot-instructions.md`
   - `agents.md`

3. **Update classifiers in `pyproject.toml`**:

   ```toml
   classifiers = [
       "Programming Language :: Python :: 3.13",
   ]
   ```

4. **Update CI/CD workflows**:
   - `.github/workflows/ci.yml` - Update the `python-version` matrix to test new versions
   - Example: Change `["3.10", "3.11", "3.12", "3.13"]` to `["3.13"]` if dropping old versions

5. **Update GitHub branch protection rules** (if applicable):
   - See "Branch Protection Rules" section below

6. **Test with the new version**:

   ```bash
   # Create new venv with Python 3.13
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   pytest
   ```

7. **Close the GitHub issue** created by the workflow

## Branch Protection Rules

If you have branch protection rules that require specific CI checks to pass (e.g., `test (3.10)`, `test (3.11)`), removing a Python version from your CI matrix will cause issues:

- The old check (e.g., `test (3.10)`) will never complete
- Pull requests will be blocked waiting for a check that no longer exists

**Solution:** Consider using a status check aggregate job (like `ci-complete`) that depends on all matrix jobs. This allows you to require only one check in branch protection rules, which remains stable regardless of Python version changes in the matrix.

See the project's `.github/workflows/ci.yml` for an example implementation.

## Configuration

### Workflow File

Location: `.github/workflows/python-version-check.yml`

Customize the schedule:

```yaml
on:
  schedule:
    - cron: '0 9 1 * *'  # Monthly on the 1st at 9:00 UTC
```

### Warning Threshold

The script warns 6 months before EOL. To change this:

Edit `.github/scripts/check_python_eol.py`:

```python
warning_threshold = today + timedelta(days=180)  # Change 180 to desired days
```

## Dependencies

The EOL check script requires:

- `requests`: For fetching EOL data from the API
- `packaging`: For version comparison

These are included in the `dev` dependencies in `pyproject.toml`.

## Troubleshooting

### Script fails to fetch EOL data

The script uses the free [endoflife.date API](https://endoflife.date/docs/api/). If it's unreachable:

- Check Internet connection
- Verify the API is operational
- Run manually to see detailed error messages

### Issue not created automatically

Ensure:

- GitHub Actions has permission to create issues
- The workflow completed successfully
- Check Actions logs for errors

### Script exits with error locally

This is expected behavior when:

- A supported Python version is EOL
- A version is approaching EOL within 6 months

Review the report for recommended actions.

## Data Source

Python EOL data is sourced from [endoflife.date](https://endoflife.date/python), which tracks official Python release schedules and EOL dates from [python.org](https://devguide.python.org/versions/).
