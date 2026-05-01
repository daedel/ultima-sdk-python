"""
Hues module - Manages color palette data.
Supports full read AND write (modify individual hues + save whole file).
"""

import struct
from typing import List, Optional
from .binary_extensions import BinaryReader
from .files import Files
from .exceptions import FileAccessException

# hues.mul layout:
#   375 groups * (4-byte group header + 8 * 88-byte HueEntry records)
#   = 3000 hue entries total
#
#   Each 88-byte HueEntry:
#     32 bytes  = 16 * uint16 colors
#     2  bytes  = uint16 table_start
#     2  bytes  = uint16 table_end
#     20 bytes  = null-padded name
#     32 bytes  = 16 * uint16 colors again (duplicate "table" copy)

_HUES_PER_GROUP = 8
_ENTRY_SIZE = 88
_GROUPS = 375
_TOTAL_HUES = _HUES_PER_GROUP * _GROUPS  # 3000


class HueEntry:
    """Represents a single hue color entry."""

    def __init__(
        self,
        colors: List[int],
        table_start: int = 0,
        table_end: int = 0,
        name: str = "",
    ):
        self.colors: List[int] = list(colors)  # 16 BGR-555 values
        self.table_start = table_start
        self.table_end = table_end
        self.name = name

    def get_color(self, index: int) -> Optional[int]:
        if 0 <= index < len(self.colors):
            return self.colors[index]
        return None

    def set_color(self, index: int, value: int) -> None:
        """Set a single BGR-555 color slot. Call ``Hues.save()`` to persist."""
        if not (0 <= index < 16):
            raise IndexError(f"Color index {index} out of range (0-15)")
        self.colors[index] = int(value) & 0xFFFF


class Hues:
    """Static class for managing hue data."""

    _hues: List[HueEntry] = []
    _initialized = False

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    @classmethod
    def initialize(cls) -> bool:
        if cls._initialized:
            return True
        try:
            path = Files.get_file_path("hues.mul")
            if not path:
                return False
            with open(path, "rb") as f:
                reader = BinaryReader(f)
                cls._load_hues(reader)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to load hues.mul: {e}")

    @classmethod
    def _load_hues(cls, reader: BinaryReader) -> None:
        cls._hues = []
        for _group in range(_GROUPS):
            reader.read_uint32()  # group header
            for _ in range(_HUES_PER_GROUP):
                colors = [reader.read_uint16() for _ in range(16)]
                table_start = reader.read_uint16()
                table_end = reader.read_uint16()
                raw_name = reader.read_string(20, null_terminated=True)
                name = raw_name.strip("\x00")
                cls._hues.append(HueEntry(colors, table_start, table_end, name))

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @classmethod
    def get_hue(cls, id: int) -> Optional[HueEntry]:
        if not cls._initialized:
            cls.initialize()
        if 0 <= id < len(cls._hues):
            return cls._hues[id]
        return None

    @classmethod
    def count(cls) -> int:
        if not cls._initialized:
            cls.initialize()
        return len(cls._hues)

    # ------------------------------------------------------------------
    # In-memory patch
    # ------------------------------------------------------------------

    @classmethod
    def set_hue(
        cls,
        id: int,
        colors: List[int] | None = None,
        table_start: int | None = None,
        table_end: int | None = None,
        name: str | None = None,
    ) -> None:
        """Patch a hue entry in memory. Call :meth:`save` to persist.

        Parameters
        ----------
        id:
            Zero-based hue index (0-2999).
        colors:
            Optional list of exactly 16 BGR-555 values.
        table_start / table_end:
            Optional range markers stored in the entry.
        name:
            Optional display name (max 20 chars).
        """
        if not cls._initialized:
            cls.initialize()
        if not (0 <= id < len(cls._hues)):
            raise IndexError(f"Hue id {id} out of range")
        h = cls._hues[id]
        if colors is not None:
            if len(colors) != 16:
                raise ValueError("colors must be exactly 16 values")
            h.colors = [int(c) & 0xFFFF for c in colors]
        if table_start is not None:
            h.table_start = int(table_start) & 0xFFFF
        if table_end is not None:
            h.table_end = int(table_end) & 0xFFFF
        if name is not None:
            h.name = str(name)[:20]

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    @classmethod
    def save(cls, path: str | None = None) -> None:
        """Write the full hues.mul to *path*.

        If *path* is ``None``, overwrites the original file.
        Each entry writes its 16 color words twice (primary + table duplicate)
        to match the original EA format exactly.
        """
        if not cls._initialized:
            cls.initialize()
        if path is None:
            path = Files.get_file_path("hues.mul")
        if not path:
            raise FileAccessException("No hues.mul path available")

        with open(path, "wb") as f:
            for g in range(_GROUPS):
                f.write(struct.pack("<I", 0))  # group header
                for i in range(_HUES_PER_GROUP):
                    h = cls._hues[g * _HUES_PER_GROUP + i]
                    # Primary color table
                    for c in h.colors:
                        f.write(struct.pack("<H", c))
                    f.write(struct.pack("<HH", h.table_start, h.table_end))
                    name_bytes = h.name.encode("latin-1", errors="replace")[:20]
                    f.write(name_bytes.ljust(20, b"\x00"))
                    # Duplicate color table (EA format requires this)
                    for c in h.colors:
                        f.write(struct.pack("<H", c))
