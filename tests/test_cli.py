"""Tests for CLI module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from krra_race_series.cli import main


@pytest.fixture
def sample_members_csv(tmp_path):
    """Create a sample members CSV file."""
    members_file = tmp_path / "members.csv"
    members_file.write_text(
        "member_id,first_name,last_name,email,age,gender\n"
        "M001,John,Doe,john@example.com,35,M\n"
        "M002,Jane,Smith,jane@example.com,28,F\n"
    )
    return members_file


@pytest.fixture
def sample_race_csv(tmp_path):
    """Create a sample race results CSV file."""
    race_file = tmp_path / "spring_5k.csv"
    race_file.write_text(
        "place,name,time,age,gender,bib_number\n"
        "1,John Doe,18:30,35,M,101\n"
        "2,Jane Smith,19:45,28,F,102\n"
    )
    return race_file


def test_main_basic_execution(tmp_path, sample_members_csv, sample_race_csv):
    """Test basic CLI execution with required arguments."""
    output_file = tmp_path / "results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_file),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    # Verify output file was created
    assert output_file.exists()

    # Verify content
    content = output_file.read_text()
    assert '"Rank"' in content and '"Member ID"' in content
    assert "John Doe" in content or "Jane Smith" in content


def test_main_with_multiple_races(tmp_path, sample_members_csv, sample_race_csv):
    """Test CLI execution with multiple race files."""
    race_file_2 = tmp_path / "summer_8k.csv"
    race_file_2.write_text(
        "place,name,time,age,gender,bib_number\n"
        "1,Jane Smith,32:15,28,F,102\n"
        "2,John Doe,33:45,35,M,101\n"
    )

    output_file = tmp_path / "results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        str(race_file_2),
        "--output",
        str(output_file),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    assert output_file.exists()


def test_main_with_detailed_output(tmp_path, sample_members_csv, sample_race_csv):
    """Test CLI execution with detailed output flag."""
    output_file = tmp_path / "detailed_results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_file),
        "--detailed",
    ]

    with patch.object(sys, "argv", test_args):
        main()

    # Verify output file was created
    assert output_file.exists()

    # Detailed CSV should have more columns
    content = output_file.read_text()
    assert (
        '"Race"' in content
        and '"Overall Place"' in content
        and '"Overall Points"' in content
    )


def test_main_default_output_path(tmp_path, sample_members_csv, sample_race_csv):
    """Test CLI with default output path."""
    # Create the default output directory
    default_output_dir = Path("data/output")
    default_output_dir.mkdir(parents=True, exist_ok=True)
    default_output_file = default_output_dir / "series_results.csv"

    # Clean up if it exists from previous runs
    if default_output_file.exists():
        default_output_file.unlink()

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
    ]

    try:
        with patch.object(sys, "argv", test_args):
            main()

        # Verify default output file was created
        assert default_output_file.exists()
    finally:
        # Clean up
        if default_output_file.exists():
            default_output_file.unlink()


def test_main_creates_output_directory(tmp_path, sample_members_csv, sample_race_csv):
    """Test that CLI creates output directory if it doesn't exist."""
    output_file = tmp_path / "nested" / "dir" / "results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_file),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    assert output_file.exists()


def test_main_prints_progress_messages(
    tmp_path, sample_members_csv, sample_race_csv, capsys
):
    """Test that CLI prints progress messages."""
    output_file = tmp_path / "results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_file),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()

    # Check for expected progress messages
    assert "Loading members" in captured.out
    assert "Loaded 2 members" in captured.out
    assert "Processing race" in captured.out
    assert "finishers" in captured.out
    assert "matched with members" in captured.out
    assert "Calculating series totals" in captured.out
    assert "Exporting results" in captured.out
    assert "Top 10 standings" in captured.out
    assert "Complete!" in captured.out


def test_main_prints_top_10_standings(
    tmp_path, sample_members_csv, sample_race_csv, capsys
):
    """Test that CLI prints top 10 standings."""
    output_file = tmp_path / "results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_file),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()

    # Check that standings include member names and points
    output_lines = captured.out.split("\n")
    standings_section = [
        line for line in output_lines if "points" in line and "races" in line
    ]

    # Should have at least one standing line
    assert len(standings_section) > 0


def test_main_missing_required_arguments():
    """Test that CLI fails gracefully when required arguments are missing."""
    test_args = ["krra-scoring"]

    with patch.object(sys, "argv", test_args), pytest.raises(SystemExit):
        main()


def test_main_with_nonexistent_members_file(tmp_path, sample_race_csv):
    """Test CLI behavior with non-existent members file."""
    output_file = tmp_path / "results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(tmp_path / "nonexistent_members.csv"),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_file),
    ]

    with patch.object(sys, "argv", test_args), pytest.raises(FileNotFoundError):
        main()


def test_main_with_nonexistent_race_file(tmp_path, sample_members_csv):
    """Test CLI behavior with non-existent race file."""
    output_file = tmp_path / "results.csv"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(tmp_path / "nonexistent_race.csv"),
        "--output",
        str(output_file),
    ]

    with patch.object(sys, "argv", test_args), pytest.raises(FileNotFoundError):
        main()
