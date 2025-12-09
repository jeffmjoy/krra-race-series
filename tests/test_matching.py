"""Tests for matching module."""

import pytest

from krra_race_series.matching import FinisherMatcher
from krra_race_series.members import Member, MemberRegistry
from krra_race_series.race_results import RaceResult


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
    assert match.confidence == 1.0
    assert match.is_ambiguous is False


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
        RaceResult(place=3, name="Jane Smith", time="19:30"),
    ]

    matches = matcher.match_all(results)

    assert len(matches) == 3
    assert matches[0].matched is True
    assert matches[1].matched is False
    assert matches[2].matched is True


@pytest.mark.parametrize(
    "race_name,expected_match,min_confidence",
    [
        ("Jeff Davis", True, 0.70),  # Nickname variation
        ("Jeffrey Davis", True, 0.70),  # Full name
        ("J Davis", True, 0.60),  # Initial + last name (lower confidence)
        ("Mountjoy", True, 0.50),  # Truncated hyphenated name - needs lower threshold
        ("Sarah Mountjoy-Stringham", True, 0.70),  # Full hyphenated name
        ("Sara Mountjoy", True, 0.70),  # Common misspelling + truncation
        ("John A. Smith", True, 0.70),  # Middle initial
        ("Smyth", False, 0.90),  # Deliberate typo with high threshold
        ("Bob Wilson", True, 0.60),  # Nickname (Robert -> Bob)
    ],
)
def test_fuzzy_matching_variations(race_name, expected_match, min_confidence):
    """Test fuzzy matching handles common name variations."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="Jeffrey", last_name="Davis"),
        Member(member_id="M002", first_name="Sarah", last_name="Mountjoy-Stringham"),
        Member(member_id="M003", first_name="John", last_name="Smith"),
        Member(member_id="M004", first_name="Robert", last_name="Wilson"),
    ]

    matcher = FinisherMatcher(registry, min_confidence=min_confidence)
    race_result = RaceResult(place=1, name=race_name, time="18:30")
    match = matcher.match_finisher(race_result)

    assert match.matched is expected_match


def test_confidence_scores():
    """Test that confidence scores are calculated appropriately."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Doe"),
    ]

    matcher = FinisherMatcher(registry)

    # Exact match should have confidence = 1.0
    exact_match = matcher.match_finisher(
        RaceResult(place=1, name="John Doe", time="18:30")
    )
    assert exact_match.confidence == 1.0

    # Close match should have high confidence
    close_match = matcher.match_finisher(
        RaceResult(place=1, name="Jon Doe", time="18:30")
    )
    assert close_match.matched is True
    assert 0.85 <= close_match.confidence < 1.0

    # Poor match should have low confidence
    poor_match = matcher.match_finisher(
        RaceResult(place=1, name="Jane Smith", time="18:30")
    )
    assert poor_match.matched is False
    assert poor_match.confidence < 0.70


def test_ambiguous_matches():
    """Test detection of ambiguous matches with similar names."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Smith"),
        Member(member_id="M002", first_name="Jon", last_name="Smith"),
        Member(member_id="M003", first_name="Jane", last_name="Doe"),
    ]

    # Use higher threshold to catch the subtle difference
    matcher = FinisherMatcher(registry, min_confidence=0.70, ambiguity_threshold=0.10)

    # Typo "Jhn Smith" scores similarly to both "John Smith" and "Jon Smith"
    race_result = RaceResult(place=1, name="Jhn Smith", time="18:30")
    match = matcher.match_finisher(race_result)

    # Should still match one
    assert match.matched is True
    # Should be flagged as ambiguous due to similar scores
    assert match.is_ambiguous is True


def test_non_ambiguous_with_clear_winner():
    """Test that clear matches are not flagged as ambiguous."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Doe"),
        Member(member_id="M002", first_name="Jane", last_name="Smith"),
    ]

    matcher = FinisherMatcher(registry, min_confidence=0.70, ambiguity_threshold=0.05)

    race_result = RaceResult(place=1, name="John Doe", time="18:30")
    match = matcher.match_finisher(race_result)

    assert match.matched is True
    assert match.is_ambiguous is False


def test_min_confidence_threshold():
    """Test that matches below min_confidence are rejected."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Doe"),
    ]

    # Use high confidence threshold
    matcher = FinisherMatcher(registry, min_confidence=0.95)

    # Close but not exact match should be rejected
    race_result = RaceResult(place=1, name="Jon Do", time="18:30")
    match = matcher.match_finisher(race_result)

    assert match.matched is False


def test_custom_thresholds():
    """Test that custom thresholds are applied correctly."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Doe"),
    ]

    # Lower threshold should accept more matches
    lenient_matcher = FinisherMatcher(registry, min_confidence=0.50)
    strict_matcher = FinisherMatcher(registry, min_confidence=0.90)

    race_result = RaceResult(place=1, name="J. Doe", time="18:30")

    lenient_match = lenient_matcher.match_finisher(race_result)
    strict_match = strict_matcher.match_finisher(race_result)

    assert lenient_match.matched is True
    assert strict_match.matched is False
