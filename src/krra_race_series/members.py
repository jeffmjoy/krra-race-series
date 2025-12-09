"""Module for managing KRRA member data."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from rapidfuzz import fuzz


class MatchResultDict(TypedDict):
    """Type definition for fuzzy match result."""

    member: Member | None
    confidence: float
    is_ambiguous: bool


@dataclass
class Member:
    """Represents a KRRA member."""

    member_id: str
    first_name: str
    last_name: str
    email: str | None = None
    age: int | None = None
    gender: str | None = None

    @property
    def full_name(self) -> str:
        """Return the member's full name."""
        return f"{self.first_name} {self.last_name}"


class MemberRegistry:
    """Manages the registry of KRRA members."""

    def __init__(self) -> None:
        self.members: list[Member] = []
        self.name_corrections: dict[str, str] = {}  # race_name -> member_name

    def load_name_corrections(self, filepath: Path) -> None:
        """Load name corrections from a CSV file.

        CSV format: race_name,member_name
        Maps race result names to their correct member names.

        Args:
            filepath: Path to the CSV file containing name corrections

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Name corrections file not found: {filepath}")

        self.name_corrections = {}

        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                race_name = row.get("race_name", "").strip()
                member_name = row.get("member_name", "").strip()
                if race_name and member_name:
                    # Store normalized (lowercase) for case-insensitive lookup
                    self.name_corrections[race_name.lower()] = member_name

    def load_from_csv(self, filepath: Path) -> None:
        """Load members from a CSV file.

        Args:
            filepath: Path to the CSV file containing member data

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Member file not found: {filepath}")

        self.members = []

        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                member = Member(
                    member_id=row.get("member_id", ""),
                    first_name=row.get("first_name", "").strip(),
                    last_name=row.get("last_name", "").strip(),
                    email=row.get("email"),
                    age=int(row["age"]) if row.get("age") else None,
                    gender=row.get("gender"),
                )
                self.members.append(member)

    def find_by_name(
        self,
        name: str,
        min_confidence: float = 0.70,
        ambiguity_threshold: float = 0.05,
    ) -> MatchResultDict:
        """Find a member by their full name using fuzzy matching.

        First checks name corrections mapping, then uses rapidfuzz to calculate
        similarity scores between the search name and all member names. Returns
        the best match if it exceeds the minimum confidence threshold. Flags
        matches as ambiguous if multiple members have similar scores.

        Args:
            name: Full name to search for
            min_confidence: Minimum confidence score (0.0-1.0) to accept a match
            ambiguity_threshold: Max score difference to flag as ambiguous

        Returns:
            Dictionary with member (or None), confidence score, and ambiguity flag
        """
        name_normalized = name.strip().lower()

        if not self.members:
            return MatchResultDict(member=None, confidence=0.0, is_ambiguous=False)

        # Check name corrections first
        if name_normalized in self.name_corrections:
            corrected_name = self.name_corrections[name_normalized]
            # Find the member with this corrected name (exact match)
            for member in self.members:
                if member.full_name.lower() == corrected_name.lower():
                    return MatchResultDict(
                        member=member, confidence=1.0, is_ambiguous=False
                    )

        # Calculate fuzzy match scores for all members
        scores: list[tuple[Member, float]] = []
        for member in self.members:
            # Use token_sort_ratio to handle word order variations
            score = fuzz.token_sort_ratio(name_normalized, member.full_name.lower())
            # Convert to 0.0-1.0 scale
            normalized_score = score / 100.0
            if normalized_score == 1.0:
                # Early exit on perfect match
                return MatchResultDict(member=member, confidence=1.0, is_ambiguous=False)
            scores.append((member, normalized_score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        if not scores:
            return MatchResultDict(member=None, confidence=0.0, is_ambiguous=False)
        best_member, best_score = scores[0]

        # Check if match meets minimum confidence threshold
        if best_score < min_confidence:
            return MatchResultDict(
                member=None, confidence=best_score, is_ambiguous=False
            )

        # Check for ambiguity: are there other members with similar scores?
        is_ambiguous = False
        if len(scores) > 1:
            second_best_score = scores[1][1]
            if (best_score - second_best_score) <= ambiguity_threshold:
                is_ambiguous = True

        return MatchResultDict(
            member=best_member, confidence=best_score, is_ambiguous=is_ambiguous
        )

    def get_all_members(self) -> list[Member]:
        """Return all members in the registry."""
        return self.members.copy()
