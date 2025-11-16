"""Tests for race results module."""

from datetime import date
from pathlib import Path

import pytest

from krra_race_series.race_results import RaceResult, RaceResultsLoader


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


def test_load_csv_with_complete_data(tmp_path):
    """Test loading race results from a CSV file with complete data."""
    loader = RaceResultsLoader()

    # Create test CSV file
    csv_path = tmp_path / "spring_5k.csv"
    csv_path.write_text(
        "place,name,time,age,gender,bib_number\n"
        "1,John Doe,18:30,35,M,101\n"
        "2,Jane Smith,19:45,28,F,102\n"
        "3,Bob Johnson,20:15,42,M,103\n"
    )

    race = loader.load_csv(csv_path)

    assert race.name == "spring_5k"
    assert isinstance(race.date, date)
    assert len(race.results) == 3

    # Check first result
    assert race.results[0].place == 1
    assert race.results[0].name == "John Doe"
    assert race.results[0].time == "18:30"
    assert race.results[0].age == 35
    assert race.results[0].gender == "M"
    assert race.results[0].bib_number == "101"


def test_load_csv_with_partial_data(tmp_path):
    """Test loading race results with missing optional fields."""
    loader = RaceResultsLoader()

    # Create test CSV with missing optional fields
    csv_path = tmp_path / "race.csv"
    csv_path.write_text(
        "place,name,time,age,gender,bib_number\n"
        "1,John Doe,18:30,,,\n"
        "2,Jane Smith,19:45,28,F,\n"
    )

    race = loader.load_csv(csv_path)

    assert len(race.results) == 2

    # First result with missing optional fields
    assert race.results[0].place == 1
    assert race.results[0].name == "John Doe"
    assert race.results[0].time == "18:30"
    assert race.results[0].age is None
    # Empty strings in CSV are loaded as empty strings, not None
    assert race.results[0].gender == ""
    assert race.results[0].bib_number == ""

    # Second result with partial data
    assert race.results[1].age == 28
    assert race.results[1].gender == "F"


def test_load_csv_strips_whitespace(tmp_path):
    """Test that names are stripped of leading/trailing whitespace."""
    loader = RaceResultsLoader()

    # Create test CSV with whitespace
    csv_path = tmp_path / "race.csv"
    csv_path.write_text(
        "place,name,time,age,gender,bib_number\n1,  John Doe  ,18:30,35,M,101\n"
    )

    race = loader.load_csv(csv_path)

    assert race.results[0].name == "John Doe"


def test_load_csv_race_name_from_filename(tmp_path):
    """Test that race name is derived from filename stem."""
    loader = RaceResultsLoader()

    # Create test CSV
    csv_path = tmp_path / "summer_marathon_2024.csv"
    csv_path.write_text(
        "place,name,time,age,gender,bib_number\n1,John Doe,18:30,35,M,101\n"
    )

    race = loader.load_csv(csv_path)

    assert race.name == "summer_marathon_2024"
