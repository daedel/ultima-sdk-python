"""
Skills module - Manages skill information and data.
"""

from typing import List, Optional, Dict
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException


class SkillInfo:
    """Information about a skill."""

    def __init__(self, skill_id: int, name: str, button_id: int):
        self.skill_id = skill_id
        self.name = name
        self.button_id = button_id


class Skills:
    """Static class for managing skill data."""

    _skills: List[SkillInfo] = []
    _skill_map: Dict[str, SkillInfo] = {}
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize skill data."""
        if cls._initialized:
            return True

        try:
            cls._load_skills()
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize skills: {e}")

    @classmethod
    def _load_skills(cls) -> None:
        """Load skill data from file."""
        # Implementation would load from skills.mul
        pass

    @classmethod
    def get_skill(cls, skill_id: int) -> Optional[SkillInfo]:
        """Get skill by ID."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= skill_id < len(cls._skills):
            return cls._skills[skill_id]
        return None

    @classmethod
    def find_skill(cls, name: str) -> Optional[SkillInfo]:
        """Find skill by name."""
        if not cls._initialized:
            cls.initialize()

        return cls._skill_map.get(name.lower())
