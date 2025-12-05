"""Module for calculating age-graded performance percentages.

This module implements WMA (World Masters Athletics) age-grading calculations
for running races, based on the 2020 age-grading factors.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .members import Member
    from .race_results import RaceResult


class RaceDistance(Enum):
    """Standard race distances supported for age-grading."""

    KM_5 = "5K"
    KM_8 = "8K"
    KM_10 = "10K"
    HALF_MARATHON = "Half Marathon"
    MARATHON = "Marathon"


# WMA 2020 Age-Grading Factors
# These are multiplicative factors for converting actual time to age-graded time
# Format: {distance: {gender: {age: factor}}}
# Factor represents the ratio: (open_standard / age_standard)
# where open_standard is the world-class time for that distance
# A higher factor means the age standard is slower (older age)

# World-class reference times (in seconds) for open age group
# These are approximate based on world records and WMA standards
WORLD_CLASS_TIMES = {
    RaceDistance.KM_5: {
        "M": 12 * 60 + 51,  # 12:51 (approximate)
        "F": 14 * 60 + 44,  # 14:44 (approximate)
    },
    RaceDistance.KM_8: {
        "M": 21 * 60 + 15,  # 21:15 (approximate)
        "F": 24 * 60 + 30,  # 24:30 (approximate)
    },
    RaceDistance.KM_10: {
        "M": 26 * 60 + 24,  # 26:24 (approximate)
        "F": 29 * 60 + 43,  # 29:43 (approximate)
    },
    RaceDistance.HALF_MARATHON: {
        "M": 58 * 60 + 1,  # 58:01 (approximate)
        "F": 65 * 60 + 15,  # 1:05:15 (approximate)
    },
    RaceDistance.MARATHON: {
        "M": 2 * 3600 + 0 * 60 + 35,  # 2:00:35 (approximate)
        "F": 2 * 3600 + 11 * 60 + 53,  # 2:11:53 (approximate)
    },
}

# Simplified age-grading factors based on WMA 2020 tables
# For a complete implementation, you would load all factors from WMA tables
# These are sample factors showing the general pattern
AGE_GRADING_FACTORS = {
    RaceDistance.KM_5: {
        "M": {
            # Age: factor (simplified - actual tables have year-by-year)
            20: 1.000,
            25: 1.000,
            30: 1.005,
            35: 1.020,
            40: 1.048,
            45: 1.089,
            50: 1.147,
            55: 1.222,
            60: 1.318,
            65: 1.442,
            70: 1.602,
            75: 1.810,
            80: 2.088,
            85: 2.458,
        },
        "F": {
            20: 1.000,
            25: 1.000,
            30: 1.008,
            35: 1.027,
            40: 1.058,
            45: 1.102,
            50: 1.163,
            55: 1.244,
            60: 1.349,
            65: 1.485,
            70: 1.661,
            75: 1.890,
            80: 2.188,
            85: 2.576,
        },
    },
    RaceDistance.KM_8: {
        "M": {
            20: 1.000,
            25: 1.000,
            30: 1.006,
            35: 1.022,
            40: 1.052,
            45: 1.096,
            50: 1.158,
            55: 1.239,
            60: 1.343,
            65: 1.477,
            70: 1.650,
            75: 1.873,
            80: 2.164,
            85: 2.546,
        },
        "F": {
            20: 1.000,
            25: 1.000,
            30: 1.009,
            35: 1.029,
            40: 1.062,
            45: 1.109,
            50: 1.174,
            55: 1.260,
            60: 1.372,
            65: 1.516,
            70: 1.701,
            75: 1.940,
            80: 2.251,
            85: 2.653,
        },
    },
    RaceDistance.KM_10: {
        "M": {
            20: 1.000,
            25: 1.000,
            30: 1.007,
            35: 1.024,
            40: 1.056,
            45: 1.103,
            50: 1.169,
            55: 1.256,
            60: 1.368,
            65: 1.512,
            70: 1.698,
            75: 1.936,
            80: 2.240,
            85: 2.634,
        },
        "F": {
            20: 1.000,
            25: 1.000,
            30: 1.010,
            35: 1.031,
            40: 1.066,
            45: 1.116,
            50: 1.185,
            55: 1.276,
            60: 1.395,
            65: 1.547,
            70: 1.741,
            75: 1.990,
            80: 2.314,
            85: 2.730,
        },
    },
    RaceDistance.HALF_MARATHON: {
        "M": {
            20: 1.000,
            25: 1.000,
            30: 1.009,
            35: 1.028,
            40: 1.064,
            45: 1.117,
            50: 1.191,
            55: 1.289,
            60: 1.418,
            65: 1.582,
            70: 1.792,
            75: 2.062,
            80: 2.408,
            85: 2.850,
        },
        "F": {
            20: 1.000,
            25: 1.000,
            30: 1.012,
            35: 1.035,
            40: 1.074,
            45: 1.130,
            50: 1.207,
            55: 1.308,
            60: 1.441,
            65: 1.609,
            70: 1.821,
            75: 2.090,
            80: 2.440,
            85: 2.884,
        },
    },
    RaceDistance.MARATHON: {
        "M": {
            20: 1.000,
            25: 1.000,
            30: 1.011,
            35: 1.032,
            40: 1.072,
            45: 1.131,
            50: 1.213,
            55: 1.322,
            60: 1.468,
            65: 1.652,
            70: 1.886,
            75: 2.188,
            80: 2.576,
            85: 3.066,
        },
        "F": {
            20: 1.000,
            25: 1.000,
            30: 1.014,
            35: 1.039,
            40: 1.082,
            45: 1.144,
            50: 1.229,
            55: 1.340,
            60: 1.487,
            65: 1.671,
            70: 1.901,
            75: 2.190,
            80: 2.566,
            85: 3.038,
        },
    },
}


def infer_race_distance(race_name: str) -> RaceDistance | None:
    """Infer the race distance from the race name.

    Args:
        race_name: Name of the race (typically from filename)

    Returns:
        RaceDistance enum value or None if distance cannot be determined

    Examples:
        >>> infer_race_distance("spring_5k")
        RaceDistance.KM_5
        >>> infer_race_distance("county_half_marathon")
        RaceDistance.HALF_MARATHON
    """
    race_name_lower = race_name.lower()

    # Check for specific patterns
    if "5k" in race_name_lower or "5_k" in race_name_lower:
        return RaceDistance.KM_5
    elif "8k" in race_name_lower or "8_k" in race_name_lower:
        return RaceDistance.KM_8
    elif "10k" in race_name_lower or "10_k" in race_name_lower:
        return RaceDistance.KM_10
    elif "half" in race_name_lower or "half_marathon" in race_name_lower:
        return RaceDistance.HALF_MARATHON
    elif "marathon" in race_name_lower and "half" not in race_name_lower:
        return RaceDistance.MARATHON

    # Try to extract distance from patterns like "charity_9k" -> closest standard
    match = re.search(r"(\d+)k", race_name_lower)
    if match:
        km = int(match.group(1))
        if km <= 6:
            return RaceDistance.KM_5
        elif km <= 9:
            return RaceDistance.KM_8
        elif km <= 15:
            return RaceDistance.KM_10
        elif km <= 25:
            return RaceDistance.HALF_MARATHON
        else:
            return RaceDistance.MARATHON

    return None


def get_age_factor(distance: RaceDistance, age: int, gender: str) -> float:
    """Get the age-grading factor for a given distance, age, and gender.

    Interpolates between known age values if exact age is not in the table.

    Args:
        distance: Race distance
        age: Athlete's age
        gender: Athlete's gender ('M' or 'F')

    Returns:
        Age-grading factor (ratio of open standard to age standard)
    """
    if distance not in AGE_GRADING_FACTORS:
        return 1.0

    gender_factors = AGE_GRADING_FACTORS[distance].get(gender, {})
    if not gender_factors:
        return 1.0

    # If exact age is in the table, return it
    if age in gender_factors:
        return gender_factors[age]

    # Find the two nearest ages and interpolate
    ages = sorted(gender_factors.keys())

    # If age is less than minimum, use minimum factor
    if age < ages[0]:
        return gender_factors[ages[0]]

    # If age is greater than maximum, use maximum factor
    if age > ages[-1]:
        return gender_factors[ages[-1]]

    # Find the two surrounding ages
    for i in range(len(ages) - 1):
        if ages[i] <= age <= ages[i + 1]:
            age_low = ages[i]
            age_high = ages[i + 1]
            factor_low = gender_factors[age_low]
            factor_high = gender_factors[age_high]

            # Linear interpolation
            ratio = (age - age_low) / (age_high - age_low)
            return factor_low + ratio * (factor_high - factor_low)

    return 1.0


def time_to_seconds(time_str: str) -> float:
    """Convert a time string to seconds.

    Supports formats:
    - MM:SS (e.g., "18:30" -> 1110.0)
    - HH:MM:SS (e.g., "1:15:30" -> 4530.0)
    - MM:SS.ms (e.g., "18:30.5" -> 1110.5)

    Args:
        time_str: Time string in one of the supported formats

    Returns:
        Time in seconds as a float
    """
    parts = time_str.split(":")
    if len(parts) == 2:
        # MM:SS format
        minutes = float(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # HH:MM:SS format
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")


@dataclass
class AgeGradedResult:
    """Age-graded performance result for a race finisher."""

    member_id: str
    member_name: str
    race_name: str
    age: int
    gender: str
    actual_time: str
    actual_seconds: float
    distance: RaceDistance
    age_factor: float
    age_graded_percentage: float
    overall_place: int

    @property
    def age_graded_time_seconds(self) -> float:
        """Calculate the age-graded equivalent time in seconds.

        Returns:
            Age-graded time in seconds (what the performance would be at peak age)
        """
        return self.actual_seconds / self.age_factor


class AgeGradingCalculator:
    """Calculates age-graded performance percentages for race results."""

    def __init__(self, factor_year: int = 2020) -> None:
        """Initialize the age-grading calculator.

        Args:
            factor_year: Year of the age-grading factors to use (default: 2020)
        """
        self.factor_year = factor_year

    def calculate_age_graded_result(
        self,
        member: Member,
        race_result: RaceResult,
        race_name: str,
    ) -> AgeGradedResult | None:
        """Calculate age-graded performance for a single race result.

        Args:
            member: KRRA member who completed the race
            race_result: The member's race result
            race_name: Name of the race

        Returns:
            AgeGradedResult if calculation is possible, None otherwise
        """
        # Check if we have required data
        if not member.age or not member.gender:
            return None

        # Infer race distance
        distance = infer_race_distance(race_name)
        if not distance:
            return None

        # Get age-grading factor
        age_factor = get_age_factor(distance, member.age, member.gender)

        # Convert time to seconds
        try:
            actual_seconds = time_to_seconds(race_result.time)
        except ValueError:
            return None

        # Calculate age-graded percentage
        # Age-graded % = (age_standard_time / actual_time) * 100
        # Since factor = open_standard / age_standard
        # We have: age_standard = open_standard / factor
        # Therefore: age_graded % = (open_standard / factor / actual_time) * 100
        world_class_time = WORLD_CLASS_TIMES.get(distance, {}).get(member.gender)
        if not world_class_time:
            # Fallback to simplified calculation if no world-class time available
            age_graded_percentage = (1.0 / age_factor) * 100.0
        else:
            age_standard_time = world_class_time / age_factor
            age_graded_percentage = (age_standard_time / actual_seconds) * 100.0

        return AgeGradedResult(
            member_id=member.member_id,
            member_name=member.full_name,
            race_name=race_name,
            age=member.age,
            gender=member.gender,
            actual_time=race_result.time,
            actual_seconds=actual_seconds,
            distance=distance,
            age_factor=age_factor,
            age_graded_percentage=age_graded_percentage,
            overall_place=race_result.place,
        )


@dataclass
class AgeGradedSeriesTotal:
    """Cumulative age-graded series total for a member."""

    member_id: str
    member_name: str
    races_completed: int
    average_age_graded_percentage: float
    race_details: list[AgeGradedResult]
    race_percentages_by_race: dict[str, float] | None = None


class AgeGradedSeriesScoring:
    """Manages cumulative age-graded scoring across the race series."""

    def __init__(self) -> None:
        self.all_age_graded_results: list[AgeGradedResult] = []
        self.race_names: list[str] = []

    def add_age_graded_results(self, results: list[AgeGradedResult]) -> None:
        """Add age-graded results from a race to the series.

        Args:
            results: Age-graded results from a race
        """
        self.all_age_graded_results.extend(results)
        # Track race names
        if results:
            race_name = results[0].race_name
            if race_name not in self.race_names:
                self.race_names.append(race_name)

    def get_race_names(self) -> list[str]:
        """Get the list of all race names in the series.

        Returns:
            List of race names in the order they were added
        """
        return self.race_names.copy()

    def calculate_age_graded_standings(
        self, max_races: int | None = None
    ) -> list[AgeGradedSeriesTotal]:
        """Calculate age-graded standings combining all genders.

        Uses the average of the member's best age-graded percentages.
        Tie-break by number of races completed (more races wins).

        Args:
            max_races: Maximum number of races to count. If None, all races
                       are included (default).

        Returns:
            List of age-graded series totals sorted by average percentage (descending)
        """
        # Group results by member
        member_results: dict[str, list[AgeGradedResult]] = {}

        for result in self.all_age_graded_results:
            if result.member_id not in member_results:
                member_results[result.member_id] = []
            member_results[result.member_id].append(result)

        # Calculate totals
        totals = []
        for member_id, results_list in member_results.items():
            member_name = results_list[0].member_name if results_list else "Unknown"

            # Sort by age-graded percentage and take top N races
            sorted_results = sorted(
                results_list,
                key=lambda x: x.age_graded_percentage,
                reverse=True,
            )
            if max_races is not None:
                counted_races = sorted_results[:max_races]
            else:
                counted_races = sorted_results

            # Calculate average age-graded percentage
            avg_percentage = sum(r.age_graded_percentage for r in counted_races) / len(
                counted_races
            )

            # Build per-race percentage mapping
            race_percentages = {
                result.race_name: result.age_graded_percentage
                for result in results_list
            }

            total = AgeGradedSeriesTotal(
                member_id=member_id,
                member_name=member_name,
                races_completed=len(counted_races),
                average_age_graded_percentage=avg_percentage,
                race_details=counted_races,
                race_percentages_by_race=race_percentages,
            )
            totals.append(total)

        # Sort by average percentage (descending), then by races completed (descending)
        totals.sort(
            key=lambda x: (x.average_age_graded_percentage, x.races_completed),
            reverse=True,
        )

        return totals
