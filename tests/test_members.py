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
    assert found is not None
    assert found.member_id == "M001"

    not_found = registry.find_by_name("Bob Jones")
    assert not_found is None


def test_member_registry_case_insensitive():
    """Test that name matching is case insensitive."""
    registry = MemberRegistry()

    member = Member(member_id="M001", first_name="John", last_name="Doe")
    registry.members = [member]

    found = registry.find_by_name("john doe")
    assert found is not None
    assert found.member_id == "M001"


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
    assert found is not None
    assert found.member_id == "M001"
