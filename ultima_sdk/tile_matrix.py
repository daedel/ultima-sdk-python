"""
TileMatrix module - Manages tile matrix data for maps.
Supports read AND write (set_tile with dirty tracking + save for in-place block patching).
"""

from typing import Optional, Tuple

import os
import struct


class TileMatrix:
    """Represents a tile matrix for a map."""

    def __init__(
        self,
        map_id: int,
        width: int,
        height: int,
        map_path: str | None = None,
        *,
        map_uop_path: str | None = None,
        map_uop_pattern: str | None = None,
    ):
        self.map_id       = map_id
        self.width        = width
        self.height       = height
        self.tiles: list  = []
        self.map_path     = map_path

        self._uop         = None
        self._uop_pattern = map_uop_pattern
        self._uop_segment_cache: dict[int, bytes] = {}

        if map_uop_path and map_uop_pattern:
            from .uop import UopFile
            self._uop = UopFile(map_uop_path, map_uop_pattern)

        self._verdata_file_id: int | None = None
        if map_id == 0:
            try:
                from .verdata_ids import IDS as VERDATA_IDS
                self._verdata_file_id = VERDATA_IDS.MAP0_MUL
            except Exception:
                self._verdata_file_id = None

        self.block_width  = width >> 3
        self.block_height = height >> 3

        self._land_block_cache: dict[tuple[int, int], list[tuple[int, int]]] = {}
        # Blocks modified via set_tile that have not yet been flushed to disk.
        self._dirty_blocks: dict[tuple[int, int], list[tuple[int, int]]] = {}

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_tile(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Get tile ID and altitude at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.map_path or self._uop is not None:
                return self._get_tile_from_map_file(x, y)
            idx = y * self.width + x
            if idx < len(self.tiles):
                return self.tiles[idx]
        return None

    def _get_tile_from_map_file(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        if not self.map_path and not self._uop:
            return None
        if self.map_path and not os.path.exists(self.map_path):
            return None

        bx = x >> 3
        by = y >> 3
        if bx < 0 or by < 0 or bx >= self.block_width or by >= self.block_height:
            return None

        block = self._get_land_block(bx, by)
        ti    = ((y & 0x7) << 3) + (x & 0x7)
        if 0 <= ti < 64:
            return block[ti]
        return None

    def _get_land_block(self, bx: int, by: int) -> list[tuple[int, int]]:
        key = (bx, by)
        # Dirty blocks take priority over the read cache.
        dirty = self._dirty_blocks.get(key)
        if dirty is not None:
            return dirty

        cached = self._land_block_cache.get(key)
        if cached is not None:
            return cached

        block_index = (bx * self.block_height) + by
        block: list[tuple[int, int]] = [(0, 0)] * 64

        raw = b""
        # Verdata override (map0 only).
        if self._verdata_file_id is not None:
            try:
                from .verdata import Verdata
                patch = Verdata.read_patch(self._verdata_file_id, int(block_index))
            except Exception:
                patch = None
            if patch is not None and len(patch) >= 196:
                raw = patch[4:4 + (64 * 3)]

        if not raw:
            if self._uop is not None:
                segment_id = int(block_index >> 12)
                within     = int(block_index & 0x0FFF)
                segment    = self._uop_segment_cache.get(segment_id)
                if segment is None:
                    segment = self._uop.read_raw(segment_id) or b""
                    self._uop_segment_cache[segment_id] = segment
                base = (within * 196) + 4
                end  = base + (64 * 3)
                raw  = segment[base:end] if end <= len(segment) else b""
            else:
                base = (block_index * 196) + 4
                if self.map_path:
                    with open(self.map_path, "rb") as f:
                        f.seek(base)
                        raw = f.read(64 * 3)

        if len(raw) == 64 * 3:
            for i in range(64):
                tile_id, z = struct.unpack_from("<Hb", raw, i * 3)
                block[i] = (int(tile_id), int(z))

        self._land_block_cache[key] = block
        return block

    # ------------------------------------------------------------------
    # In-memory write
    # ------------------------------------------------------------------

    def set_tile(self, x: int, y: int, tile_id: int, altitude: int) -> None:
        """Set a tile in memory and mark its 8x8 block dirty.

        Reads are immediately consistent after this call.
        Call :meth:`save` to flush dirty blocks to disk.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        # Update the flat tile list (in-memory / no-file mode).
        idx = y * self.width + x
        while len(self.tiles) <= idx:
            self.tiles.append((0, 0))
        self.tiles[idx] = (int(tile_id), int(altitude))

        # Load the whole block first so adjacent tiles are not lost.
        bx  = x >> 3
        by  = y >> 3
        key = (bx, by)
        block = list(self._get_land_block(bx, by))
        ti    = ((y & 0x7) << 3) + (x & 0x7)
        block[ti] = (int(tile_id), int(altitude))

        self._dirty_blocks[key]     = block
        self._land_block_cache[key] = block

    # ------------------------------------------------------------------
    # Flush to disk
    # ------------------------------------------------------------------

    def save(self, path: str | None = None) -> None:
        """Flush all dirty blocks to *path* (map*.mul) with in-place patching.

        Only blocks modified via :meth:`set_tile` are rewritten; all other
        blocks remain untouched on disk.  The 4-byte block header is
        preserved from the existing file.

        Parameters
        ----------
        path:
            Output file path. Defaults to :attr:`map_path`.  UOP-backed
            maps do not support in-place write via this method.
        """
        if path is None:
            path = self.map_path
        if not path:
            from .exceptions import FileAccessException
            raise FileAccessException(
                "No map_path set on TileMatrix — "
                "UOP-backed maps cannot be written in-place via save()."
            )

        if not self._dirty_blocks:
            return

        with open(path, 'r+b') as f:
            for (bx, by), block in self._dirty_blocks.items():
                block_index = (bx * self.block_height) + by
                # Each map block is 196 bytes: 4-byte header + 64 * 3-byte tiles.
                block_offset = block_index * 196
                f.seek(block_offset)
                header = f.read(4)
                if len(header) < 4:
                    header = b"\x00" * 4
                f.seek(block_offset)
                f.write(header)
                for tile_id, z in block:
                    f.write(struct.pack("<Hb", tile_id & 0xFFFF, z & 0xFF))

        self._dirty_blocks.clear()

    def has_unsaved_changes(self) -> bool:
        """Return ``True`` if any blocks have been modified but not yet saved."""
        return bool(self._dirty_blocks)
