"""Tests for scoring module."""

import pytest
from krra_race_series.members import Member, MemberRegistry
from krra_race_series.race_results import RaceResult
from krra_race_series.matching import MatchResult
from krra_race_series.scoring import (
    PointsConfig, PointsCalculator, SeriesScoring
)


def test_points_calculation():
    """Test basic points calculation."""
    config = PointsConfig(base_points=100, decrement=1)
    
    assert config.calculate_points(1) == 100
    assert config.calculate_points(2) == 99
    assert config.calculate_points(10) == 91


def test_points_minimum():
    """Test that points don't go below minimum."""
    config = PointsConfig(base_points=10, decrement=1, minimum_points=1)
    
    assert config.calculate_points(50) == 1


def test_calculate_race_points():
    """Test calculating points for a race."""
    calculator = PointsCalculator()
    
    member = Member(member_id="M001", first_name="John", last_name="Doe")
    race_result = RaceResult(place=1, name="John Doe", time="18:30")
    match = MatchResult(race_result=race_result, member=member, matched=True)
    
    race_points = calculator.calculate_race_points([match], "Test Race")
    
    assert len(race_points) == 1
    assert race_points[0].member_id == "M001"
    assert race_points[0].place == 1
    assert race_points[0].points == 100


def test_series_scoring():
    """Test cumulative series scoring."""
    registry = MemberRegistry()
    member1 = Member(member_id="M001", first_name="John", last_name="Doe")
    member2 = Member(member_id="M002", first_name="Jane", last_name="Smith")
    registry.members = [member1, member2]
    
    series = SeriesScoring()
    calculator = PointsCalculator()
    
    # Race 1
    match1 = MatchResult(
        race_result=RaceResult(place=1, name="John Doe", time="18:30"),
        member=member1,
        matched=True
    )
    match2 = MatchResult(
        race_result=RaceResult(place=2, name="Jane Smith", time="19:00"),
        member=member2,
        matched=True
    )
    
    race1_points = calculator.calculate_race_points([match1, match2], "Race 1")
    series.add_race_points(race1_points)
    
    # Race 2
    match3 = MatchResult(
        race_result=RaceResult(place=1, name="Jane Smith", time="18:45"),
        member=member2,
        matched=True
    )
    
    race2_points = calculator.calculate_race_points([match3], "Race 2")
    series.add_race_points(race2_points)
    
    # Calculate totals
    totals = series.calculate_series_totals(registry)
    
    assert len(totals) == 2
    # Jane should be first (100 + 99 = 199)
    assert totals[0].member_id == "M002"
    assert totals[0].total_points == 199
    assert totals[0].races_completed == 2
    # John should be second (100)
    assert totals[1].member_id == "M001"
    assert totals[1].total_points == 100
    assert totals[1].races_completed == 1
