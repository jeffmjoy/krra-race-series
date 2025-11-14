"""Tests for race results module."""

import pytest
from pathlib import Path
from krra_race_series.race_results import RaceResultsLoader, RaceResult


def test_race_result_creation():
    """Test creating a RaceResult."""
    result = RaceResult(place=1, name="John Doe", time="18:30", age=35, gender="M")

    assert result.place == 1
    assert result.name == "John Doe"
    assert result.time == "18:30"


def test_load_csv_file_not_found():
    """Test loading a non-existent CSV file."""
    loader = RaceResultsLoader()

    with pytest.raises(FileNotFoundError):
        loader.load_csv(Path("nonexistent.csv"))
