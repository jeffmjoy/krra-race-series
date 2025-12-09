"""Module for matching race finishers with KRRA members."""

from dataclasses import dataclass

from .members import Member, MemberRegistry
from .race_results import RaceResult


@dataclass
class MatchResult:
    """Represents the result of matching a race finisher to a member."""

    race_result: RaceResult
    member: Member | None
    matched: bool
    confidence: float = 1.0  # 0.0 to 1.0, where 1.0 = exact match
    is_ambiguous: bool = False  # True if multiple members had similar scores

    @property
    def member_id(self) -> str | None:
        """Return the member ID if matched."""
        return self.member.member_id if self.member else None


class FinisherMatcher:
    """Matches race finishers with KRRA members."""

    def __init__(
        self,
        member_registry: MemberRegistry,
        min_confidence: float = 0.70,
        ambiguity_threshold: float = 0.05,
    ):
        """Initialize the matcher with a member registry.

        Args:
            member_registry: Registry of KRRA members
            min_confidence: Minimum confidence score (0.0-1.0) to accept a match
            ambiguity_threshold: Max score difference to flag as ambiguous
        """
        self.member_registry = member_registry
        self.min_confidence = min_confidence
        self.ambiguity_threshold = ambiguity_threshold

    def match_finisher(self, race_result: RaceResult) -> MatchResult:
        """Match a race finisher to a KRRA member using fuzzy matching.

        Uses rapidfuzz to find the best matching member name with confidence scoring.
        Flags matches as ambiguous if multiple members have similar scores.

        Args:
            race_result: Race result to match

        Returns:
            MatchResult with confidence score and ambiguity flag
        """
        result = self.member_registry.find_by_name(
            race_result.name,
            min_confidence=self.min_confidence,
            ambiguity_threshold=self.ambiguity_threshold,
        )

        return MatchResult(
            race_result=race_result,
            member=result["member"],
            matched=result["member"] is not None,
            confidence=result["confidence"],
            is_ambiguous=result["is_ambiguous"],
        )

    def match_all(self, race_results: list[RaceResult]) -> list[MatchResult]:
        """Match all race results to KRRA members.

        Args:
            race_results: List of race results to match

        Returns:
            List of match results
        """
        return [self.match_finisher(result) for result in race_results]
