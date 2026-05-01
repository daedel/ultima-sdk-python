"""
Multis module - Manages multi-tile object data (houses, ships, etc).
Supports full read AND write (add/remove components + save to multi.mul/idx).
"""

from typing import Optional, List, Dict
import struct

from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException


class MultiComponent:
    """Represents a single component of a multi-tile object."""

    def __init__(
        self,
        item_id: int,
        x: int,
        y: int,
        z: int,
        flags: int = 0,
        unk1: int | None = None,
    ):
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
        """Append a component."""
        self.components.append(component)

    def remove_component(self, index: int) -> None:
        """Remove a component by list index."""
        del self.components[index]

    def clear_components(self) -> None:
        """Remove all components."""
        self.components.clear()

    def to_bytes(self, *, use_extended: bool = False) -> bytes:
        """Serialise this multi record to raw bytes.

        Parameters
        ----------
        use_extended:
            Write 16-byte entries (with ``unk1``) instead of classic 12-byte.
        """
        parts: List[bytes] = []
        for c in self.components:
            base = struct.pack(
                "<Hhhhi",
                c.item_id & 0xFFFF,
                c.x,
                c.y,
                c.z,
                c.flags,
            )
            if use_extended:
                base += struct.pack("<i", c.unk1 if c.unk1 is not None else 0)
            parts.append(base)
        return b"".join(parts)


class Multis:
    """Static class for managing multi data."""

    _multis: Dict[int, MultiData] = {}
    _index: Optional[FileIndex] = None
    _initialized = False

    # ------------------------------------------------------------------
    # Init / load
    # ------------------------------------------------------------------

    @classmethod
    def initialize(
        cls, idx_path: str | None = None, mul_path: str | None = None
    ) -> bool:
        if cls._initialized:
            if idx_path is None and mul_path is None:
                return True
            if (
                cls._index
                and idx_path == cls._index.idx_path
                and mul_path == cls._index.mul_path
            ):
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
        from .verdata_ids import IDS as VERDATA_IDS

        cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.MULTI_MUL)
        cls._multis = {}

    # ------------------------------------------------------------------
    # Decode heuristic
    # ------------------------------------------------------------------

    @staticmethod
    def _score_decoding(components: List[MultiComponent]) -> int:
        score = 0
        sample = components[:64]
        for c in sample:
            if -128 <= c.x <= 127 and -128 <= c.y <= 127 and -128 <= c.z <= 127:
                score += 2
            else:
                score -= 6
            if -60 <= c.x <= 60 and -60 <= c.y <= 60:
                score += 1
            if 0 < c.item_id <= 0xFFFF:
                score += 1
            else:
                score -= 2
        if 1 <= len(components) <= 50000:
            score += 2
        else:
            score -= 5
        return score

    @classmethod
    def _decode_components(cls, data: bytes) -> List[MultiComponent]:
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
                comps.append(
                    MultiComponent(
                        item_id=item_id, x=x, y=y, z=z, flags=flags, unk1=unk1
                    )
                )
            score = cls._score_decoding(comps)
            if best_score is None or score > best_score:
                best_score = score
                best_components = comps

        return best_components or []

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @classmethod
    def get_multi(cls, multi_id: int) -> Optional[MultiData]:
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

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @classmethod
    def save(
        cls,
        mul_path: str | None = None,
        idx_path: str | None = None,
        *,
        use_extended: bool = False,
    ) -> None:
        """Write all cached multi records back to disk.

        Records modified in memory are re-encoded; records that were never
        loaded are copied verbatim from the source index.

        Parameters
        ----------
        mul_path / idx_path:
            Output paths. Default to the original files via
            :class:`~ultima_sdk.files.Files`.
        use_extended:
            Write 16-byte (extended) component records instead of classic
            12-byte ones.
        """
        if not cls._initialized:
            cls.initialize()

        if mul_path is None:
            mul_path = Files.get_file_path("multi.mul")
        if idx_path is None:
            idx_path = Files.get_file_path("multi.idx")
        if not mul_path or not idx_path:
            raise FileAccessException("No multi.mul / multi.idx path available")
        if not cls._index:
            raise FileAccessException("Multi index not loaded")

        total = cls._index.entry_count

        mul_buf = bytearray()
        idx_entries: List[tuple[int, int, int]] = []

        for i in range(total):
            multi = cls._multis.get(i)
            record = (
                multi.to_bytes(use_extended=use_extended)
                if multi is not None
                else (cls._index.read_raw(i) or b"")
            )

            if record:
                offset = len(mul_buf)
                idx_entries.append((offset, len(record), 0))
                mul_buf += record
            else:
                idx_entries.append((0xFFFFFFFF, 0, 0))

        with open(mul_path, "wb") as f:
            f.write(mul_buf)

        with open(idx_path, "wb") as f:
            for offset, length, extra in idx_entries:
                f.write(struct.pack("<III", offset, length, extra))
