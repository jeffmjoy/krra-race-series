"""Tests for members module."""

from pathlib import Path

import pytest

from krra_race_series.members import Member, MemberRegistry


def test_member_creation():
    """Test creating a Member."""
    member = Member(
        member_id="M001", first_name="John", last_name="Doe", email="john@example.com"
    )

    assert member.member_id == "M001"
    assert member.full_name == "John Doe"


def test_member_registry_find_by_name():
    """Test finding a member by name."""
    registry = MemberRegistry()

    member1 = Member(member_id="M001", first_name="John", last_name="Doe")
    member2 = Member(member_id="M002", first_name="Jane", last_name="Smith")

    registry.members = [member1, member2]

    found = registry.find_by_name("John Doe")
    assert found["member"] is not None
    assert found["member"].member_id == "M001"
    assert found["confidence"] == 1.0

    not_found = registry.find_by_name("Bob Jones")
    assert not_found["member"] is None


def test_member_registry_case_insensitive():
    """Test that name matching is case insensitive."""
    registry = MemberRegistry()

    member = Member(member_id="M001", first_name="John", last_name="Doe")
    registry.members = [member]

    found = registry.find_by_name("john doe")
    assert found["member"] is not None
    assert found["member"].member_id == "M001"


def test_load_from_csv_with_complete_data(tmp_path):
    """Test loading members from a CSV file with complete data."""
    registry = MemberRegistry()

    # Create test CSV file
    csv_path = tmp_path / "members.csv"
    csv_path.write_text(
        "member_id,first_name,last_name,email,age,gender\n"
        "M001,John,Doe,john@example.com,35,M\n"
        "M002,Jane,Smith,jane@example.com,28,F\n"
    )

    registry.load_from_csv(csv_path)

    assert len(registry.members) == 2
    assert registry.members[0].member_id == "M001"
    assert registry.members[0].first_name == "John"
    assert registry.members[0].last_name == "Doe"
    assert registry.members[0].email == "john@example.com"
    assert registry.members[0].age == 35
    assert registry.members[0].gender == "M"


def test_load_from_csv_with_partial_data(tmp_path):
    """Test loading members from a CSV file with partial data."""
    registry = MemberRegistry()

    # Create test CSV file with missing optional fields
    csv_path = tmp_path / "members.csv"
    csv_path.write_text(
        "member_id,first_name,last_name,email,age,gender\n"
        "M001,John,Doe,,,\n"
        "M002,Jane,Smith,jane@example.com,28,\n"
    )

    registry.load_from_csv(csv_path)

    assert len(registry.members) == 2
    assert registry.members[0].member_id == "M001"
    # Empty strings in CSV are loaded as empty strings, not None
    assert registry.members[0].email == ""
    assert registry.members[0].age is None
    assert registry.members[0].gender == ""

    assert registry.members[1].member_id == "M002"
    assert registry.members[1].age == 28


def test_load_from_csv_file_not_found():
    """Test loading from a non-existent CSV file raises FileNotFoundError."""
    registry = MemberRegistry()

    with pytest.raises(FileNotFoundError, match="Member file not found"):
        registry.load_from_csv(Path("nonexistent.csv"))


def test_load_from_csv_strips_whitespace(tmp_path):
    """Test that names are stripped of leading/trailing whitespace."""
    registry = MemberRegistry()

    # Create test CSV with whitespace
    csv_path = tmp_path / "members.csv"
    csv_path.write_text(
        "member_id,first_name,last_name,email,age,gender\n"
        "M001,  John  ,  Doe  ,john@example.com,35,M\n"
    )

    registry.load_from_csv(csv_path)

    assert registry.members[0].first_name == "John"
    assert registry.members[0].last_name == "Doe"
    assert registry.members[0].full_name == "John Doe"


def test_get_all_members():
    """Test getting all members returns a copy of the member list."""
    registry = MemberRegistry()

    member1 = Member(member_id="M001", first_name="John", last_name="Doe")
    member2 = Member(member_id="M002", first_name="Jane", last_name="Smith")

    registry.members = [member1, member2]

    all_members = registry.get_all_members()

    # Should return all members
    assert len(all_members) == 2

    # Should be a copy, not the original list
    assert all_members is not registry.members

    # Modifying the returned list shouldn't affect the registry
    all_members.clear()
    assert len(registry.members) == 2


def test_find_by_name_with_whitespace():
    """Test finding a member by name with extra whitespace."""
    registry = MemberRegistry()

    member = Member(member_id="M001", first_name="John", last_name="Doe")
    registry.members = [member]

    found = registry.find_by_name("  John Doe  ")
    assert found["member"] is not None
    assert found["member"].member_id == "M001"


def test_load_name_corrections(tmp_path):
    """Test loading name corrections from CSV."""
    registry = MemberRegistry()

    # Create test corrections file
    corrections_path = tmp_path / "corrections.csv"
    corrections_path.write_text(
        "race_name,member_name\n"
        "Jeff Davis,Jeffrey Davis\n"
        "Bob Smith,Robert Smith\n"
        "Sara Jones,Sarah Jones\n"
    )

    registry.load_name_corrections(corrections_path)

    assert len(registry.name_corrections) == 3
    assert registry.name_corrections["jeff davis"] == "Jeffrey Davis"
    assert registry.name_corrections["bob smith"] == "Robert Smith"


def test_load_name_corrections_file_not_found():
    """Test loading corrections from non-existent file raises error."""
    registry = MemberRegistry()

    with pytest.raises(FileNotFoundError, match="Name corrections file not found"):
        registry.load_name_corrections(Path("nonexistent.csv"))


def test_find_by_name_with_corrections():
    """Test that name corrections are applied before fuzzy matching."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="Jeffrey", last_name="Davis"),
        Member(member_id="M002", first_name="Robert", last_name="Smith"),
    ]

    # Manually add corrections
    registry.name_corrections = {
        "jeff davis": "Jeffrey Davis",
        "bob smith": "Robert Smith",
    }

    # Should use correction for exact match
    result = registry.find_by_name("Jeff Davis")
    assert result["member"] is not None
    assert result["member"].member_id == "M001"
    assert result["confidence"] == 1.0  # Correction gives perfect match
    assert result["is_ambiguous"] is False


def test_find_by_name_without_corrections_uses_fuzzy():
    """Test that fuzzy matching is used when no correction exists."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="Jeffrey", last_name="Davis"),
    ]

    # No corrections loaded
    result = registry.find_by_name("Jeff Davis")

    # Should still match via fuzzy matching
    assert result["member"] is not None
    assert result["member"].member_id == "M001"
    # Confidence will be less than 1.0 since it's fuzzy
    assert result["confidence"] < 1.0
    assert result["confidence"] >= 0.70  # Default threshold


def test_fuzzy_match_with_typo():
    """Test fuzzy matching handles minor typos."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="Sarah", last_name="Johnson"),
    ]

    # Typo: Sara instead of Sarah
    result = registry.find_by_name("Sara Johnson")

    assert result["member"] is not None
    assert result["member"].member_id == "M001"
    assert result["confidence"] >= 0.85  # Should be high confidence


def test_fuzzy_match_truncated_name():
    """Test fuzzy matching with truncated hyphenated names."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="Sarah", last_name="Mountjoy-Stringham"),
    ]

    # Truncated last name
    result = registry.find_by_name("Sarah Mountjoy")

    assert result["member"] is not None
    assert result["member"].member_id == "M001"
    assert result["confidence"] >= 0.70


def test_fuzzy_match_below_threshold():
    """Test that matches below confidence threshold are rejected."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Doe"),
    ]

    # Very different name
    result = registry.find_by_name("Jane Smith", min_confidence=0.70)

    assert result["member"] is None
    assert result["confidence"] < 0.70


def test_ambiguity_detection():
    """Test detection of ambiguous matches."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Smith"),
        Member(member_id="M002", first_name="Jon", last_name="Smith"),
    ]

    # Search for name that could match both similarly
    result = registry.find_by_name("Jhon Smith", ambiguity_threshold=0.05)

    # Should match one of them
    assert result["member"] is not None
    # Should be flagged as ambiguous due to similar scores
    assert result["is_ambiguous"] is True


def test_no_ambiguity_with_clear_winner():
    """Test that clear matches are not flagged as ambiguous."""
    registry = MemberRegistry()
    registry.members = [
        Member(member_id="M001", first_name="John", last_name="Doe"),
        Member(member_id="M002", first_name="Jane", last_name="Smith"),
    ]

    result = registry.find_by_name("John Doe", ambiguity_threshold=0.05)

    assert result["member"] is not None
    assert result["member"].member_id == "M001"
    assert result["is_ambiguous"] is False
