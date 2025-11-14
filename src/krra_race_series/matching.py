"""Module for matching race finishers with KRRA members."""

from dataclasses import dataclass
from typing import List, Optional

from .members import Member, MemberRegistry
from .race_results import RaceResult


@dataclass
class MatchResult:
    """Represents the result of matching a race finisher to a member."""

    race_result: RaceResult
    member: Optional[Member]
    matched: bool

    @property
    def member_id(self) -> Optional[str]:
        """Return the member ID if matched."""
        return self.member.member_id if self.member else None


class FinisherMatcher:
    """Matches race finishers with KRRA members."""

    def __init__(self, member_registry: MemberRegistry):
        """Initialize the matcher with a member registry.

        Args:
            member_registry: Registry of KRRA members
        """
        self.member_registry = member_registry

    def match_finisher(self, race_result: RaceResult) -> MatchResult:
        """Match a race finisher to a KRRA member.

        Currently performs exact name matching. Future versions will implement
        fuzzy matching with confidence levels.

        Args:
            race_result: Race result to match

        Returns:
            MatchResult indicating if a match was found
        """
        member = self.member_registry.find_by_name(race_result.name)

        return MatchResult(
            race_result=race_result, member=member, matched=member is not None
        )

    def match_all(self, race_results: List[RaceResult]) -> List[MatchResult]:
        """Match all race results to KRRA members.

        Args:
            race_results: List of race results to match

        Returns:
            List of match results
        """
        return [self.match_finisher(result) for result in race_results]
