"""Module for ingesting and processing race result files."""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional


@dataclass
class RaceResult:
    """Represents a single finisher's result in a race."""

    place: int
    name: str
    time: str
    age: Optional[int] = None
    gender: Optional[str] = None
    bib_number: Optional[str] = None


@dataclass
class Race:
    """Represents a race event with all finishers."""

    name: str
    date: date
    results: List[RaceResult]


class RaceResultsLoader:
    """Loads race results from CSV files."""

    def load_csv(self, filepath: Path) -> Race:
        """Load race results from a CSV file.

        Args:
            filepath: Path to the CSV file containing race results

        Returns:
            Race object with all finishers

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the CSV format is invalid
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Race results file not found: {filepath}")

        results = []
        race_name = filepath.stem
        race_date = date.today()  # TODO: Extract from filename or file content

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                result = RaceResult(
                    place=int(row.get("place", 0)),
                    name=row.get("name", "").strip(),
                    time=row.get("time", ""),
                    age=int(row["age"]) if row.get("age") else None,
                    gender=row.get("gender"),
                    bib_number=row.get("bib_number"),
                )
                results.append(result)

        return Race(name=race_name, date=race_date, results=results)
