"""Module for calculating race series points."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .matching import MatchResult

if TYPE_CHECKING:
    from .members import MemberRegistry


class RaceType(Enum):
    """Type of race based on points awarded."""

    RACE_100 = 100  # Major races: Half Marathon, County Marathon
    RACE_75 = 75  # Standard races: 5K, 8K, 10K, etc.


class AgeGroup(Enum):
    """Age group categories for race series."""

    UNDER_20 = "<=19"
    AGE_20_29 = "20-29"
    AGE_30_39 = "30-39"
    AGE_40_49 = "40-49"
    AGE_50_59 = "50-59"
    AGE_60_69 = "60-69"
    AGE_70_79 = "70-79"
    AGE_80_PLUS = "80+"

    @staticmethod
    def from_age(age: int | None) -> AgeGroup | None:
        """Determine age group from age.

        Args:
            age: Age of the participant

        Returns:
            Corresponding AgeGroup or None if age is not provided
        """
        if age is None:
            return None

        if age <= 19:
            return AgeGroup.UNDER_20
        elif age <= 29:
            return AgeGroup.AGE_20_29
        elif age <= 39:
            return AgeGroup.AGE_30_39
        elif age <= 49:
            return AgeGroup.AGE_40_49
        elif age <= 59:
            return AgeGroup.AGE_50_59
        elif age <= 69:
            return AgeGroup.AGE_60_69
        elif age <= 79:
            return AgeGroup.AGE_70_79
        else:
            return AgeGroup.AGE_80_PLUS


@dataclass
class PointsConfig:
    """Configuration for the points scoring system."""

    race_type: RaceType = RaceType.RACE_75

    def calculate_overall_points(self, place: int) -> int:
        """Calculate overall points for a given finishing place.

        Args:
            place: Overall finishing position (1-indexed)

        Returns:
            Points awarded for that position

        Based on KRRA scoring:
        - 100-point races: 1st=100, 2nd=98, 3rd=96...decreasing by 2 until place 11
          Then decreasing by 1 from 11th onward, minimum 1 point
        - 75-point races: 1st=75, 2nd=73, 3rd=71...decreasing by 2 until place 11
          Then decreasing by 1 from 11th onward, minimum 1 point
        """
        if self.race_type == RaceType.RACE_100:
            if place == 1:
                return 100
            elif place <= 10:
                return 100 - (place - 1) * 2
            elif place <= 91:
                return 82 - (place - 10)
            else:
                return 1
        else:  # RACE_75
            if place == 1:
                return 75
            elif place <= 10:
                return 75 - (place - 1) * 2
            elif place <= 66:
                return 57 - (place - 10)
            else:
                return 1

    def calculate_age_group_points(self, place_in_age_group: int) -> int:
        """Calculate age group points for a given place within the age group.

        Args:
            place_in_age_group: Position within age/gender group (1-indexed)

        Returns:
            Points awarded for that position in age group

        Based on KRRA scoring:
        - 100-point races: 1st=20, 2nd=19...decreasing by 1 until 20th,
          then 1 point
        - 75-point races: 1st=15, 2nd=14...decreasing by 1 until 15th,
          then 1 point
        """
        max_points = 20 if self.race_type == RaceType.RACE_100 else 15

        if place_in_age_group <= max_points:
            return max_points - (place_in_age_group - 1)
        else:
            return 1


@dataclass
class RacePoints:
    """Points earned by a member in a single race."""

    member_id: str
    race_name: str
    overall_place: int
    overall_points: int
    age_group: AgeGroup | None = None
    age_group_place: int | None = None
    age_group_points: int = 0
    gender: str | None = None

    @property
    def total_points(self) -> int:
        """Return total points (overall + age group)."""
        return self.overall_points + self.age_group_points


class PointsCalculator:
    """Calculates points for race results."""

    def __init__(self, config: PointsConfig | None = None) -> None:
        """Initialize the calculator with a points configuration.

        Args:
            config: Points configuration. Uses default if not provided.
        """
        self.config = config or PointsConfig()

    def calculate_race_points(
        self, match_results: list[MatchResult], race_name: str
    ) -> list[RacePoints]:
        """Calculate points for all matched finishers in a race.

        Calculates both overall points and age group points for each finisher.

        Args:
            match_results: List of matched race results
            race_name: Name of the race

        Returns:
            List of points earned by each matched member
        """
        race_points = []
        matched_results = [
            match for match in match_results if match.matched and match.member
        ]

        # Calculate overall points
        for match in matched_results:
            if not match.member:
                continue

            overall_points = self.config.calculate_overall_points(
                match.race_result.place
            )

            # Determine age group
            age_group = AgeGroup.from_age(match.member.age)

            race_points.append(
                RacePoints(
                    member_id=match.member.member_id,
                    race_name=race_name,
                    overall_place=match.race_result.place,
                    overall_points=overall_points,
                    age_group=age_group,
                    gender=match.member.gender,
                )
            )

        # Calculate age group points
        self._calculate_age_group_points(race_points)

        return race_points

    def _calculate_age_group_points(self, race_points: list[RacePoints]) -> None:
        """Calculate age group points for finishers.

        Groups finishers by age group and gender, then assigns points based
        on their position within that group.

        Args:
            race_points: List of RacePoints to update with age group points
        """
        # Group by age group and gender
        groups: dict[tuple[AgeGroup | None, str | None], list[RacePoints]] = {}

        for rp in race_points:
            key = (rp.age_group, rp.gender)
            if key not in groups:
                groups[key] = []
            groups[key].append(rp)

        # Sort each group by overall place and assign age group points
        for _group_key, group_members in groups.items():
            # Sort by overall place
            group_members.sort(key=lambda x: x.overall_place)

            # Assign age group points based on position within group
            for idx, rp in enumerate(group_members, start=1):
                rp.age_group_place = idx
                rp.age_group_points = self.config.calculate_age_group_points(idx)


@dataclass
class SeriesTotal:
    """Cumulative series total for a member."""

    member_id: str
    member_name: str
    races_completed: int
    total_points: int
    race_details: list[RacePoints]


class SeriesScoring:
    """Manages cumulative scoring across the race series."""

    def __init__(self) -> None:
        self.all_race_points: list[RacePoints] = []

    def add_race_points(self, race_points: list[RacePoints]) -> None:
        """Add points from a race to the series.

        Args:
            race_points: Points earned in a race
        """
        self.all_race_points.extend(race_points)

    def calculate_series_totals(
        self, member_registry: MemberRegistry, max_races: int = 7
    ) -> list[SeriesTotal]:
        """Calculate cumulative totals for all members.

        Args:
            member_registry: Registry to get member names
            max_races: Maximum number of races that count (default 7)

        Returns:
            List of series totals sorted by total points (descending)
        """
        # Group points by member
        member_points: dict[str, list[RacePoints]] = {}

        for race_point in self.all_race_points:
            if race_point.member_id not in member_points:
                member_points[race_point.member_id] = []
            member_points[race_point.member_id].append(race_point)

        # Calculate totals
        totals = []
        for member_id, points_list in member_points.items():
            member = next(
                (
                    m
                    for m in member_registry.get_all_members()
                    if m.member_id == member_id
                ),
                None,
            )
            member_name = member.full_name if member else "Unknown"

            # Sort races by total points and take top N races
            sorted_points = sorted(
                points_list, key=lambda x: x.total_points, reverse=True
            )
            counted_races = sorted_points[:max_races]

            total = SeriesTotal(
                member_id=member_id,
                member_name=member_name,
                races_completed=len(counted_races),
                total_points=sum(p.total_points for p in counted_races),
                race_details=counted_races,
            )
            totals.append(total)

        # Sort by total points (descending)
        totals.sort(key=lambda x: x.total_points, reverse=True)

        return totals
