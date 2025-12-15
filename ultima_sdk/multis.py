"""
Multis module - Manages multi-tile object data (houses, ships, etc).
"""

from typing import Optional, List, Dict
import struct

from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class MultiComponent:
    """Represents a single component of a multi-tile object."""

    def __init__(self, item_id: int, x: int, y: int, z: int, flags: int = 0, unk1: int | None = None):
        self.item_id = item_id
        self.x = x
        self.y = y
        self.z = z
        self.flags = flags
        self.unk1 = unk1


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
    _index: Optional[FileIndex] = None
    _initialized = False

    @classmethod
    def initialize(cls, idx_path: str | None = None, mul_path: str | None = None) -> bool:
        """Initialize multi data."""
        if cls._initialized:
            # If the caller didn't request explicit paths, keep the current index.
            if idx_path is None and mul_path is None:
                return True
            # If explicit paths match the currently loaded index, no-op.
            if cls._index and idx_path == cls._index.idx_path and mul_path == cls._index.mul_path:
                return True

        try:
            if mul_path is None:
                mul_path = Files.get_file_path("multi.mul")
            if idx_path is None:
                idx_path = Files.get_file_path("multi.idx")

            if mul_path and idx_path:
                cls._load_multis(idx_path, mul_path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize multis: {e}")

        return False

    @classmethod
    def _load_multis(cls, idx_path: str, mul_path: str) -> None:
        """Load multi data from files."""
        from .verdata_ids import IDS as VERDATA_IDS

        cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.MULTI_MUL)
        cls._multis = {}

    @staticmethod
    def _score_decoding(components: List[MultiComponent]) -> int:
        """Heuristic score for a decoded multi record.

        Used to choose between classic 12-byte and newer 16-byte entry layouts.
        """
        score = 0
        sample = components[:64]
        for c in sample:
            # Offsets are typically small (tile-space). Prefer reasonable ranges.
            if -128 <= c.x <= 127 and -128 <= c.y <= 127 and -128 <= c.z <= 127:
                score += 2
            else:
                score -= 6

            if -60 <= c.x <= 60 and -60 <= c.y <= 60:
                score += 1

            # Item ids should be non-zero and within uint16.
            if 0 < c.item_id <= 0xFFFF:
                score += 1
            else:
                score -= 2

        # Prefer decodings that produce a plausible number of components.
        if 1 <= len(components) <= 50000:
            score += 2
        else:
            score -= 5

        return score

    @classmethod
    def _decode_components(cls, data: bytes) -> List[MultiComponent]:
        """Decode a multi.mul record into component entries.

        Layouts (little-endian):
        - Classic: 12 bytes/entry: uint16 itemId, int16 x, int16 y, int16 z, int32 flags
        - Newer:  16 bytes/entry: same + int32 unk1

        The loader picks the best matching layout using simple heuristics.
        """
        if not data:
            return []

        candidates: list[tuple[int, bool]] = []
        if len(data) % 12 == 0:
            candidates.append((12, False))
        if len(data) % 16 == 0:
            candidates.append((16, True))
        if not candidates:
            raise ValueError("Unsupported multi record length")

        best_components: List[MultiComponent] | None = None
        best_score: int | None = None

        for record_size, use_new_format in candidates:
            count = len(data) // record_size
            comps: List[MultiComponent] = []
            for i in range(count):
                base = i * record_size
                item_id, x, y, z = struct.unpack_from("<Hhhh", data, base)
                flags = struct.unpack_from("<i", data, base + 8)[0]
                unk1 = None
                if use_new_format:
                    unk1 = struct.unpack_from("<i", data, base + 12)[0]
                comps.append(MultiComponent(item_id=item_id, x=x, y=y, z=z, flags=flags, unk1=unk1))

            score = cls._score_decoding(comps)
            if best_score is None or score > best_score:
                best_score = score
                best_components = comps

        return best_components or []

    @classmethod
    def get_multi(cls, multi_id: int) -> Optional[MultiData]:
        """Get multi data by ID."""
        if not cls._initialized:
            cls.initialize()

        cached = cls._multis.get(multi_id)
        if cached is not None:
            return cached

        if not cls._index:
            return None

        raw = cls._index.read_raw(multi_id)
        if not raw:
            return None

        components = cls._decode_components(raw)
        multi = MultiData(multi_id)
        for c in components:
            multi.add_component(c)
        cls._multis[multi_id] = multi
        return multi
