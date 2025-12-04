"""Tests for CLI module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from krra_race_series.cli import main


def test_main_basic_execution(tmp_path, sample_members_csv, sample_race_csv):
    """Test basic CLI execution with required arguments."""
    output_dir = tmp_path / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_dir),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    # Verify output directory was created
    assert output_dir.exists()
    assert output_dir.is_dir()

    # Verify category files were created
    assert (output_dir / "M_overall.csv").exists()
    assert (output_dir / "F_overall.csv").exists()

    # Verify content of one file
    content = (output_dir / "M_overall.csv").read_text()
    assert '"Rank"' in content and '"Member ID"' in content
    assert "John Doe" in content


def test_main_with_multiple_races(tmp_path, sample_members_csv, sample_race_csv):
    """Test CLI execution with multiple race files."""
    race_file_2 = tmp_path / "summer_8k.csv"
    race_file_2.write_text(
        "place,name,time,age,gender,bib_number\n"
        "1,Jane Smith,32:15,28,F,102\n"
        "2,John Doe,33:45,35,M,101\n"
    )

    output_dir = tmp_path / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        str(race_file_2),
        "--output",
        str(output_dir),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    assert output_dir.exists()
    assert (output_dir / "M_overall.csv").exists()


def test_main_with_categories_filter(tmp_path, sample_members_csv, sample_race_csv):
    """Test CLI execution with categories filter."""
    output_dir = tmp_path / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_dir),
        "--categories",
        "M_overall,F_20-29",
    ]

    with patch.object(sys, "argv", test_args):
        main()

    # Verify only requested category files were created
    assert (output_dir / "M_overall.csv").exists()
    assert (output_dir / "F_20-29.csv").exists()
    assert not (output_dir / "F_overall.csv").exists()
    assert not (output_dir / "M_30-39.csv").exists()


def test_main_default_output_path(tmp_path, sample_members_csv, sample_race_csv):
    """Test CLI with default output path."""
    # Create the default output directory
    default_output_dir = Path("data/output")
    default_output_dir.mkdir(parents=True, exist_ok=True)

    # Clean up any existing category files
    for f in default_output_dir.glob("*.csv"):
        f.unlink()

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

        # Verify category files were created in default output directory
        assert (default_output_dir / "M_overall.csv").exists()
        assert (default_output_dir / "F_overall.csv").exists()
    finally:
        # Clean up
        for f in default_output_dir.glob("*.csv"):
            f.unlink()


def test_main_creates_output_directory(tmp_path, sample_members_csv, sample_race_csv):
    """Test that CLI creates output directory if it doesn't exist."""
    output_dir = tmp_path / "nested" / "dir" / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_dir),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    assert output_dir.exists()
    assert (output_dir / "M_overall.csv").exists()


def test_main_prints_progress_messages(
    tmp_path, sample_members_csv, sample_race_csv, capsys
):
    """Test that CLI prints progress messages."""
    output_dir = tmp_path / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_dir),
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
    assert "Calculating category standings" in captured.out
    assert "Exporting category standings" in captured.out
    assert "Category Standings Summary" in captured.out
    assert "Complete!" in captured.out


def test_main_prints_top_10_standings(
    tmp_path, sample_members_csv, sample_race_csv, capsys
):
    """Test that CLI prints category standings summary."""
    output_dir = tmp_path / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_dir),
    ]

    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()

    # Check that standings include member names and points
    output_lines = captured.out.split("\n")
    standings_section = [
        line for line in output_lines if "points" in line and "races" in line
    ]

    # Should have at least one standing line per category
    assert len(standings_section) > 0
    # Should show category names
    assert "M_overall:" in captured.out or "F_overall:" in captured.out


def test_main_missing_required_arguments():
    """Test that CLI fails gracefully when required arguments are missing."""
    test_args = ["krra-scoring"]

    with patch.object(sys, "argv", test_args), pytest.raises(SystemExit):
        main()


def test_main_with_nonexistent_members_file(tmp_path, sample_race_csv):
    """Test CLI behavior with non-existent members file."""
    output_dir = tmp_path / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(tmp_path / "nonexistent_members.csv"),
        "--races",
        str(sample_race_csv),
        "--output",
        str(output_dir),
    ]

    with patch.object(sys, "argv", test_args), pytest.raises(FileNotFoundError):
        main()


def test_main_with_nonexistent_race_file(tmp_path, sample_members_csv):
    """Test CLI behavior with non-existent race file."""
    output_dir = tmp_path / "results"

    test_args = [
        "krra-scoring",
        "--members",
        str(sample_members_csv),
        "--races",
        str(tmp_path / "nonexistent_race.csv"),
        "--output",
        str(output_dir),
    ]

    with patch.object(sys, "argv", test_args), pytest.raises(FileNotFoundError):
        main()


def test_cli_module_main_block(tmp_path, sample_members_csv, sample_race_csv):
    """Test the if __name__ == '__main__' block by running the module."""
    output_dir = tmp_path / "results"

    # Create a test script that imports and runs the CLI module's main block
    test_script = tmp_path / "run_cli.py"
    test_script.write_text(
        f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent / "src"}')

# Set up command line arguments
sys.argv = [
    'cli.py',
    '--members', '{sample_members_csv}',
    '--races', '{sample_race_csv}',
    '--output', '{output_dir}'
]

# Import and run the CLI module as if it were executed directly
if __name__ == '__main__':
    from krra_race_series import cli
    cli.main()
"""
    )

    # Run the script
    result = subprocess.run(
        [sys.executable, str(test_script)], capture_output=True, text=True
    )

    # Verify it executed successfully
    assert result.returncode == 0
    assert output_dir.exists()
    assert (output_dir / "M_overall.csv").exists()
