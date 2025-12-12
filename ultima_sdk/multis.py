"""
Multis module - Manages multi-tile object data (houses, ships, etc).
"""

from typing import Optional, List, Dict
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException


class MultiComponent:
    """Represents a single component of a multi-tile object."""

    def __init__(self, item_id: int, x: int, y: int, z: int, flags: int = 0):
        self.item_id = item_id
        self.x = x
        self.y = y
        self.z = z
        self.flags = flags


class MultiData:
    """Represents multi-tile object data."""

    def __init__(self, multi_id: int):
        self.multi_id = multi_id
        self.components: List[MultiComponent] = []

    def add_component(self, component: MultiComponent) -> None:
        """Add a component to this multi."""
        self.components.append(component)


class Multis:
    """Static class for managing multi data."""

    _multis: Dict[int, MultiData] = {}
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize multi data."""
        if cls._initialized:
            return True

        try:
            path = Files.get_file_path("multi.mul")
            idx_path = Files.get_file_path("multi.idx")

            if path and idx_path:
                cls._load_multis(idx_path, path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize multis: {e}")

        return False

    @classmethod
    def _load_multis(cls, idx_path: str, mul_path: str) -> None:
        """Load multi data from files."""
        # Implementation
        pass

    @classmethod
    def get_multi(cls, multi_id: int) -> Optional[MultiData]:
        """Get multi data by ID."""
        if not cls._initialized:
            cls.initialize()

        return cls._multis.get(multi_id)
