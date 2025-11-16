"""Tests for scoring module."""

from krra_race_series.matching import MatchResult
from krra_race_series.members import Member, MemberRegistry
from krra_race_series.race_results import RaceResult
from krra_race_series.scoring import (
    AgeGroup,
    PointsCalculator,
    PointsConfig,
    RaceType,
    SeriesScoring,
)


def test_age_group_categorization():
    """Test age group categorization."""
    assert AgeGroup.from_age(15) == AgeGroup.UNDER_20
    assert AgeGroup.from_age(19) == AgeGroup.UNDER_20
    assert AgeGroup.from_age(20) == AgeGroup.AGE_20_29
    assert AgeGroup.from_age(29) == AgeGroup.AGE_20_29
    assert AgeGroup.from_age(35) == AgeGroup.AGE_30_39
    assert AgeGroup.from_age(45) == AgeGroup.AGE_40_49
    assert AgeGroup.from_age(55) == AgeGroup.AGE_50_59
    assert AgeGroup.from_age(65) == AgeGroup.AGE_60_69
    assert AgeGroup.from_age(75) == AgeGroup.AGE_70_79
    assert AgeGroup.from_age(85) == AgeGroup.AGE_80_PLUS
    assert AgeGroup.from_age(None) is None


def test_overall_points_calculation_75_race():
    """Test overall points calculation for 75-point races."""
    config = PointsConfig(race_type=RaceType.RACE_75)

    assert config.calculate_overall_points(1) == 75
    assert config.calculate_overall_points(2) == 73
    assert config.calculate_overall_points(3) == 71
    assert config.calculate_overall_points(10) == 57
    assert config.calculate_overall_points(11) == 56
    assert config.calculate_overall_points(20) == 47
    assert config.calculate_overall_points(65) == 2
    assert config.calculate_overall_points(66) == 1
    assert config.calculate_overall_points(100) == 1


def test_overall_points_calculation_100_race():
    """Test overall points calculation for 100-point races."""
    config = PointsConfig(race_type=RaceType.RACE_100)

    assert config.calculate_overall_points(1) == 100
    assert config.calculate_overall_points(2) == 98
    assert config.calculate_overall_points(3) == 96
    assert config.calculate_overall_points(10) == 82
    assert config.calculate_overall_points(11) == 81
    assert config.calculate_overall_points(20) == 72
    assert config.calculate_overall_points(90) == 2
    assert config.calculate_overall_points(91) == 1
    assert config.calculate_overall_points(100) == 1


def test_age_group_points_75_race():
    """Test age group points for 75-point races."""
    config = PointsConfig(race_type=RaceType.RACE_75)

    assert config.calculate_age_group_points(1) == 15
    assert config.calculate_age_group_points(2) == 14
    assert config.calculate_age_group_points(10) == 6
    assert config.calculate_age_group_points(15) == 1
    assert config.calculate_age_group_points(20) == 1
    assert config.calculate_age_group_points(50) == 1


def test_age_group_points_100_race():
    """Test age group points for 100-point races."""
    config = PointsConfig(race_type=RaceType.RACE_100)

    assert config.calculate_age_group_points(1) == 20
    assert config.calculate_age_group_points(2) == 19
    assert config.calculate_age_group_points(10) == 11
    assert config.calculate_age_group_points(20) == 1
    assert config.calculate_age_group_points(30) == 1


def test_calculate_race_points_with_age_groups():
    """Test calculating points for a race with age groups."""
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Create members with different ages and genders
    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    member2 = Member(
        member_id="M002", first_name="Jane", last_name="Smith", age=33, gender="F"
    )
    member3 = Member(
        member_id="M003", first_name="Bob", last_name="Jones", age=45, gender="M"
    )

    # Create race results - overall positions
    match1 = MatchResult(
        race_result=RaceResult(place=1, name="John Doe", time="18:30"),
        member=member1,
        matched=True,
    )
    match2 = MatchResult(
        race_result=RaceResult(place=2, name="Jane Smith", time="19:00"),
        member=member2,
        matched=True,
    )
    match3 = MatchResult(
        race_result=RaceResult(place=3, name="Bob Jones", time="19:30"),
        member=member3,
        matched=True,
    )

    race_points = calculator.calculate_race_points([match1, match2, match3], "Test")

    assert len(race_points) == 3

    # John: 1st overall (75 pts), 1st in M30-39 (15 pts) = 90 total
    john_points = next(p for p in race_points if p.member_id == "M001")
    assert john_points.overall_place == 1
    assert john_points.overall_points == 75
    assert john_points.age_group == AgeGroup.AGE_30_39
    assert john_points.age_group_place == 1
    assert john_points.age_group_points == 15
    assert john_points.total_points == 90

    # Jane: 2nd overall (73 pts), 1st in F30-39 (15 pts) = 88 total
    jane_points = next(p for p in race_points if p.member_id == "M002")
    assert jane_points.overall_place == 2
    assert jane_points.overall_points == 73
    assert jane_points.age_group == AgeGroup.AGE_30_39
    assert jane_points.age_group_place == 1
    assert jane_points.age_group_points == 15
    assert jane_points.total_points == 88

    # Bob: 3rd overall (71 pts), 1st in M40-49 (15 pts) = 86 total
    bob_points = next(p for p in race_points if p.member_id == "M003")
    assert bob_points.overall_place == 3
    assert bob_points.overall_points == 71
    assert bob_points.age_group == AgeGroup.AGE_40_49
    assert bob_points.age_group_place == 1
    assert bob_points.age_group_points == 15
    assert bob_points.total_points == 86


def test_age_group_ranking_within_gender():
    """Test that age group ranking is correctly calculated within gender."""
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Two males in the same age group
    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    member2 = Member(
        member_id="M002", first_name="Bob", last_name="Smith", age=38, gender="M"
    )

    match1 = MatchResult(
        race_result=RaceResult(place=1, name="John Doe", time="18:30"),
        member=member1,
        matched=True,
    )
    match2 = MatchResult(
        race_result=RaceResult(place=5, name="Bob Smith", time="20:00"),
        member=member2,
        matched=True,
    )

    race_points = calculator.calculate_race_points([match1, match2], "Test")

    # John: 1st in M30-39
    john_points = next(p for p in race_points if p.member_id == "M001")
    assert john_points.age_group_place == 1
    assert john_points.age_group_points == 15

    # Bob: 2nd in M30-39
    bob_points = next(p for p in race_points if p.member_id == "M002")
    assert bob_points.age_group_place == 2
    assert bob_points.age_group_points == 14


def test_series_scoring_max_races():
    """Test that series scoring counts only top 7 races."""
    registry = MemberRegistry()
    member = Member(member_id="M001", first_name="John", last_name="Doe", age=35)
    registry.members = [member]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Add 10 races with varying points
    for i in range(10):
        match = MatchResult(
            race_result=RaceResult(place=i + 1, name="John Doe", time="18:30"),
            member=member,
            matched=True,
        )
        race_points = calculator.calculate_race_points([match], f"Race {i + 1}")
        series.add_race_points(race_points)

    totals = series.calculate_series_totals(registry, max_races=7)

    # Should only count top 7 races
    assert len(totals) == 1
    assert totals[0].races_completed == 7
    # Top 7 should be races with places 1-7
    # Place 1: 75+15=90, Place 2: 73+15=88, etc.
    expected = 90 + 88 + 86 + 84 + 82 + 80 + 78  # Top 7 races
    assert totals[0].total_points == expected


def test_series_scoring_multiple_members():
    """Test cumulative series scoring with multiple members."""
    registry = MemberRegistry()
    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    member2 = Member(
        member_id="M002", first_name="Jane", last_name="Smith", age=28, gender="F"
    )
    registry.members = [member1, member2]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Race 1: John 1st, Jane 2nd
    match1 = MatchResult(
        race_result=RaceResult(place=1, name="John Doe", time="18:30"),
        member=member1,
        matched=True,
    )
    match2 = MatchResult(
        race_result=RaceResult(place=2, name="Jane Smith", time="19:00"),
        member=member2,
        matched=True,
    )
    race1_points = calculator.calculate_race_points([match1, match2], "Race 1")
    series.add_race_points(race1_points)

    # Race 2: Jane 1st
    match3 = MatchResult(
        race_result=RaceResult(place=1, name="Jane Smith", time="18:45"),
        member=member2,
        matched=True,
    )
    race2_points = calculator.calculate_race_points([match3], "Race 2")
    series.add_race_points(race2_points)

    # Calculate totals
    totals = series.calculate_series_totals(registry)

    assert len(totals) == 2

    # Jane: Race1 (73+15=88) + Race2 (75+15=90) = 178
    assert totals[0].member_id == "M002"
    assert totals[0].total_points == 178
    assert totals[0].races_completed == 2

    # John: Race1 (75+15=90) = 90
    assert totals[1].member_id == "M001"
    assert totals[1].total_points == 90
    assert totals[1].races_completed == 1


def test_calculate_race_points_with_unmatched_results():
    """Test that unmatched results are skipped when calculating race points."""
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )

    # Create a matched result and an unmatched result
    match1 = MatchResult(
        race_result=RaceResult(place=1, name="John Doe", time="18:30"),
        member=member1,
        matched=True,
    )
    match2 = MatchResult(
        race_result=RaceResult(place=2, name="Unknown Runner", time="19:00"),
        member=None,
        matched=False,
    )

    race_points = calculator.calculate_race_points([match1, match2], "Test Race")

    # Should only have points for the matched result
    assert len(race_points) == 1
    assert race_points[0].member_id == "M001"


def test_calculate_race_points_with_matched_but_no_member():
    """Test edge case where matched=True but member=None (defensive check)."""
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )

    # Create normal match and edge case match (matched=True but member=None)
    match1 = MatchResult(
        race_result=RaceResult(place=1, name="John Doe", time="18:30"),
        member=member1,
        matched=True,
    )
    match2 = MatchResult(
        race_result=RaceResult(place=2, name="Edge Case", time="19:00"),
        member=None,
        matched=True,  # Unusual: marked as matched but no member
    )

    race_points = calculator.calculate_race_points([match1, match2], "Test Race")

    # Should only have points for match with actual member
    assert len(race_points) == 1
    assert race_points[0].member_id == "M001"
