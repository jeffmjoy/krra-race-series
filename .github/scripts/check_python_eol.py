#!/usr/bin/env python3
"""
Check Python version EOL status and recommend updates.

This script:
1. Fetches official Python EOL data from endoflife.date API
2. Checks project's supported Python versions from pyproject.toml
3. Alerts if any supported version is EOL or approaching EOL
4. Recommends updates to newer stable versions
"""

import contextlib
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

try:
    import requests
    from packaging.specifiers import InvalidSpecifier, SpecifierSet
    from packaging.version import Version
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install requests packaging")
    sys.exit(1)


def fetch_python_eol_data() -> list[dict[str, Any]]:
    """Fetch Python EOL data from endoflife.date API."""
    url = "https://endoflife.date/api/python.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch Python EOL data: {e}")
        sys.exit(1)


def parse_pyproject_toml() -> dict[str, Any]:
    """Parse pyproject.toml to extract Python version requirements."""
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"ERROR: pyproject.toml not found at {pyproject_path}")
        sys.exit(1)

    content = pyproject_path.read_text(encoding="utf-8")

    # Simple parser for requires-python field
    requires_python = None
    for line in content.split("\n"):
        if "requires-python" in line.lower():
            # Extract version specifier: requires-python = ">=3.10"
            parts = line.split("=", 1)
            if len(parts) == 2:
                requires_python = parts[1].strip().strip('"').strip("'")
                break

    if not requires_python:
        print("ERROR: Could not find requires-python in pyproject.toml")
        print("Please ensure pyproject.toml contains a requires-python field")
        sys.exit(1)

    return {"requires_python": requires_python, "path": str(pyproject_path)}


def get_minimum_version(specifier_str: str) -> str | None:
    """Extract minimum Python version from specifier."""
    try:
        spec = SpecifierSet(specifier_str)
        # Look for >= or > operators
        for s in spec:
            if s.operator in (">=", ">"):
                return str(s.version)
    except InvalidSpecifier as e:
        print(f"WARNING: Could not parse specifier '{specifier_str}': {e}")
    return None


def check_eol_status(
    eol_data: list[dict[str, Any]], min_version: str
) -> dict[str, Any]:
    """Check EOL status for Python versions."""
    today = datetime.now().date()
    warning_threshold = today + timedelta(days=180)  # 6 months warning
    maturity_threshold = timedelta(days=90)  # Only recommend versions 90+ days old

    results: dict[str, Any] = {
        "min_version": min_version,
        "eol_versions": [],
        "approaching_eol": [],
        "latest_stable": None,
        "latest_mature": None,
        "recommendations": [],
    }

    for version_data in eol_data:
        cycle = version_data.get("cycle", "")
        eol_date_str = version_data.get("eol", "")
        latest = version_data.get("latest", "")
        lts = version_data.get("lts", False)
        release_date_str = version_data.get("releaseDate", "")

        if not eol_date_str or eol_date_str == "false":
            continue

        try:
            eol_date = datetime.strptime(eol_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        # Parse release date if available
        release_date = None
        if release_date_str:
            with contextlib.suppress(ValueError):
                release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()

        # If the cycle does not contain a dot, assume it is a minor version
        # (e.g., "10" -> "3.10"). This is based on current API behavior for
        # Python 3.x. If Python 4.x cycles appear, update this logic for
        # major version transitions.
        version_str = f"3.{cycle}" if "." not in cycle else cycle

        # Track latest stable (non-EOL) version
        if eol_date > today and (
            results["latest_stable"] is None
            or Version(version_str) > Version(results["latest_stable"]["version"])
        ):
            results["latest_stable"] = {
                "version": version_str,
                "latest_patch": latest,
                "eol_date": eol_date_str,
                "lts": lts,
                "release_date": release_date_str,
            }

        # Track latest mature version (released 90+ days ago)
        if release_date is not None:
            is_mature = (today - release_date) >= maturity_threshold
            if (
                eol_date > today
                and is_mature
                and (
                    results["latest_mature"] is None
                    or Version(version_str)
                    > Version(results["latest_mature"]["version"])
                )
            ):
                results["latest_mature"] = {
                    "version": version_str,
                    "latest_patch": latest,
                    "eol_date": eol_date_str,
                    "lts": lts,
                    "release_date": release_date_str,
                    "days_since_release": (today - release_date).days,
                }

        # Check if versions in our supported range are EOL or approaching EOL
        try:
            if Version(version_str) >= Version(min_version):
                if eol_date < today:
                    results["eol_versions"].append(
                        {
                            "version": version_str,
                            "latest_patch": latest,
                            "eol_date": eol_date_str,
                            "days_past_eol": (today - eol_date).days,
                        }
                    )
                elif eol_date < warning_threshold:
                    results["approaching_eol"].append(
                        {
                            "version": version_str,
                            "latest_patch": latest,
                            "eol_date": eol_date_str,
                            "days_until_eol": (eol_date - today).days,
                        }
                    )
        except (ValueError, TypeError):
            # Skip versions with invalid version strings
            continue

    return results


def generate_report(results: dict[str, Any], pyproject_info: dict[str, Any]) -> str:
    """Generate a human-readable report."""
    lines = []
    lines.append("# Python Version EOL Status Report")
    lines.append("")
    lines.append(f"**Report Date:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Project Requirement:** `{pyproject_info['requires_python']}`")
    lines.append(f"**Minimum Version:** Python {results['min_version']}")
    lines.append("")

    has_issues = False

    # EOL versions
    if results["eol_versions"]:
        has_issues = True
        lines.append("## ⚠️ End-of-Life Versions")
        lines.append("")
        lines.append(
            "The following Python versions in your supported range are **already EOL**:"
        )
        lines.append("")
        for v in results["eol_versions"]:
            lines.append(f"- **Python {v['version']}** (latest: {v['latest_patch']})")
            lines.append(f"  - EOL Date: {v['eol_date']}")
            lines.append(f"  - Days past EOL: **{v['days_past_eol']} days**")
        lines.append("")

    # Approaching EOL
    if results["approaching_eol"]:
        has_issues = True
        lines.append("## ⏰ Approaching End-of-Life")
        lines.append("")
        lines.append("The following versions will reach EOL soon (within 6 months):")
        lines.append("")
        for v in results["approaching_eol"]:
            lines.append(f"- **Python {v['version']}** (latest: {v['latest_patch']})")
            lines.append(f"  - EOL Date: {v['eol_date']}")
            lines.append(f"  - Days until EOL: **{v['days_until_eol']} days**")
        lines.append("")

    # Latest stable recommendation (prioritize mature versions)
    recommended_version = results.get("latest_mature") or results.get("latest_stable")
    if recommended_version:
        lines.append("## ✅ Latest Stable Version")
        lines.append("")
        lines.append(
            f"**Python {recommended_version['version']}** "
            f"(latest patch: {recommended_version['latest_patch']})"
        )
        lines.append(f"- EOL Date: {recommended_version['eol_date']}")
        if recommended_version.get("lts"):
            lines.append("- **LTS** (Long Term Support)")
        if "days_since_release" in recommended_version:
            days = recommended_version["days_since_release"]
            lines.append(f"- Released {days} days ago (mature version)")
        lines.append("")

        # Note if a newer version exists but is too new
        if results["latest_stable"] and not results.get("latest_mature"):
            latest = results["latest_stable"]
            lines.append(
                "ℹ️ **Note**: A newer version is available but not yet recommended:"
            )
            lines.append("")
            lines.append(
                f"- **Python {latest['version']}** "
                f"(latest patch: {latest['latest_patch']})"
            )
            if latest.get("release_date"):
                try:
                    release = datetime.strptime(
                        latest["release_date"], "%Y-%m-%d"
                    ).date()
                    days_old = (datetime.now().date() - release).days
                    lines.append(
                        f"  - Released {days_old} days ago "
                        "(waiting for 90-day maturity period)"
                    )
                except ValueError:
                    pass
            lines.append("")

    # Recommendations
    if has_issues or recommended_version:
        lines.append("## 📋 Recommendations")
        lines.append("")

        if results["eol_versions"]:
            lines.append(
                "- **Immediately update minimum Python version** - "
                "Your current minimum version is EOL"
            )
            if recommended_version:
                rec_ver = recommended_version["version"]
                lines.append(f"  - Update `requires-python` to `>={rec_ver}`")
                lines.append(f"  - Update CI/CD workflows to test Python {rec_ver}")

        if results["approaching_eol"]:
            lines.append(
                "- **Plan migration** - "
                "Prepare to update your minimum version before EOL"
            )

        if recommended_version and Version(recommended_version["version"]) > Version(
            results["min_version"]
        ):
            rec_ver = recommended_version["version"]
            lines.append(f"- **Consider upgrading to Python {rec_ver}** for:")
            lines.append("  - Latest security patches")
            lines.append("  - Performance improvements")
            lines.append("  - New language features")
            lines.append("  - Extended support timeline")

        lines.append("")
        lines.append("## ⚠️ Branch Protection Consideration")
        lines.append("")
        lines.append(
            "If you have branch protection rules that require specific CI checks "
            "(e.g., `test (3.10)`), you may need to update those rules when adding "
            "or removing Python versions from the CI matrix."
        )
        lines.append("")
        lines.append(
            "See `docs/PYTHON_VERSION_MANAGEMENT.md` for guidance on managing "
            "branch protection rules."
        )
        lines.append("")
        lines.append("## 🔧 Action Items")
        lines.append("")
        lines.append("- [ ] Update `pyproject.toml` `requires-python` field")
        lines.append("- [ ] Update `pyproject.toml` classifiers")
        lines.append(
            "- [ ] Update instruction files (`.github/copilot-instructions.md`, "
            "`agents.md`)"
        )
        lines.append(
            "- [ ] Update GitHub Actions workflows (`.github/workflows/*.yml`) "
            "Python version matrices"
        )
        lines.append(
            "- [ ] Update GitHub branch protection rules (if using specific CI checks)"
        )
        lines.append("- [ ] Test with new Python version")
        lines.append("- [ ] Update documentation")
    else:
        lines.append("## ✅ Status: OK")
        lines.append("")
        lines.append(
            "All supported Python versions are current and not approaching EOL."
        )

    lines.append("")
    lines.append("---")
    lines.append(
        "*This report is generated automatically by "
        "`.github/workflows/python-version-check.yml`*"
    )

    return "\n".join(lines)


def main() -> None:
    """Main execution function."""
    print("Checking Python EOL status...")

    # Fetch data
    eol_data = fetch_python_eol_data()
    pyproject_info = parse_pyproject_toml()

    # Extract minimum version
    min_version = get_minimum_version(pyproject_info["requires_python"])
    if not min_version:
        print(
            "ERROR: Could not determine minimum version from "
            f"'{pyproject_info['requires_python']}'"
        )
        sys.exit(1)

    print(f"Minimum Python version: {min_version}")

    # Check EOL status
    results = check_eol_status(eol_data, min_version)

    # Generate report
    report = generate_report(results, pyproject_info)

    # Print to console
    print("\n" + "=" * 70)
    print(report)
    print("=" * 70)

    report_path = Path("python-version-report.txt")
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {report_path}")

    # Exit with error if action needed
    if results["eol_versions"] or results["approaching_eol"]:
        print("\n⚠️  ACTION REQUIRED: Python version update needed!")
        sys.exit(1)

    print("\n✅ All Python versions are current.")
    sys.exit(0)


if __name__ == "__main__":
    main()
