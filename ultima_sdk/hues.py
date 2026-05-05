"""
Hues module - Reads and writes hue palette data from hues.mul.

Each hue group block is 708 bytes:
  header: 4 bytes (unused)
  8 hue entries × 88 bytes each

Each hue entry (88 bytes):
  32 × uint16  colors          (64 bytes) — all 32 colors in one contiguous block
  uint16       tableStart
  uint16       tableEnd
  char[20]     name
  = 64 + 2 + 2 + 20 = 88 bytes ✓

Color storage: 15-bit RGB, bit 15 = opaque flag.
  On read:  color |= 0x8000   (mark opaque)
  On write: color ^= 0x8000   (strip opaque bit back to storage format)

Total entries: 3000  (375 groups × 8 entries)
"""

import struct
from typing import List, Optional, Dict
from .files import Files
from .exceptions import FileAccessException

_GROUP_HEADER_SIZE = 4
_ENTRIES_PER_GROUP = 8
_COLORS_PER_ENTRY  = 32
_ENTRY_SIZE        = 88   # 32*2 + 2 + 2 + 20
_GROUP_SIZE        = _GROUP_HEADER_SIZE + _ENTRIES_PER_GROUP * _ENTRY_SIZE  # 708


class Hues:
    """Static class for managing hue palette data."""

    _entries: List[Dict] = []
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> bool:
        if cls._initialized:
            return True
        try:
            path = Files.get_file_path("hues.mul")
            if not path:
                return False
            with open(path, "rb") as f:
                data = f.read()
            cls._entries = cls._parse(data)
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to load hues.mul: {e}")

    @staticmethod
    def _parse(data: bytes) -> List[Dict]:
        entries: List[Dict] = []
        pos = 0
        while pos + _GROUP_SIZE <= len(data):
            pos += _GROUP_HEADER_SIZE  # skip group header
            for _ in range(_ENTRIES_PER_GROUP):
                entry_start = pos
                # Read all 32 colors as one contiguous block — THEN metadata.
                raw_colors = struct.unpack_from("<32H", data, pos)
                pos += _COLORS_PER_ENTRY * 2   # 64 bytes

                (table_start,) = struct.unpack_from("<H", data, pos)
                pos += 2
                (table_end,) = struct.unpack_from("<H", data, pos)
                pos += 2

                raw_name = data[pos: pos + 20]
                pos += 20

                name = raw_name.split(b"\x00", 1)[0].decode("latin-1")

                # Apply opaque bit to every non-zero color on read.
                colors = [
                    (c | 0x8000) if c != 0 else 0
                    for c in raw_colors
                ]

                entries.append(
                    {
                        "colors":      colors,
                        "tableStart":  table_start,
                        "tableEnd":    table_end,
                        "name":        name,
                    }
                )
        return entries

    @classmethod
    def get_hue(cls, id: int) -> Optional[Dict]:
        if not cls._initialized:
            cls.initialize()
        if 0 <= id < len(cls._entries):
            return cls._entries[id]
        return None

    @classmethod
    def get_count(cls) -> int:
        if not cls._initialized:
            cls.initialize()
        return len(cls._entries)

    @classmethod
    def set_hue(cls, id: int, **fields) -> None:
        """Patch one or more fields on a hue entry (in memory).

        Recognised keys: ``colors`` (list of 32 ints), ``tableStart``,
        ``tableEnd``, ``name``.
        """
        if not cls._initialized:
            cls.initialize()
        if not (0 <= id < len(cls._entries)):
            raise IndexError(f"Hue id {id} out of range")
        entry = dict(cls._entries[id])
        for k, v in fields.items():
            if k not in entry:
                raise KeyError(f"Unknown hue field: {k!r}")
            entry[k] = v
        cls._entries[id] = entry

    @classmethod
    def save(cls, path: str | None = None) -> None:
        """Write hues.mul to *path* (or overwrite original if None)."""
        if not cls._initialized:
            cls.initialize()
        if path is None:
            path = Files.get_file_path("hues.mul")
        if not path:
            raise FileAccessException("No hues.mul path available")

        num_groups = (len(cls._entries) + _ENTRIES_PER_GROUP - 1) // _ENTRIES_PER_GROUP
        with open(path, "wb") as f:
            for g in range(num_groups):
                f.write(b"\x00" * _GROUP_HEADER_SIZE)  # group header
                for i in range(_ENTRIES_PER_GROUP):
                    idx = g * _ENTRIES_PER_GROUP + i
                    if idx < len(cls._entries):
                        entry = cls._entries[idx]
                    else:
                        entry = {
                            "colors":     [0] * _COLORS_PER_ENTRY,
                            "tableStart": 0,
                            "tableEnd":   0,
                            "name":       "",
                        }
                    # Strip opaque bit on write: color ^ 0x8000 for non-zero colors.
                    storage_colors = [
                        (c ^ 0x8000) if c != 0 else 0
                        for c in entry["colors"]
                    ]
                    f.write(struct.pack("<32H", *storage_colors))
                    f.write(struct.pack("<HH", entry["tableStart"], entry["tableEnd"]))
                    name_bytes = entry["name"].encode("latin-1", errors="replace")[:20]
                    f.write(name_bytes.ljust(20, b"\x00"))
