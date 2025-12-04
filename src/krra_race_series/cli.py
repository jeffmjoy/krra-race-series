"""Command-line interface for the KRRA race series scoring system."""

import argparse
from pathlib import Path

from .export import ResultsExporter
from .matching import FinisherMatcher
from .members import MemberRegistry
from .race_results import RaceResultsLoader
from .scoring import PointsCalculator, SeriesScoring


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="KRRA Race Series Scoring System")

    parser.add_argument(
        "--members", type=Path, required=True, help="Path to the members CSV file"
    )

    parser.add_argument(
        "--races",
        type=Path,
        nargs="+",
        required=True,
        help="Path(s) to race results CSV file(s)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output"),
        help="Directory for category standings output files (default: data/output)",
    )

    parser.add_argument(
        "--categories",
        type=str,
        help=(
            "Comma-separated list of categories to generate "
            "(e.g., 'M_overall,F_30-39,M_50-59'). "
            "If not specified, all categories are generated."
        ),
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

    # Calculate category standings
    print("\nCalculating category standings...")
    category_standings = series.calculate_category_standings(member_registry)

    # Filter categories if specified
    if args.categories:
        requested_categories = [c.strip() for c in args.categories.split(",")]
        category_standings = {
            cat: standings
            for cat, standings in category_standings.items()
            if cat in requested_categories
        }
        print(f"Generating {len(category_standings)} requested categories")
    else:
        print(f"Generating all {len(category_standings)} categories")

    # Export category results
    print(f"\nExporting category standings to {args.output}/...")
    race_names = series.get_race_names()
    exporter.export_category_standings(category_standings, args.output, race_names)

    # Display summary for each category
    print("\nCategory Standings Summary:")
    for category_name in sorted(category_standings.keys()):
        totals = category_standings[category_name]
        print(f"\n{category_name}:")
        for i, total in enumerate(totals[:5], start=1):
            print(
                f"  {i}. {total.member_name} - {total.total_points} points "
                f"({total.races_completed} races)"
            )
        if len(totals) > 5:
            print(f"  ... and {len(totals) - 5} more")

    print(f"\n✓ Complete! Category standings exported to {args.output}/")


if __name__ == "__main__":
    main()
