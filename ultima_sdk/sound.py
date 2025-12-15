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
    def initialize(cls, idx_path: str | None = None, mul_path: str | None = None) -> bool:
        """Initialize sound index."""
        if cls._initialized:
            return True

        try:
            if idx_path is None:
                idx_path = Files.get_file_path("soundidx.mul")
            if mul_path is None:
                mul_path = Files.get_file_path("sound.mul")

            if idx_path and mul_path:
                from .file_index import FileIndex
                from .verdata_ids import IDS as VERDATA_IDS

                cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.SOUND_MUL)
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

        if not cls._index:
            return None

        raw = cls._index.read_raw(sound_id)
        if not raw:
            return None

        if not cls._looks_like_wav(raw):
            raise WaveFormatException("Sound data is not a valid RIFF/WAVE stream")

        return SoundData(sound_id=sound_id, data=raw)

    @staticmethod
    def _looks_like_wav(data: bytes) -> bool:
        # Minimal RIFF/WAVE validation.
        if len(data) < 12:
            return False
        if data[0:4] != b"RIFF":
            return False
        if data[8:12] != b"WAVE":
            return False

        # If the RIFF chunk size is present and plausible, accept.
        # RIFF size excludes the leading 'RIFF' + size field (8 bytes).
        try:
            riff_size = int.from_bytes(data[4:8], "little", signed=False)
        except Exception:
            return False

        # Some writers use 0 or don't match exactly; be permissive but reject absurd values.
        if riff_size > (1024 * 1024 * 256):
            return False

        return True
