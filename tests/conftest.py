"""Shared test fixtures and configuration."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_members_csv(tmp_path: Path) -> Path:
    """Create a sample members CSV file for testing.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to the created members CSV file
    """
    members_file = tmp_path / "members.csv"
    members_file.write_text(
        "member_id,first_name,last_name,email,age,gender\n"
        "M001,John,Doe,john@example.com,35,M\n"
        "M002,Jane,Smith,jane@example.com,28,F\n"
    )
    return members_file


@pytest.fixture
def sample_race_csv(tmp_path: Path) -> Path:
    """Create a sample race results CSV file for testing.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to the created race results CSV file
    """
    race_file = tmp_path / "spring_5k.csv"
    race_file.write_text(
        "place,name,time,age,gender,bib_number\n"
        "1,John Doe,18:30,35,M,101\n"
        "2,Jane Smith,19:45,28,F,102\n"
    )
    return race_file


@pytest.fixture
def sample_members_with_multiple_age_groups(tmp_path: Path) -> Path:
    """Create a members CSV with diverse ages for age group testing.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to the created members CSV file
    """
    members_file = tmp_path / "members_diverse.csv"
    members_file.write_text(
        "member_id,first_name,last_name,email,age,gender\n"
        "M001,John,Doe,john@example.com,35,M\n"
        "M002,Jane,Smith,jane@example.com,28,F\n"
        "M003,Bob,Jones,bob@example.com,45,M\n"
        "M004,Alice,Brown,alice@example.com,52,F\n"
        "M005,Charlie,Wilson,charlie@example.com,19,M\n"
    )
    return members_file
