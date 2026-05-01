"""
Map module - Manages map and terrain data.
"""

from typing import Optional, Dict, Tuple
import math
import os

from .tile_matrix import TileMatrix
from .files import Files
from .exceptions import FileAccessException


class MapData:
    """Represents map terrain data."""

    def __init__(self, map_id: int):
        self.map_id = map_id
        self.tile_matrix: Optional[TileMatrix] = None

    def get_tile(self, x: int, y: int) -> Optional[Tuple[int, int]]:
    """Get tile ID and altitude at coordinates."""
    if 0 <= x < self.width and 0 <= y < self.height:
        if self.map_path or self._uop is not None:
            return self._get_tile_from_map_file(x, y)

        idx = y * self.width + x
        if idx < len(self.tiles):
            return self.tiles[idx]
    return None


class Map:
    """Static class for managing map data."""

    _maps: Dict[int, MapData] = {}
    _initialized = False

    # Default map dimensions in tiles (from common client layouts).
    DEFAULT_MAP_SIZES: Dict[int, Tuple[int, int]] = {
        0: (6144, 4096),
        1: (6144, 4096),
        2: (2304, 1600),
        3: (2560, 2048),
        4: (1448, 1448),
        5: (1280, 4096),
    }

    @classmethod
    def initialize(cls) -> bool:
        """Initialize map data."""
        if cls._initialized:
            return True

        try:
            cls._load_maps()
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize map: {e}")

    @classmethod
    def _load_maps(cls) -> None:
        """Load all map data."""
        cls._maps = {}

        # Load all map files
        for i in range(11):
            map_mul = Files.get_file_path(f"map{i}.mul")
            if map_mul:
                width, height = cls._infer_map_size(i, map_mul)
                map_data = MapData(i)
                map_data.tile_matrix = TileMatrix(map_id=i, width=width, height=height, map_path=map_mul)
                cls._maps[i] = map_data
                continue

            map_uop = Files.get_file_path(f"map{i}legacymul.uop")
            if map_uop:
                width, height = cls._infer_map_size_from_uop(i, map_uop)
                map_data = MapData(i)
                map_data.tile_matrix = TileMatrix(
                    map_id=i,
                    width=width,
                    height=height,
                    map_path=None,
                    map_uop_path=map_uop,
                    map_uop_pattern=f"build/map{i}legacymul/{{0:D8}}.dat",
                )
                cls._maps[i] = map_data

    @classmethod
    def _infer_map_size(cls, map_id: int, path: str) -> Tuple[int, int]:
        """Infer map dimensions in tiles.

        `map*.mul` stores 8x8 blocks, 196 bytes per block.
        When the file does not match known client sizes, fall back to a best-effort
        factorization of the number of blocks.
        """
        try:
            file_len = os.path.getsize(path)
        except Exception:
            # Safe fallback.
            return cls.DEFAULT_MAP_SIZES.get(map_id, (8, 8))

        if file_len < 196:
            return (8, 8)

        blocks = file_len // 196
        if blocks <= 1:
            return (8, 8)

        default = cls.DEFAULT_MAP_SIZES.get(map_id)
        if default:
            w, h = default
            expected_blocks = (w >> 3) * (h >> 3)
            if expected_blocks > 0 and file_len >= expected_blocks * 196:
                return default

        # Best-effort: choose factor pair (bw,bh) with minimal difference.
        best_bw = blocks
        best_bh = 1
        best_diff = blocks
        limit = int(math.isqrt(blocks))
        for bh in range(1, limit + 1):
            if blocks % bh != 0:
                continue
            bw = blocks // bh
            diff = abs(bw - bh)
            if diff < best_diff:
                best_bw, best_bh, best_diff = bw, bh, diff

        return (best_bw << 3, best_bh << 3)

    @classmethod
    def _infer_map_size_from_uop(cls, map_id: int, uop_path: str) -> Tuple[int, int]:
        """Infer map dimensions from a UOP container.

        We avoid decompressing full segments by using UOP entry metadata:
        each entry holds N * 196-byte map blocks.
        """
        try:
            from .uop import UopFile

            u = UopFile(uop_path, f"build/map{map_id}legacymul/{{0:D8}}.dat")
            u.parse()

            blocks = 0
            saw_any = False
            for segment_id in range(0, 4096):
                entry = u.get_entry(segment_id)
                if entry is None:
                    break
                saw_any = True
                length = entry.decompressed_length if entry.decompressed_length > 0 else entry.compressed_length
                if length > 0:
                    blocks += (length // 196)

            if not saw_any or blocks <= 0:
                return cls.DEFAULT_MAP_SIZES.get(map_id, (8, 8))

            if blocks == 1:
                return (8, 8)

            default = cls.DEFAULT_MAP_SIZES.get(map_id)
            if default:
                w, h = default
                expected_blocks = (w >> 3) * (h >> 3)
                if expected_blocks > 0 and blocks >= expected_blocks:
                    return default

            # Best-effort: choose factor pair (bw,bh) with minimal difference.
            best_bw = blocks
            best_bh = 1
            best_diff = blocks
            limit = int(math.isqrt(blocks))
            for bh in range(1, limit + 1):
                if blocks % bh != 0:
                    continue
                bw = blocks // bh
                diff = abs(bw - bh)
                if diff < best_diff:
                    best_bw, best_bh, best_diff = bw, bh, diff

            return (best_bw << 3, best_bh << 3)
        except Exception:
            return cls.DEFAULT_MAP_SIZES.get(map_id, (8, 8))

    @classmethod
    def get_map(cls, map_id: int) -> Optional[MapData]:
        """Get map data by ID."""
        if not cls._initialized:
            cls.initialize()

        return cls._maps.get(map_id)
