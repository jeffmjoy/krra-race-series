"""Tests for export module."""

import pytest
import csv
from pathlib import Path
from krra_race_series.scoring import SeriesTotal, RacePoints
from krra_race_series.export import ResultsExporter


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

    with open(output_path, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Total Points"]
        assert rows[1] == ["1", "M001", "John Doe", "2", "190"]
        assert rows[2] == ["2", "M002", "Jane Smith", "1", "100"]
