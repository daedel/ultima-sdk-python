"""Verdata support (verdata.mul).

`verdata.mul` is a patch table used by some Ultima Online client installs to
override blocks from other MUL/UOP-backed resources.

This module provides a small, deterministic API:
- Parse the verdata index table.
- Read patched bytes for a given (file_id, block_id) pair.

Integration point: `FileIndex.read_raw()` can consult `Verdata` when a
`FileIndex` is constructed with a `file_id`.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .exceptions import FileAccessException, FileParseError
from .files import Files


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
