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


def test_calculate_category_standings_overall():
    """Test category standings for overall categories using overall points only."""
    registry = MemberRegistry()
    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    member2 = Member(
        member_id="M002", first_name="Jane", last_name="Smith", age=28, gender="F"
    )
    member3 = Member(
        member_id="M003", first_name="Bob", last_name="Jones", age=42, gender="M"
    )
    registry.members = [member1, member2, member3]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Race 1: John 1st (75 overall, 15 age), Jane 2nd (73, 15), Bob 3rd (71, 15)
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
    race_points = calculator.calculate_race_points([match1, match2, match3], "Race 1")
    series.add_race_points(race_points)

    category_standings = series.calculate_category_standings(registry)

    # Check that overall categories exist
    assert "M_overall" in category_standings
    assert "F_overall" in category_standings

    # M_overall should have John (75) and Bob (71)
    m_overall = category_standings["M_overall"]
    assert len(m_overall) == 2
    assert m_overall[0].member_id == "M001"
    assert m_overall[0].total_points == 75  # Only overall points
    assert m_overall[1].member_id == "M003"
    assert m_overall[1].total_points == 71

    # F_overall should have Jane (73)
    f_overall = category_standings["F_overall"]
    assert len(f_overall) == 1
    assert f_overall[0].member_id == "M002"
    assert f_overall[0].total_points == 73  # Only overall points


def test_calculate_category_standings_age_groups():
    """Test category standings for age groups using age group points only."""
    registry = MemberRegistry()
    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    member2 = Member(
        member_id="M002", first_name="Jane", last_name="Smith", age=28, gender="F"
    )
    member3 = Member(
        member_id="M003", first_name="Bob", last_name="Jones", age=42, gender="M"
    )
    member4 = Member(
        member_id="M004", first_name="Alex", last_name="Brown", age=37, gender="M"
    )
    registry.members = [member1, member2, member3, member4]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Race: John 1st, Alex 2nd, Bob 3rd, Jane 4th
    # John M30-39 1st (15 age pts), Alex M30-39 2nd (14),
    # Bob M40-49 1st (15), Jane F20-29 1st (15)
    matches = [
        MatchResult(
            race_result=RaceResult(place=1, name="John Doe", time="18:30"),
            member=member1,
            matched=True,
        ),
        MatchResult(
            race_result=RaceResult(place=2, name="Alex Brown", time="19:00"),
            member=member4,
            matched=True,
        ),
        MatchResult(
            race_result=RaceResult(place=3, name="Bob Jones", time="19:30"),
            member=member3,
            matched=True,
        ),
        MatchResult(
            race_result=RaceResult(place=4, name="Jane Smith", time="20:00"),
            member=member2,
            matched=True,
        ),
    ]
    race_points = calculator.calculate_race_points(matches, "Race 1")
    series.add_race_points(race_points)

    category_standings = series.calculate_category_standings(registry)

    # M_30-39: John (15 age pts), Alex (14)
    assert "M_30-39" in category_standings
    m_30_39 = category_standings["M_30-39"]
    assert len(m_30_39) == 2
    assert m_30_39[0].member_id == "M001"
    assert m_30_39[0].total_points == 15  # Only age group points
    assert m_30_39[1].member_id == "M004"
    assert m_30_39[1].total_points == 14

    # M_40-49: Bob (15 age pts)
    assert "M_40-49" in category_standings
    m_40_49 = category_standings["M_40-49"]
    assert len(m_40_49) == 1
    assert m_40_49[0].member_id == "M003"
    assert m_40_49[0].total_points == 15

    # F_20-29: Jane (15 age pts)
    assert "F_20-29" in category_standings
    f_20_29 = category_standings["F_20-29"]
    assert len(f_20_29) == 1
    assert f_20_29[0].member_id == "M002"
    assert f_20_29[0].total_points == 15


def test_calculate_category_standings_max_races():
    """Test that category standings respect max_races limit."""
    registry = MemberRegistry()
    member = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    registry.members = [member]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Add 10 races
    for i in range(10):
        match = MatchResult(
            race_result=RaceResult(place=i + 1, name="John Doe", time="18:30"),
            member=member,
            matched=True,
        )
        race_points = calculator.calculate_race_points([match], f"Race {i + 1}")
        series.add_race_points(race_points)

    category_standings = series.calculate_category_standings(registry, max_races=7)

    # M_overall should count top 7 overall point races
    m_overall = category_standings["M_overall"]
    assert m_overall[0].races_completed == 7
    # Top 7 overall: 75, 73, 71, 69, 67, 65, 63 = 483
    assert m_overall[0].total_points == 483

    # M_30-39 should count top 7 age group point races (all 15 pts)
    m_30_39 = category_standings["M_30-39"]
    assert m_30_39[0].races_completed == 7
    assert m_30_39[0].total_points == 7 * 15  # 105


def test_calculate_category_standings_all_age_groups():
    """Test that all age groups are represented in category standings."""
    registry = MemberRegistry()

    # Create members in each age group for both genders
    members = [
        Member(member_id="M01", first_name="A", last_name="U20M", age=18, gender="M"),
        Member(member_id="M02", first_name="B", last_name="U20F", age=19, gender="F"),
        Member(member_id="M03", first_name="C", last_name="20M", age=25, gender="M"),
        Member(member_id="M04", first_name="D", last_name="20F", age=27, gender="F"),
        Member(member_id="M05", first_name="E", last_name="30M", age=35, gender="M"),
        Member(member_id="M06", first_name="F", last_name="30F", age=37, gender="F"),
        Member(member_id="M07", first_name="G", last_name="40M", age=45, gender="M"),
        Member(member_id="M08", first_name="H", last_name="40F", age=47, gender="F"),
        Member(member_id="M09", first_name="I", last_name="50M", age=55, gender="M"),
        Member(member_id="M10", first_name="J", last_name="50F", age=57, gender="F"),
        Member(member_id="M11", first_name="K", last_name="60M", age=65, gender="M"),
        Member(member_id="M12", first_name="L", last_name="60F", age=67, gender="F"),
        Member(member_id="M13", first_name="M", last_name="70M", age=75, gender="M"),
        Member(member_id="M14", first_name="N", last_name="70F", age=77, gender="F"),
        Member(member_id="M15", first_name="O", last_name="80M", age=85, gender="M"),
        Member(member_id="M16", first_name="P", last_name="80F", age=87, gender="F"),
    ]
    registry.members = members

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Create a race with all members
    matches = [
        MatchResult(
            race_result=RaceResult(place=i + 1, name=m.full_name, time="20:00"),
            member=m,
            matched=True,
        )
        for i, m in enumerate(members)
    ]
    race_points = calculator.calculate_race_points(matches, "Test Race")
    series.add_race_points(race_points)

    category_standings = series.calculate_category_standings(registry)

    # Check all age group categories exist
    expected_categories = [
        "M_overall",
        "F_overall",
        "M_U20",
        "F_U20",
        "M_20-29",
        "F_20-29",
        "M_30-39",
        "F_30-39",
        "M_40-49",
        "F_40-49",
        "M_50-59",
        "F_50-59",
        "M_60-69",
        "F_60-69",
        "M_70-79",
        "F_70-79",
        "M_80+",
        "F_80+",
    ]

    for category in expected_categories:
        assert category in category_standings, f"Category {category} not found"
        assert len(category_standings[category]) > 0


def test_calculate_category_standings_skips_no_gender():
    """Test that members without gender are excluded from category standings."""
    registry = MemberRegistry()
    member1 = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    member2 = Member(
        member_id="M002",
        first_name="Unknown",
        last_name="Person",
        age=30,
        gender=None,
    )
    registry.members = [member1, member2]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    matches = [
        MatchResult(
            race_result=RaceResult(place=1, name="John Doe", time="18:30"),
            member=member1,
            matched=True,
        ),
        MatchResult(
            race_result=RaceResult(place=2, name="Unknown Person", time="19:00"),
            member=member2,
            matched=True,
        ),
    ]
    race_points = calculator.calculate_race_points(matches, "Test Race")
    series.add_race_points(race_points)

    category_standings = series.calculate_category_standings(registry)

    # Only M_overall and M_30-39 should exist
    assert "M_overall" in category_standings
    assert "M_30-39" in category_standings
    assert "F_overall" not in category_standings
    assert len(category_standings["M_overall"]) == 1


def test_series_scoring_tracks_race_names():
    """Test that SeriesScoring correctly tracks race names in order."""
    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    member = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )

    # Add races in a specific order
    for race_name in ["Spring 5K", "Summer 8K", "Fall 10K"]:
        match = MatchResult(
            race_result=RaceResult(place=1, name="John Doe", time="18:30"),
            member=member,
            matched=True,
        )
        race_points = calculator.calculate_race_points([match], race_name)
        series.add_race_points(race_points)

    race_names = series.get_race_names()
    assert race_names == ["Spring 5K", "Summer 8K", "Fall 10K"]


def test_series_scoring_does_not_duplicate_race_names():
    """Test that race names are not duplicated even when called multiple times."""
    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    member = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )

    # Add the same race twice (edge case)
    for _ in range(2):
        match = MatchResult(
            race_result=RaceResult(place=1, name="John Doe", time="18:30"),
            member=member,
            matched=True,
        )
        race_points = calculator.calculate_race_points([match], "Spring 5K")
        series.add_race_points(race_points)

    race_names = series.get_race_names()
    assert race_names == ["Spring 5K"]


def test_series_totals_include_race_points_by_race():
    """Test that SeriesTotal includes race_points_by_race breakdown."""
    registry = MemberRegistry()
    member = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    registry.members = [member]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Add two races with different placements
    for race_name, place in [("Spring 5K", 1), ("Summer 8K", 3)]:
        match = MatchResult(
            race_result=RaceResult(place=place, name="John Doe", time="18:30"),
            member=member,
            matched=True,
        )
        race_points = calculator.calculate_race_points([match], race_name)
        series.add_race_points(race_points)

    totals = series.calculate_series_totals(registry)

    assert len(totals) == 1
    assert totals[0].race_points_by_race is not None
    # Spring 5K: 75 overall + 15 age = 90
    # Summer 8K: 71 overall + 15 age = 86
    assert totals[0].race_points_by_race["Spring 5K"] == 90
    assert totals[0].race_points_by_race["Summer 8K"] == 86
    assert totals[0].total_points == 90 + 86


def test_category_standings_include_race_points_by_race():
    """Test that category standings include race_points_by_race breakdown."""
    registry = MemberRegistry()
    member = Member(
        member_id="M001", first_name="John", last_name="Doe", age=35, gender="M"
    )
    registry.members = [member]

    series = SeriesScoring()
    calculator = PointsCalculator(PointsConfig(race_type=RaceType.RACE_75))

    # Add two races with different placements
    for race_name, place in [("Spring 5K", 1), ("Summer 8K", 3)]:
        match = MatchResult(
            race_result=RaceResult(place=place, name="John Doe", time="18:30"),
            member=member,
            matched=True,
        )
        race_points = calculator.calculate_race_points([match], race_name)
        series.add_race_points(race_points)

    category_standings = series.calculate_category_standings(registry)

    # Check M_overall uses overall points only
    m_overall = category_standings["M_overall"][0]
    assert m_overall.race_points_by_race is not None
    assert m_overall.race_points_by_race["Spring 5K"] == 75  # overall points only
    assert m_overall.race_points_by_race["Summer 8K"] == 71
    assert m_overall.total_points == 75 + 71

    # Check M_30-39 uses age group points only
    m_30_39 = category_standings["M_30-39"][0]
    assert m_30_39.race_points_by_race is not None
    assert m_30_39.race_points_by_race["Spring 5K"] == 15  # age group points only
    assert m_30_39.race_points_by_race["Summer 8K"] == 15
    assert m_30_39.total_points == 15 + 15
