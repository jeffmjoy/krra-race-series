"""Module for exporting race series results."""

import csv
from pathlib import Path
from typing import List

from .scoring import SeriesTotal


class ResultsExporter:
    """Exports race series results to various formats."""
    
    def export_to_csv(self, series_totals: List[SeriesTotal], 
                     output_path: Path) -> None:
        """Export series totals to a CSV file.
        
        Args:
            series_totals: List of series totals to export
            output_path: Path where the CSV file will be written
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Rank', 'Member ID', 'Name', 'Races', 'Total Points'])
            
            # Write data
            for rank, total in enumerate(series_totals, start=1):
                writer.writerow([
                    rank,
                    total.member_id,
                    total.member_name,
                    total.races_completed,
                    total.total_points
                ])
    
    def export_detailed_csv(self, series_totals: List[SeriesTotal],
                           output_path: Path) -> None:
        """Export detailed series results including individual race points.
        
        Args:
            series_totals: List of series totals to export
            output_path: Path where the CSV file will be written
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Rank', 'Member ID', 'Name', 'Race', 'Place', 
                           'Points', 'Total Points'])
            
            # Write data
            for rank, total in enumerate(series_totals, start=1):
                if total.race_details:
                    for race_points in total.race_details:
                        writer.writerow([
                            rank,
                            total.member_id,
                            total.member_name,
                            race_points.race_name,
                            race_points.place,
                            race_points.points,
                            total.total_points
                        ])
                else:
                    # No races completed
                    writer.writerow([
                        rank,
                        total.member_id,
                        total.member_name,
                        '',
                        '',
                        '',
                        total.total_points
                    ])
