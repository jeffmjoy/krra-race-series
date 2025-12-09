"""Command-line interface for the KRRA race series scoring system."""

import argparse
from pathlib import Path

from .age_grading import AgeGradedSeriesScoring, AgeGradingCalculator
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
            "(e.g., 'M_overall,F_30-39,M_50-59,age_graded'). "
            "If not specified, all categories are generated. "
            "Use 'age_graded' to include age-graded combined rankings."
        ),
    )

    parser.add_argument(
        "--age-grading-year",
        type=int,
        default=2020,
        help="Year of WMA age-grading factors to use (only 2020 is available)",
    )

    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.70,
        help=(
            "Minimum confidence score (0.0-1.0) to accept a fuzzy name "
            "match (default: 0.70)"
        ),
    )

    parser.add_argument(
        "--flag-threshold",
        type=float,
        default=0.05,
        help="Max score difference to flag ambiguous matches (default: 0.05)",
    )

    parser.add_argument(
        "--unmatched-report",
        type=Path,
        help="Optional: Export low-confidence/ambiguous matches to CSV for review",
    )

    parser.add_argument(
        "--name-corrections",
        type=Path,
        help="Optional: Path to CSV file with name corrections (race_name,member_name)",
    )

    args = parser.parse_args()

    # Load members
    print(f"Loading members from {args.members}...")
    member_registry = MemberRegistry()
    member_registry.load_from_csv(args.members)
    print(f"Loaded {len(member_registry.get_all_members())} members")

    # Load name corrections if provided
    if args.name_corrections:
        if args.name_corrections.exists():
            print(f"Loading name corrections from {args.name_corrections}...")
            member_registry.load_name_corrections(args.name_corrections)
            print(f"Loaded {len(member_registry.name_corrections)} name corrections")
        else:
            print(f"Warning: Name corrections file not found: {args.name_corrections}")

    # Initialize components
    matcher = FinisherMatcher(
        member_registry,
        min_confidence=args.min_confidence,
        ambiguity_threshold=args.flag_threshold,
    )
    calculator = PointsCalculator()
    series = SeriesScoring()
    age_grading_calc = AgeGradingCalculator(factor_year=args.age_grading_year)
    age_graded_series = AgeGradedSeriesScoring()
    exporter = ResultsExporter()

    # Track flagged matches for reporting
    # Format: (race, name, confidence, reason)
    flagged_matches: list[tuple[str, str, float, str]] = []

    # Process each race
    loader = RaceResultsLoader()
    for race_path in args.races:
        print(f"\nProcessing race: {race_path}...")
        race = loader.load_csv(race_path)
        print(f"  {len(race.results)} finishers")

        # Match finishers
        matches = matcher.match_all(race.results)
        matched_count = sum(1 for m in matches if m.matched)
        unmatched_count = sum(1 for m in matches if not m.matched)
        ambiguous_count = sum(1 for m in matches if m.is_ambiguous)
        low_conf_count = sum(1 for m in matches if m.matched and m.confidence < 0.90)

        print(f"  {matched_count} matched with members")
        if unmatched_count > 0:
            print(f"  ⚠ {unmatched_count} unmatched")
        if ambiguous_count > 0:
            print(f"  ⚠ {ambiguous_count} ambiguous matches")
        if low_conf_count > 0:
            print(f"  ⚠ {low_conf_count} low-confidence matches (<90%)")

        # Track flagged matches (ambiguous or low-confidence only)
        for match in matches:
            if match.matched and match.is_ambiguous:
                member_name = match.member.full_name if match.member else "N/A"
                flagged_matches.append(
                    (
                        race.name,
                        match.race_result.name,
                        match.confidence,
                        f"ambiguous (matched: {member_name})",
                    )
                )
            elif match.matched and match.confidence < 0.90:
                member_name = match.member.full_name if match.member else "N/A"
                flagged_matches.append(
                    (
                        race.name,
                        match.race_result.name,
                        match.confidence,
                        f"low confidence (matched: {member_name})",
                    )
                )

        # Calculate points
        race_points = calculator.calculate_race_points(matches, race.name)
        series.add_race_points(race_points)

        # Calculate age-graded results
        age_graded_results = []
        for match in matches:
            if match.matched and match.member:
                ag_result = age_grading_calc.calculate_age_graded_result(
                    match.member, match.race_result, race.name
                )
                if ag_result:
                    age_graded_results.append(ag_result)

        age_graded_series.add_age_graded_results(age_graded_results)
        print(f"  {len(age_graded_results)} age-graded results calculated")

    # Calculate category standings
    print("\nCalculating category standings...")
    category_standings = series.calculate_category_standings(member_registry)

    # Determine if age-graded should be included
    include_age_graded = True
    if args.categories:
        requested_categories = [c.strip() for c in args.categories.split(",")]
        # Check if 'age_graded' is in the requested categories
        include_age_graded = "age_graded" in requested_categories
        # Filter out 'age_graded' from category_standings filter
        filtered_categories = [c for c in requested_categories if c != "age_graded"]
        if filtered_categories:
            category_standings = {
                cat: standings
                for cat, standings in category_standings.items()
                if cat in filtered_categories
            }
        print(
            f"Generating {len(category_standings)} requested categories"
            + (" + age-graded" if include_age_graded else "")
        )
    else:
        print(f"Generating all {len(category_standings)} categories + age-graded")

    # Export category results
    print(f"\nExporting category standings to {args.output}/...")
    race_names = series.get_race_names()
    exporter.export_category_standings(category_standings, args.output, race_names)

    # Calculate and export age-graded standings
    if include_age_graded:
        print("\nCalculating age-graded standings...")
        age_graded_standings = age_graded_series.calculate_age_graded_standings()
        print(f"  {len(age_graded_standings)} members ranked")

        age_graded_output = args.output / "age_graded.csv"
        age_graded_race_names = age_graded_series.get_race_names()
        exporter.export_age_graded_standings(
            age_graded_standings, age_graded_output, age_graded_race_names
        )
        print(f"✓ Age-graded standings exported to {age_graded_output}")

        # Display age-graded summary
        print("\nAge-Graded Standings Summary:")
        for i, ag_total in enumerate(age_graded_standings[:5], start=1):
            print(
                f"  {i}. {ag_total.member_name} - "
                f"{ag_total.average_age_graded_percentage:.2f}% "
                f"({ag_total.races_completed} races)"
            )
        if len(age_graded_standings) > 5:
            print(f"  ... and {len(age_graded_standings) - 5} more")

    # Display summary for each category
    print("\nCategory Standings Summary:")
    for category_name in sorted(category_standings.keys()):
        cat_totals = category_standings[category_name]
        print(f"\n{category_name}:")
        for i, cat_total in enumerate(cat_totals[:5], start=1):
            print(
                f"  {i}. {cat_total.member_name} - {cat_total.total_points} points "
                f"({cat_total.races_completed} races)"
            )
        if len(cat_totals) > 5:
            print(f"  ... and {len(cat_totals) - 5} more")

    # Export unmatched report if requested
    if args.unmatched_report and flagged_matches:
        print(f"\nExporting flagged matches to {args.unmatched_report}...")
        import csv

        args.unmatched_report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.unmatched_report, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(["Race", "Name", "Confidence", "Reason"])
            for race_name, name, confidence, reason in flagged_matches:
                writer.writerow([race_name, name, f"{confidence:.2f}", reason])
        print(f"✓ {len(flagged_matches)} flagged matches exported")
    elif flagged_matches:
        print(
            f"\n⚠ {len(flagged_matches)} flagged matches "
            f"(use --unmatched-report to export details)"
        )

    print(f"\n✓ Complete! Category standings exported to {args.output}/")


if __name__ == "__main__":
    main()
