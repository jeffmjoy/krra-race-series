"""Tests for members module."""

import pytest
from pathlib import Path
from krra_race_series.members import Member, MemberRegistry


def test_member_creation():
    """Test creating a Member."""
    member = Member(
        member_id="M001",
        first_name="John",
        last_name="Doe",
        email="john@example.com"
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
