"""Tests for age-grading calculations."""

import pytest

from krra_race_series.age_grading import (
    AGE_GRADING_FACTORS,
    AgeGradedResult,
    AgeGradedSeriesScoring,
    AgeGradingCalculator,
    RaceDistance,
    get_age_factor,
    infer_race_distance,
    time_to_seconds,
)
from krra_race_series.members import Member
from krra_race_series.race_results import RaceResult


def test_infer_race_distance_5k() -> None:
    """Test distance inference for 5K races."""
    assert infer_race_distance("spring_5k") == RaceDistance.KM_5
    assert infer_race_distance("winter_5K") == RaceDistance.KM_5
    assert infer_race_distance("charity_5_k") == RaceDistance.KM_5


def test_infer_race_distance_8k() -> None:
    """Test distance inference for 8K races."""
    assert infer_race_distance("summer_8k") == RaceDistance.KM_8
    assert infer_race_distance("charity_8K") == RaceDistance.KM_8


def test_infer_race_distance_10k() -> None:
    """Test distance inference for 10K races."""
    assert infer_race_distance("fall_10k") == RaceDistance.KM_10
    assert infer_race_distance("city_10K") == RaceDistance.KM_10


def test_infer_race_distance_half_marathon() -> None:
    """Test distance inference for half marathon races."""
    assert infer_race_distance("county_half_marathon") == RaceDistance.HALF_MARATHON
    assert infer_race_distance("spring_half") == RaceDistance.HALF_MARATHON


def test_infer_race_distance_marathon() -> None:
    """Test distance inference for marathon races."""
    assert infer_race_distance("city_marathon") == RaceDistance.MARATHON
    assert infer_race_distance("boston_marathon") == RaceDistance.MARATHON


def test_infer_race_distance_approximate_distances() -> None:
    """Test distance inference for non-standard distances."""
    # 9K should map to closest standard (8K or 10K)
    result = infer_race_distance("charity_9k")
    assert result in [RaceDistance.KM_8, RaceDistance.KM_10]


def test_infer_race_distance_unknown() -> None:
    """Test distance inference for unknown race formats."""
    assert infer_race_distance("unknown_race") is None
    assert infer_race_distance("obstacle_course") is None


def test_get_age_factor_exact_age() -> None:
    """Test getting age factor for exact age in table."""
    factor_35_male = get_age_factor(RaceDistance.KM_5, 35, "M")
    assert factor_35_male == 1.020

    factor_50_female = get_age_factor(RaceDistance.KM_5, 50, "F")
    assert factor_50_female == 1.163


def test_get_age_factor_interpolation() -> None:
    """Test age factor interpolation for ages between table values."""
    # Age 37 is between 35 (1.020) and 40 (1.048)
    factor_37 = get_age_factor(RaceDistance.KM_5, 37, "M")
    # Should be between 1.020 and 1.048
    assert 1.020 < factor_37 < 1.048


def test_get_age_factor_edge_cases() -> None:
    """Test age factor for edge cases (very young/old)."""
    # Very young age (below table minimum)
    factor_young = get_age_factor(RaceDistance.KM_5, 18, "M")
    assert factor_young == 1.000  # Should use minimum factor

    # Very old age (above table maximum)
    factor_old = get_age_factor(RaceDistance.KM_5, 90, "M")
    assert factor_old == 2.458  # Should use maximum factor


def test_get_age_factor_invalid_distance() -> None:
    """Test age factor for unsupported distance returns 1.0."""
    # RaceDistance enum only has specific distances
    # This tests the fallback behavior
    factor = get_age_factor(RaceDistance.KM_5, 35, "X")  # Invalid gender
    assert factor == 1.0


def test_time_to_seconds_mm_ss() -> None:
    """Test time conversion for MM:SS format."""
    assert time_to_seconds("18:30") == 1110.0
    assert time_to_seconds("05:00") == 300.0


def test_time_to_seconds_hh_mm_ss() -> None:
    """Test time conversion for HH:MM:SS format."""
    assert time_to_seconds("1:15:30") == 4530.0
    assert time_to_seconds("2:30:00") == 9000.0


def test_time_to_seconds_with_decimals() -> None:
    """Test time conversion with decimal seconds."""
    assert time_to_seconds("18:30.5") == 1110.5
    assert time_to_seconds("1:15:30.25") == 4530.25


def test_time_to_seconds_invalid_format() -> None:
    """Test time conversion with invalid format raises error."""
    with pytest.raises(ValueError, match="Invalid time format"):
        time_to_seconds("invalid")


def test_age_grading_calculator_initialization() -> None:
    """Test age-grading calculator initialization."""
    calc = AgeGradingCalculator()
    assert calc.factor_year == 2020

    calc_2022 = AgeGradingCalculator(factor_year=2022)
    assert calc_2022.factor_year == 2022


def test_calculate_age_graded_result_success() -> None:
    """Test successful age-graded result calculation."""
    calc = AgeGradingCalculator()

    member = Member(
        member_id="M001",
        first_name="John",
        last_name="Doe",
        age=35,
        gender="M",
    )

    race_result = RaceResult(
        place=1,
        name="John Doe",
        time="18:30",
        age=35,
        gender="M",
    )

    result = calc.calculate_age_graded_result(member, race_result, "spring_5k")

    assert result is not None
    assert result.member_id == "M001"
    assert result.member_name == "John Doe"
    assert result.age == 35
    assert result.gender == "M"
    assert result.distance == RaceDistance.KM_5
    assert result.actual_seconds == 1110.0
    assert result.age_factor == 1.020
    assert result.age_graded_percentage > 0


def test_calculate_age_graded_result_missing_age() -> None:
    """Test age-graded calculation returns None when age is missing."""
    calc = AgeGradingCalculator()

    member = Member(
        member_id="M001",
        first_name="John",
        last_name="Doe",
        age=None,  # No age
        gender="M",
    )

    race_result = RaceResult(
        place=1,
        name="John Doe",
        time="18:30",
    )

    result = calc.calculate_age_graded_result(member, race_result, "spring_5k")
    assert result is None


def test_calculate_age_graded_result_missing_gender() -> None:
    """Test age-graded calculation returns None when gender is missing."""
    calc = AgeGradingCalculator()

    member = Member(
        member_id="M001",
        first_name="John",
        last_name="Doe",
        age=35,
        gender=None,  # No gender
    )

    race_result = RaceResult(
        place=1,
        name="John Doe",
        time="18:30",
    )

    result = calc.calculate_age_graded_result(member, race_result, "spring_5k")
    assert result is None


def test_calculate_age_graded_result_unknown_distance() -> None:
    """Test age-graded calculation returns None when distance cannot be inferred."""
    calc = AgeGradingCalculator()

    member = Member(
        member_id="M001",
        first_name="John",
        last_name="Doe",
        age=35,
        gender="M",
    )

    race_result = RaceResult(
        place=1,
        name="John Doe",
        time="18:30",
    )

    result = calc.calculate_age_graded_result(member, race_result, "unknown_race")
    assert result is None


def test_calculate_age_graded_result_invalid_time() -> None:
    """Test age-graded calculation returns None for invalid time format."""
    calc = AgeGradingCalculator()

    member = Member(
        member_id="M001",
        first_name="John",
        last_name="Doe",
        age=35,
        gender="M",
    )

    race_result = RaceResult(
        place=1,
        name="John Doe",
        time="invalid",
    )

    result = calc.calculate_age_graded_result(member, race_result, "spring_5k")
    assert result is None


def test_age_graded_result_age_graded_time_calculation() -> None:
    """Test age-graded time calculation from AgeGradedResult."""
    result = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="spring_5k",
        age=35,
        gender="M",
        actual_time="18:30",
        actual_seconds=1110.0,
        distance=RaceDistance.KM_5,
        age_factor=1.020,
        age_graded_percentage=98.04,
        overall_place=1,
    )

    # Age-graded time = actual_seconds / age_factor
    expected_age_graded_time = 1110.0 / 1.020
    assert abs(result.age_graded_time_seconds - expected_age_graded_time) < 0.01


def test_age_graded_series_scoring_add_results() -> None:
    """Test adding age-graded results to series scoring."""
    scoring = AgeGradedSeriesScoring()

    result1 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="spring_5k",
        age=35,
        gender="M",
        actual_time="18:30",
        actual_seconds=1110.0,
        distance=RaceDistance.KM_5,
        age_factor=1.020,
        age_graded_percentage=98.04,
        overall_place=1,
    )

    result2 = AgeGradedResult(
        member_id="M002",
        member_name="Jane Smith",
        race_name="spring_5k",
        age=28,
        gender="F",
        actual_time="19:45",
        actual_seconds=1185.0,
        distance=RaceDistance.KM_5,
        age_factor=1.000,
        age_graded_percentage=100.0,
        overall_place=2,
    )

    scoring.add_age_graded_results([result1, result2])

    assert len(scoring.all_age_graded_results) == 2
    assert "spring_5k" in scoring.race_names


def test_age_graded_series_scoring_tracks_race_names() -> None:
    """Test that series scoring tracks race names in order."""
    scoring = AgeGradedSeriesScoring()

    result1 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="spring_5k",
        age=35,
        gender="M",
        actual_time="18:30",
        actual_seconds=1110.0,
        distance=RaceDistance.KM_5,
        age_factor=1.020,
        age_graded_percentage=98.04,
        overall_place=1,
    )

    result2 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="summer_8k",
        age=35,
        gender="M",
        actual_time="30:00",
        actual_seconds=1800.0,
        distance=RaceDistance.KM_8,
        age_factor=1.022,
        age_graded_percentage=97.85,
        overall_place=1,
    )

    scoring.add_age_graded_results([result1])
    scoring.add_age_graded_results([result2])

    race_names = scoring.get_race_names()
    assert race_names == ["spring_5k", "summer_8k"]


def test_calculate_age_graded_standings_single_member() -> None:
    """Test age-graded standings calculation for a single member."""
    scoring = AgeGradedSeriesScoring()

    result1 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="spring_5k",
        age=35,
        gender="M",
        actual_time="18:30",
        actual_seconds=1110.0,
        distance=RaceDistance.KM_5,
        age_factor=1.020,
        age_graded_percentage=98.04,
        overall_place=1,
    )

    result2 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="summer_8k",
        age=35,
        gender="M",
        actual_time="30:00",
        actual_seconds=1800.0,
        distance=RaceDistance.KM_8,
        age_factor=1.022,
        age_graded_percentage=97.85,
        overall_place=1,
    )

    scoring.add_age_graded_results([result1, result2])

    standings = scoring.calculate_age_graded_standings()

    assert len(standings) == 1
    assert standings[0].member_id == "M001"
    assert standings[0].races_completed == 2
    # Average of 98.04 and 97.85
    expected_avg = (98.04 + 97.85) / 2
    assert abs(standings[0].average_age_graded_percentage - expected_avg) < 0.01


def test_calculate_age_graded_standings_multiple_members() -> None:
    """Test age-graded standings with multiple members (mixed genders)."""
    scoring = AgeGradedSeriesScoring()

    # Male runner, age 35
    result_m1 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="spring_5k",
        age=35,
        gender="M",
        actual_time="18:30",
        actual_seconds=1110.0,
        distance=RaceDistance.KM_5,
        age_factor=1.020,
        age_graded_percentage=98.04,
        overall_place=1,
    )

    # Female runner, age 28, better age-graded percentage
    result_f1 = AgeGradedResult(
        member_id="F001",
        member_name="Jane Smith",
        race_name="spring_5k",
        age=28,
        gender="F",
        actual_time="19:00",
        actual_seconds=1140.0,
        distance=RaceDistance.KM_5,
        age_factor=1.000,
        age_graded_percentage=100.0,
        overall_place=2,
    )

    scoring.add_age_graded_results([result_m1, result_f1])

    standings = scoring.calculate_age_graded_standings()

    # Female runner should be ranked higher due to better age-graded percentage
    assert len(standings) == 2
    assert standings[0].member_id == "F001"
    assert standings[0].average_age_graded_percentage == 100.0
    assert standings[1].member_id == "M001"


def test_calculate_age_graded_standings_max_races() -> None:
    """Test that only top N races count toward age-graded standings."""
    scoring = AgeGradedSeriesScoring()

    # Member with 3 races
    results = [
        AgeGradedResult(
            member_id="M001",
            member_name="John Doe",
            race_name=f"race_{i}",
            age=35,
            gender="M",
            actual_time="18:30",
            actual_seconds=1110.0,
            distance=RaceDistance.KM_5,
            age_factor=1.020,
            age_graded_percentage=90.0 + i,  # Increasing percentages
            overall_place=1,
        )
        for i in range(3)
    ]

    scoring.add_age_graded_results(results)

    # Only count top 2 races
    standings = scoring.calculate_age_graded_standings(max_races=2)

    assert len(standings) == 1
    assert standings[0].races_completed == 2
    # Should average the top 2 percentages: 91 and 92
    expected_avg = (91.0 + 92.0) / 2
    assert abs(standings[0].average_age_graded_percentage - expected_avg) < 0.01


def test_calculate_age_graded_standings_tie_break_by_races() -> None:
    """Test that tie-breaking uses number of races completed."""
    scoring = AgeGradedSeriesScoring()

    # Member 1 with 2 races at 95% average
    result_m1_r1 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="race_1",
        age=35,
        gender="M",
        actual_time="18:30",
        actual_seconds=1110.0,
        distance=RaceDistance.KM_5,
        age_factor=1.020,
        age_graded_percentage=95.0,
        overall_place=1,
    )

    result_m1_r2 = AgeGradedResult(
        member_id="M001",
        member_name="John Doe",
        race_name="race_2",
        age=35,
        gender="M",
        actual_time="18:30",
        actual_seconds=1110.0,
        distance=RaceDistance.KM_5,
        age_factor=1.020,
        age_graded_percentage=95.0,
        overall_place=1,
    )

    # Member 2 with 1 race at 95% (same average but fewer races)
    result_m2_r1 = AgeGradedResult(
        member_id="M002",
        member_name="Jane Smith",
        race_name="race_1",
        age=28,
        gender="F",
        actual_time="19:00",
        actual_seconds=1140.0,
        distance=RaceDistance.KM_5,
        age_factor=1.000,
        age_graded_percentage=95.0,
        overall_place=2,
    )

    scoring.add_age_graded_results([result_m1_r1, result_m1_r2, result_m2_r1])

    standings = scoring.calculate_age_graded_standings()

    # Member 1 should rank higher due to more races completed
    assert len(standings) == 2
    assert standings[0].member_id == "M001"
    assert standings[0].races_completed == 2
    assert standings[1].member_id == "M002"
    assert standings[1].races_completed == 1


def test_age_grading_factors_exist_for_all_distances() -> None:
    """Test that age-grading factors are defined for all standard distances."""
    for distance in RaceDistance:
        assert distance in AGE_GRADING_FACTORS
        assert "M" in AGE_GRADING_FACTORS[distance]
        assert "F" in AGE_GRADING_FACTORS[distance]
