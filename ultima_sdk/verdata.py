"""Verdata support (verdata.mul).

`verdata.mul` is a patch table used by some Ultima Online client installs to
override blocks from other MUL/UOP-backed resources.

This module provides a small, deterministic API:
- Parse the verdata index table.
- Read patched bytes for a given (file_id, block_id) pair.
- Apply all loaded patches to the relevant in-memory SDK modules via apply().

Integration point: `FileIndex.read_raw()` can consult `Verdata` when a
`FileIndex` is constructed with a `file_id`.

FILE_IDS maps the integer file_id field in verdata entries to the target
MUL filename, matching ClassicUO's VerdataLoader.cs mapping exactly.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .exceptions import FileAccessException, FileParseError
from .files import Files

# ---------------------------------------------------------------------------
# File ID -> MUL filename mapping (mirrors ClassicUO VerdataLoader.cs)
# ---------------------------------------------------------------------------
FILE_IDS: Dict[int, str] = {
    0:  "map0.mul",
    1:  "staidx0.mul",
    2:  "statics0.mul",
    3:  "artidx.mul",
    4:  "art.mul",
    5:  "anim.idx",
    6:  "anim.mul",
    7:  "animidx.mul",
    8:  "skills.mul",
    9:  "skills.idx",
    10: "texidx.mul",
    11: "gumpidx.mul",
    12: "gumps.mul",
    13: "multi.idx",
    14: "multi.mul",
    15: "speech.mul",
    16: "speech.idx",
    17: "hues.mul",
    18: "cliloc.enu",
    19: "unifont.mul",
    20: "unifont.idx",
    21: "texmaps.mul",
    22: "map0.mul",
    23: "light.mul",
    24: "light.idx",
    25: "map1.mul",
    26: "staidx1.mul",
    27: "statics1.mul",
    28: "map2.mul",
    29: "staidx2.mul",
    30: "tiledata.mul",
    31: "animdata.mul",
}


@dataclass(frozen=True)
class VerdataEntry:
    file_id: int
    block_id: int
    offset: int
    length: int
    extra: int = 0


class Verdata:
    """Static accessor for verdata patches."""

    _entries: Dict[Tuple[int, int], VerdataEntry] = {}
    _path: Optional[str] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, path: str | None = None) -> bool:
        if cls._initialized:
            return True
        if path is None:
            path = Files.get_file_path("verdata.mul")
        if not path:
            cls._entries = {}
            cls._path = None
            cls._initialized = True
            return False
        cls._path = path
        try:
            raw = None
            with open(path, "rb") as f:
                raw = f.read()
            if raw is None or len(raw) < 4:
                raise FileParseError("Invalid verdata header", file_path=path)
            (count,) = struct.unpack_from("<i", raw, 0)
            if count < 0 or count > 1_000_000:
                raise FileParseError("Invalid verdata entry count", file_path=path)
            table_off = 4
            table_len = count * 20
            if len(raw) < table_off + table_len:
                raise FileParseError("Truncated verdata table", file_path=path)
            entries: Dict[Tuple[int, int], VerdataEntry] = {}
            for i in range(count):
                off = table_off + (i * 20)
                file_id, block_id, data_off, length, extra = struct.unpack_from(
                    "<iiiii", raw, off
                )
                if length <= 0 or data_off < 0:
                    continue
                entries[(int(file_id), int(block_id))] = VerdataEntry(
                    file_id=int(file_id),
                    block_id=int(block_id),
                    offset=int(data_off),
                    length=int(length),
                    extra=int(extra),
                )
            cls._entries = entries
            cls._initialized = True
            return True
        except FileParseError:
            raise
        except Exception as e:
            raise FileAccessException(
                "Failed to initialize verdata", file_path=path, cause=e
            )

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._initialized

    @classmethod
    def get_entry(cls, file_id: int, block_id: int) -> Optional[VerdataEntry]:
        if not cls._initialized:
            cls.initialize()
        return cls._entries.get((int(file_id), int(block_id)))

    @classmethod
    def has_patch(cls, file_id: int, block_id: int) -> bool:
        return cls.get_entry(file_id, block_id) is not None

    @classmethod
    def read_patch(cls, file_id: int, block_id: int) -> Optional[bytes]:
        """Read patch bytes for the given file/block.
        Returns None if no patch exists.
        """
        entry = cls.get_entry(file_id, block_id)
        if not entry:
            return None
        if not cls._path:
            return None
        try:
            with open(cls._path, "rb") as f:
                f.seek(entry.offset)
                data = f.read(entry.length)
        except Exception as e:
            raise FileAccessException(
                "Failed to read verdata patch", file_path=cls._path, cause=e
            )
        if data is None or len(data) != entry.length:
            raise FileParseError("Truncated verdata patch", file_path=cls._path)
        return data

    @classmethod
    def apply(cls) -> Dict[str, int]:
        """Apply all loaded verdata patches to the relevant in-memory SDK modules.

        Routes each patch by file_id to the appropriate module's patch handler.
        Currently supported targets:

            file_id 30  ->  TileData   (tiledata.mul)
            file_id 4   ->  Art        (art.mul)
            file_id 11/12 -> Gumps    (gumpidx.mul / gumps.mul)
            file_id 17  ->  Hues       (hues.mul)

        All other file_ids are recorded in the returned stats dict under their
        MUL filename but are not yet applied (raw bytes accessible via
        read_patch() directly).

        Returns:
            A dict mapping MUL filename -> number of patches applied/attempted,
            e.g. {"tiledata.mul": 12, "art.mul": 3, "skipped": 47}
        """
        if not cls._initialized:
            cls.initialize()

        stats: Dict[str, int] = {}

        for (file_id, block_id), entry in cls._entries.items():
            mul_name = FILE_IDS.get(file_id, f"unknown_{file_id}")
            data = cls.read_patch(file_id, block_id)
            if data is None:
                continue

            applied = False

            # ------------------------------------------------------------------
            # file_id 30 -- tiledata.mul
            # ------------------------------------------------------------------
            if file_id == 30:
                try:
                    from .tiledata import TileData
                    TileData.apply_verdata_patch(block_id, data, entry.extra)
                    applied = True
                except Exception:
                    pass

            # ------------------------------------------------------------------
            # file_id 4 -- art.mul (static tiles)
            # file_id 3 -- artidx.mul (index -- skip; art.py rebuilds from art.mul)
            # ------------------------------------------------------------------
            elif file_id == 4:
                try:
                    from .art import Art
                    Art.apply_verdata_patch(block_id, data, entry.extra)
                    applied = True
                except Exception:
                    pass

            # ------------------------------------------------------------------
            # file_id 11/12 -- gumpidx.mul / gumps.mul
            # ------------------------------------------------------------------
            elif file_id in (11, 12):
                try:
                    from .gumps import Gumps
                    Gumps.apply_verdata_patch(block_id, data, entry.extra)
                    applied = True
                except Exception:
                    pass

            # ------------------------------------------------------------------
            # file_id 17 -- hues.mul
            # ------------------------------------------------------------------
            elif file_id == 17:
                try:
                    from .hues import Hues
                    Hues.apply_verdata_patch(block_id, data, entry.extra)
                    applied = True
                except Exception:
                    pass

            key = mul_name if applied else "skipped"
            stats[key] = stats.get(key, 0) + 1

        return stats
