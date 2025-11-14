"""Command-line interface for the KRRA race series scoring system."""

import argparse
from pathlib import Path

from .members import MemberRegistry
from .race_results import RaceResultsLoader
from .matching import FinisherMatcher
from .scoring import PointsCalculator, SeriesScoring
from .export import ResultsExporter


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='KRRA Race Series Scoring System'
    )
    
    parser.add_argument(
        '--members',
        type=Path,
        required=True,
        help='Path to the members CSV file'
    )
    
    parser.add_argument(
        '--races',
        type=Path,
        nargs='+',
        required=True,
        help='Path(s) to race results CSV file(s)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/output/series_results.csv'),
        help='Path for the output CSV file'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Export detailed results with individual race points'
    )
    
    args = parser.parse_args()
    
    # Load members
    print(f"Loading members from {args.members}...")
    member_registry = MemberRegistry()
    member_registry.load_from_csv(args.members)
    print(f"Loaded {len(member_registry.get_all_members())} members")
    
    # Initialize components
    matcher = FinisherMatcher(member_registry)
    calculator = PointsCalculator()
    series = SeriesScoring()
    exporter = ResultsExporter()
    
    # Process each race
    loader = RaceResultsLoader()
    for race_path in args.races:
        print(f"\nProcessing race: {race_path}...")
        race = loader.load_csv(race_path)
        print(f"  {len(race.results)} finishers")
        
        # Match finishers
        matches = matcher.match_all(race.results)
        matched_count = sum(1 for m in matches if m.matched)
        print(f"  {matched_count} matched with members")
        
        # Calculate points
        race_points = calculator.calculate_race_points(matches, race.name)
        series.add_race_points(race_points)
    
    # Calculate series totals
    print("\nCalculating series totals...")
    totals = series.calculate_series_totals(member_registry)
    
    # Export results
    print(f"\nExporting results to {args.output}...")
    if args.detailed:
        exporter.export_detailed_csv(totals, args.output)
    else:
        exporter.export_to_csv(totals, args.output)
    
    print("\nTop 10 standings:")
    for i, total in enumerate(totals[:10], start=1):
        print(f"  {i}. {total.member_name} - {total.total_points} points "
              f"({total.races_completed} races)")
    
    print(f"\n✓ Complete! Results exported to {args.output}")


if __name__ == '__main__':
    main()
