"""Module for exporting race series results."""

import csv
from pathlib import Path
from typing import Any

from .scoring import SeriesTotal


class ResultsExporter:
    """Exports race series results to various formats."""

    @staticmethod
    def _sanitize_csv_field(value: Any) -> Any:
        """Sanitize a CSV field to prevent formula injection.

        Args:
            value: The value to sanitize

        Returns:
            Sanitized value safe for CSV export
        """
        if not isinstance(value, str):
            return value

        # Check if the string starts with formula characters
        if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
            # Prepend with a single quote to prevent formula execution
            return "'" + value

        return value

    def export_to_csv(
        self, series_totals: list[SeriesTotal], output_path: Path
    ) -> None:
        """Export series totals to a CSV file.

        Args:
            series_totals: List of series totals to export
            output_path: Path where the CSV file will be written
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

            # Write header
            writer.writerow(["Rank", "Member ID", "Name", "Races", "Total Points"])

            # Write data
            for rank, total in enumerate(series_totals, start=1):
                writer.writerow(
                    [
                        rank,
                        self._sanitize_csv_field(total.member_id),
                        self._sanitize_csv_field(total.member_name),
                        total.races_completed,
                        total.total_points,
                    ]
                )

    def export_detailed_csv(
        self, series_totals: list[SeriesTotal], output_path: Path
    ) -> None:
        """Export detailed series results including individual race points.

        Args:
            series_totals: List of series totals to export
            output_path: Path where the CSV file will be written
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

            # Write header
            writer.writerow(
                [
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
            )

            # Write data
            for rank, total in enumerate(series_totals, start=1):
                if total.race_details:
                    for race_points in total.race_details:
                        age_group_str = (
                            race_points.age_group.value if race_points.age_group else ""
                        )
                        writer.writerow(
                            [
                                rank,
                                self._sanitize_csv_field(total.member_id),
                                self._sanitize_csv_field(total.member_name),
                                self._sanitize_csv_field(race_points.race_name),
                                race_points.overall_place,
                                race_points.overall_points,
                                age_group_str,
                                race_points.age_group_place or "",
                                race_points.age_group_points,
                                race_points.total_points,
                                total.total_points,
                            ]
                        )
                else:
                    # No races completed
                    writer.writerow(
                        [
                            rank,
                            self._sanitize_csv_field(total.member_id),
                            self._sanitize_csv_field(total.member_name),
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            total.total_points,
                        ]
                    )
