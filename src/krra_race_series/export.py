"""Module for exporting race series results."""

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .scoring import SeriesTotal

if TYPE_CHECKING:
    from .age_grading import AgeGradedSeriesTotal


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
        self,
        series_totals: list[SeriesTotal],
        output_path: Path,
        race_names: list[str] | None = None,
    ) -> None:
        """Export series totals to a CSV file.

        Args:
            series_totals: List of series totals to export
            output_path: Path where the CSV file will be written
            race_names: Optional list of race names for individual columns.
                        If provided, creates columns for each race instead of
                        a single "Races" column.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

            # Write header
            if race_names:
                header = ["Rank", "Member ID", "Name"] + race_names + ["Total Points"]
            else:
                header = ["Rank", "Member ID", "Name", "Races", "Total Points"]
            writer.writerow(header)

            # Write data
            for rank, total in enumerate(series_totals, start=1):
                if race_names and total.race_points_by_race is not None:
                    race_columns = [
                        total.race_points_by_race.get(race, "") for race in race_names
                    ]
                    writer.writerow(
                        [
                            rank,
                            self._sanitize_csv_field(total.member_id),
                            self._sanitize_csv_field(total.member_name),
                        ]
                        + race_columns
                        + [total.total_points]
                    )
                else:
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

    def export_category_standings(
        self,
        category_standings: dict[str, list[SeriesTotal]],
        output_dir: Path,
        race_names: list[str] | None = None,
    ) -> None:
        """Export category-specific standings to separate CSV files.

        Creates one CSV file per category (e.g., M_overall.csv, F_30-39.csv).

        Args:
            category_standings: Dictionary mapping category names to series totals
            output_dir: Directory where category CSV files will be written
            race_names: Optional list of race names for individual columns.
                        If provided, creates columns for each race instead of
                        a single "Races" column.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for category_name, totals in category_standings.items():
            output_path = output_dir / f"{category_name}.csv"

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

                # Write header
                if race_names:
                    header = (
                        ["Rank", "Member ID", "Name"] + race_names + ["Total Points"]
                    )
                else:
                    header = ["Rank", "Member ID", "Name", "Races", "Total Points"]
                writer.writerow(header)

                # Write data
                for rank, total in enumerate(totals, start=1):
                    if race_names and total.race_points_by_race is not None:
                        race_columns = [
                            total.race_points_by_race.get(race, "")
                            for race in race_names
                        ]
                        writer.writerow(
                            [
                                rank,
                                self._sanitize_csv_field(total.member_id),
                                self._sanitize_csv_field(total.member_name),
                            ]
                            + race_columns
                            + [total.total_points]
                        )
                    else:
                        writer.writerow(
                            [
                                rank,
                                self._sanitize_csv_field(total.member_id),
                                self._sanitize_csv_field(total.member_name),
                                total.races_completed,
                                total.total_points,
                            ]
                        )

    def export_age_graded_standings(
        self,
        standings: list["AgeGradedSeriesTotal"],
        output_path: Path,
        race_names: list[str] | None = None,
    ) -> None:
        """Export age-graded standings to a CSV file.

        Args:
            standings: List of age-graded series totals to export
            output_path: Path where the CSV file will be written
            race_names: Optional list of race names for individual columns.
                        If provided, creates columns for each race showing
                        the age-graded percentage for that race.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

            # Write header
            if race_names:
                header = ["Rank", "Member ID", "Name"] + race_names + ["Avg %"]
            else:
                header = ["Rank", "Member ID", "Name", "Races", "Avg %"]
            writer.writerow(header)

            # Write data
            for rank, total in enumerate(standings, start=1):
                if race_names and total.race_percentages_by_race is not None:
                    race_columns = [
                        f"{total.race_percentages_by_race[race]:.2f}"
                        if race in total.race_percentages_by_race
                        else ""
                        for race in race_names
                    ]
                    writer.writerow(
                        [
                            rank,
                            self._sanitize_csv_field(total.member_id),
                            self._sanitize_csv_field(total.member_name),
                        ]
                        + race_columns
                        + [f"{total.average_age_graded_percentage:.2f}"]
                    )
                else:
                    writer.writerow(
                        [
                            rank,
                            self._sanitize_csv_field(total.member_id),
                            self._sanitize_csv_field(total.member_name),
                            total.races_completed,
                            f"{total.average_age_graded_percentage:.2f}",
                        ]
                    )
