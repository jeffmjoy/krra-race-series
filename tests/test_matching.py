"""Tests for matching module."""

import pytest
from krra_race_series.members import Member, MemberRegistry
from krra_race_series.race_results import RaceResult
from krra_race_series.matching import FinisherMatcher


def test_match_finisher_success():
    """Test successful finisher matching."""
    registry = MemberRegistry()
    member = Member(member_id="M001", first_name="John", last_name="Doe")
    registry.members = [member]

    matcher = FinisherMatcher(registry)

    race_result = RaceResult(place=1, name="John Doe", time="18:30")
    match = matcher.match_finisher(race_result)

    assert match.matched is True
    assert match.member is not None
    assert match.member.member_id == "M001"


def test_match_finisher_no_match():
    """Test finisher matching when no member exists."""
    registry = MemberRegistry()
    matcher = FinisherMatcher(registry)

    race_result = RaceResult(place=1, name="Unknown Runner", time="18:30")
    match = matcher.match_finisher(race_result)

    assert match.matched is False
    assert match.member is None


def test_match_all():
    """Test matching multiple finishers."""
    registry = MemberRegistry()
    member1 = Member(member_id="M001", first_name="John", last_name="Doe")
    member2 = Member(member_id="M002", first_name="Jane", last_name="Smith")
    registry.members = [member1, member2]

    matcher = FinisherMatcher(registry)

    results = [
        RaceResult(place=1, name="John Doe", time="18:30"),
        RaceResult(place=2, name="Unknown Runner", time="19:00"),
        RaceResult(place=3, name="Jane Smith", time="19:30")
    ]

    matches = matcher.match_all(results)

    assert len(matches) == 3
    assert matches[0].matched is True
    assert matches[1].matched is False
    assert matches[2].matched is True
