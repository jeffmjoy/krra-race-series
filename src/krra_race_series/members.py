"""Module for managing KRRA member data."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Member:
    """Represents a KRRA member."""
    
    member_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Return the member's full name."""
        return f"{self.first_name} {self.last_name}"


class MemberRegistry:
    """Manages the registry of KRRA members."""
    
    def __init__(self):
        self.members: List[Member] = []
    
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
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                member = Member(
                    member_id=row.get('member_id', ''),
                    first_name=row.get('first_name', '').strip(),
                    last_name=row.get('last_name', '').strip(),
                    email=row.get('email'),
                    age=int(row['age']) if row.get('age') else None,
                    gender=row.get('gender')
                )
                self.members.append(member)
    
    def find_by_name(self, name: str) -> Optional[Member]:
        """Find a member by their full name (exact match).
        
        Args:
            name: Full name to search for
            
        Returns:
            Member if found, None otherwise
        """
        name_normalized = name.strip().lower()
        
        for member in self.members:
            if member.full_name.lower() == name_normalized:
                return member
        
        return None
    
    def get_all_members(self) -> List[Member]:
        """Return all members in the registry."""
        return self.members.copy()
