"""Tests for export module."""

import csv

from krra_race_series.export import ResultsExporter
from krra_race_series.scoring import AgeGroup, RacePoints, SeriesTotal


def test_export_to_csv(tmp_path):
    """Test exporting series totals to CSV."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=2,
            total_points=190,
            race_details=[],
        ),
        SeriesTotal(
            member_id="M002",
            member_name="Jane Smith",
            races_completed=1,
            total_points=100,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "results.csv"
    exporter.export_to_csv(totals, output_path)

    assert output_path.exists()

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Total Points"]
        assert rows[1] == ["1", "M001", "John Doe", "2", "190"]
        assert rows[2] == ["2", "M002", "Jane Smith", "1", "100"]


def test_sanitize_csv_field_with_formula_injection():
    """Test that CSV fields are sanitized to prevent formula injection."""
    exporter = ResultsExporter()

    # Test various formula injection patterns
    assert exporter._sanitize_csv_field("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert exporter._sanitize_csv_field("+1+1") == "'+1+1"
    assert exporter._sanitize_csv_field("-5") == "'-5"
    assert exporter._sanitize_csv_field("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert exporter._sanitize_csv_field("\t1+1") == "'\t1+1"
    assert exporter._sanitize_csv_field("\r1+1") == "'\r1+1"

    # Test normal values that should not be modified
    assert exporter._sanitize_csv_field("John Doe") == "John Doe"
    assert exporter._sanitize_csv_field("123") == "123"
    assert exporter._sanitize_csv_field(42) == 42
    assert exporter._sanitize_csv_field(3.14) == 3.14
    assert exporter._sanitize_csv_field("") == ""


def test_export_to_csv_creates_parent_directory(tmp_path):
    """Test that export creates parent directories if they don't exist."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=1,
            total_points=100,
            race_details=[],
        ),
    ]

    # Use a nested path that doesn't exist
    output_path = tmp_path / "nested" / "dir" / "results.csv"
    exporter.export_to_csv(totals, output_path)

    assert output_path.exists()


def test_export_to_csv_with_formula_injection_in_data(tmp_path):
    """Test that CSV export sanitizes malicious data."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="=CMD|'/c calc'!A1",
            member_name="+1+1",
            races_completed=1,
            total_points=100,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "results.csv"
    exporter.export_to_csv(totals, output_path)

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Verify that dangerous values are prefixed with a single quote
        assert rows[1][1] == "'=CMD|'/c calc'!A1"
        assert rows[1][2] == "'+1+1"


def test_export_detailed_csv_with_race_details(tmp_path):
    """Test exporting detailed CSV with race-by-race breakdown."""
    exporter = ResultsExporter()

    race_points = [
        RacePoints(
            member_id="M001",
            race_name="Spring 5K",
            overall_place=5,
            overall_points=96,
            age_group=AgeGroup.AGE_30_39,
            age_group_place=2,
            age_group_points=10,
        ),
        RacePoints(
            member_id="M001",
            race_name="Summer 8K",
            overall_place=10,
            overall_points=91,
            age_group=AgeGroup.AGE_30_39,
            age_group_place=3,
            age_group_points=8,
        ),
    ]

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=2,
            total_points=205,
            race_details=race_points,
        ),
    ]

    output_path = tmp_path / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    assert output_path.exists()

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Check header
        assert rows[0] == [
            "Rank",
            "Member ID",
            "Name",
            "Race",
            "Overall Place",
            "Overall Points",
            "Age Group",
            "Age Group Place",
            "Age Group Points",
            "Race Total",
            "Series Total",
        ]

        # Check first race detail
        assert rows[1][0] == "1"  # Rank
        assert rows[1][1] == "M001"  # Member ID
        assert rows[1][2] == "John Doe"  # Name
        assert rows[1][3] == "Spring 5K"  # Race
        assert rows[1][4] == "5"  # Overall Place
        assert rows[1][5] == "96"  # Overall Points
        assert rows[1][6] == "30-39"  # Age Group
        assert rows[1][7] == "2"  # Age Group Place
        assert rows[1][8] == "10"  # Age Group Points
        assert rows[1][9] == "106"  # Race Total
        assert rows[1][10] == "205"  # Series Total

        # Check second race detail
        assert rows[2][3] == "Summer 8K"
        assert rows[2][6] == "30-39"  # Age group format


def test_export_detailed_csv_with_no_race_details(tmp_path):
    """Test exporting detailed CSV for members with no races."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=0,
            total_points=0,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    assert output_path.exists()

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Should have one data row with empty race fields
        assert rows[1][0] == "1"  # Rank
        assert rows[1][1] == "M001"  # Member ID
        assert rows[1][2] == "John Doe"  # Name
        assert rows[1][3] == ""  # Empty race fields
        assert rows[1][10] == "0"  # Series Total


def test_export_detailed_csv_with_no_age_group(tmp_path):
    """Test exporting detailed CSV with race results that have no age group."""
    exporter = ResultsExporter()

    race_points = [
        RacePoints(
            member_id="M001",
            race_name="Spring 5K",
            overall_place=5,
            overall_points=96,
            age_group=None,
            age_group_place=None,
            age_group_points=0,
        ),
    ]

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=1,
            total_points=96,
            race_details=race_points,
        ),
    ]

    output_path = tmp_path / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Age group fields should be empty
        assert rows[1][6] == ""  # Age Group
        assert rows[1][7] == ""  # Age Group Place


def test_export_detailed_csv_creates_parent_directory(tmp_path):
    """Test that detailed export creates parent directories if they don't exist."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=0,
            total_points=0,
            race_details=[],
        ),
    ]

    # Use a nested path that doesn't exist
    output_path = tmp_path / "nested" / "dir" / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    assert output_path.exists()
