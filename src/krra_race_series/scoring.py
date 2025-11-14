"""Module for calculating race series points."""

from dataclasses import dataclass
from typing import Dict, List

from .matching import MatchResult


@dataclass
class PointsConfig:
    """Configuration for the points scoring system."""
    
    # Default points: 1st place = 100, 2nd = 99, etc.
    base_points: int = 100
    decrement: int = 1
    minimum_points: int = 1
    
    def calculate_points(self, place: int) -> int:
        """Calculate points for a given finishing place.
        
        Args:
            place: Finishing position (1-indexed)
            
        Returns:
            Points awarded for that position
        """
        points = self.base_points - (place - 1) * self.decrement
        return max(points, self.minimum_points)


@dataclass
class RacePoints:
    """Points earned by a member in a single race."""
    
    member_id: str
    race_name: str
    place: int
    points: int


class PointsCalculator:
    """Calculates points for race results."""
    
    def __init__(self, config: PointsConfig = None):
        """Initialize the calculator with a points configuration.
        
        Args:
            config: Points configuration. Uses default if not provided.
        """
        self.config = config or PointsConfig()
    
    def calculate_race_points(self, match_results: List[MatchResult], 
                            race_name: str) -> List[RacePoints]:
        """Calculate points for all matched finishers in a race.
        
        Args:
            match_results: List of matched race results
            race_name: Name of the race
            
        Returns:
            List of points earned by each matched member
        """
        race_points = []
        
        for match in match_results:
            if match.matched and match.member:
                points = self.config.calculate_points(match.race_result.place)
                race_points.append(RacePoints(
                    member_id=match.member.member_id,
                    race_name=race_name,
                    place=match.race_result.place,
                    points=points
                ))
        
        return race_points


@dataclass
class SeriesTotal:
    """Cumulative series total for a member."""
    
    member_id: str
    member_name: str
    races_completed: int
    total_points: int
    race_details: List[RacePoints]


class SeriesScoring:
    """Manages cumulative scoring across the race series."""
    
    def __init__(self):
        self.all_race_points: List[RacePoints] = []
    
    def add_race_points(self, race_points: List[RacePoints]) -> None:
        """Add points from a race to the series.
        
        Args:
            race_points: Points earned in a race
        """
        self.all_race_points.extend(race_points)
    
    def calculate_series_totals(self, member_registry) -> List[SeriesTotal]:
        """Calculate cumulative totals for all members.
        
        Args:
            member_registry: Registry to get member names
            
        Returns:
            List of series totals sorted by total points (descending)
        """
        # Group points by member
        member_points: Dict[str, List[RacePoints]] = {}
        
        for race_point in self.all_race_points:
            if race_point.member_id not in member_points:
                member_points[race_point.member_id] = []
            member_points[race_point.member_id].append(race_point)
        
        # Calculate totals
        totals = []
        for member_id, points_list in member_points.items():
            member = next((m for m in member_registry.get_all_members() 
                          if m.member_id == member_id), None)
            member_name = member.full_name if member else "Unknown"
            
            total = SeriesTotal(
                member_id=member_id,
                member_name=member_name,
                races_completed=len(points_list),
                total_points=sum(p.points for p in points_list),
                race_details=points_list
            )
            totals.append(total)
        
        # Sort by total points (descending)
        totals.sort(key=lambda x: x.total_points, reverse=True)
        
        return totals
