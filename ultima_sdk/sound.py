"""
Sound module - Manages sound and music data.
"""

from typing import Optional
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException, WaveFormatException


class SoundData:
    """Represents sound data."""

    def __init__(self, sound_id: int, data: bytes):
        self.sound_id = sound_id
        self.data = data


class Sound:
    """Static class for managing sound data."""

    _index: Optional[FileIndex] = None
    _initialized = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize sound index."""
        if cls._initialized:
            return True

        try:
            idx_path = Files.get_file_path("soundidx.mul")
            mul_path = Files.get_file_path("sound.mul")

            if idx_path and mul_path:
                from .file_index import FileIndex
                cls._index = FileIndex(idx_path, mul_path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize sounds: {e}")

        return False

    @classmethod
    def get_sound(cls, sound_id: int) -> Optional[SoundData]:
        """Get sound by ID."""
        if not cls._initialized:
            cls.initialize()

        return None
