"""
Skills module - Manages skill information and data.
"""

from typing import List, Optional, Dict
import struct

from .binary_extensions import BinaryReader
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException
from .verdata_ids import IDS as VERDATA_IDS


class SkillInfo:
    """Information about a skill."""

    def __init__(self, skill_id: int, name: str, button_id: int):
        self.skill_id = skill_id
        self.name = name
        self.button_id = button_id


class Skills:
    """Static class for managing skill data."""

    _skills: List[SkillInfo] = []
    _skill_map: Dict[str, SkillInfo] = {}
    _index: Optional[FileIndex] = None
    _source_paths: tuple[str | None, str | None] = (None, None)
    _initialized = False

    @classmethod
    def initialize(
        cls, idx_path: str | None = None, mul_path: str | None = None
    ) -> bool:
        """Initialize skill data."""
        if cls._initialized:
            if idx_path is None and mul_path is None:
                return True
            if cls._source_paths == (idx_path, mul_path):
                return True

        try:
            cls._load_skills(idx_path=idx_path, mul_path=mul_path)
            cls._initialized = True
            return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize skills: {e}")

    @classmethod
    def _load_skills(
        cls, idx_path: str | None = None, mul_path: str | None = None
    ) -> None:
        """Load skill data from file."""
        cls._skills = []
        cls._skill_map = {}
        cls._index = None

        if idx_path is None:
            idx_path = Files.get_file_path("skills.idx")
        if mul_path is None:
            mul_path = Files.get_file_path("skills.mul")

        cls._source_paths = (idx_path, mul_path)

        if idx_path and mul_path:
            cls._index = FileIndex(idx_path, mul_path, file_id=VERDATA_IDS.SKILLS_MUL)
            cls._load_from_index()
            return

        if mul_path:
            # Best-effort: some distributions may ship only skills.mul.
            with open(mul_path, "rb") as f:
                data = f.read()
            cls._load_from_stream_bytes(data)

    @staticmethod
    def _decode_index_record(skill_id: int, data: bytes) -> SkillInfo:
        """Decode a single skills.mul indexed record.

        Real client formats vary across eras. We support a couple of common shapes
        and fall back to a forgiving parse.
        """
        if not data:
            raise ValueError("Empty skill record")

        def make(name: str, button_id: int) -> SkillInfo:
            name = name.strip("\x00").strip()
            if not name:
                name = f"Skill {skill_id}"
            return SkillInfo(skill_id=skill_id, name=name, button_id=button_id)

        # Format A: uint16 name_len, name bytes, int32 button_id
        if len(data) >= 2 + 4:
            name_len = struct.unpack_from("<H", data, 0)[0]
            if 0 < name_len <= len(data) - 6:
                if len(data) == 2 + name_len + 4:
                    name_bytes = data[2 : 2 + name_len]
                    button_id = struct.unpack_from("<i", data, 2 + name_len)[0]
                    if 0 <= button_id <= 0x7FFFFFFF:
                        return make(
                            name_bytes.decode("utf-8", errors="replace"), button_id
                        )

        # Format B: byte name_len, name bytes, int32 button_id
        if len(data) >= 1 + 4:
            name_len8 = data[0]
            if 0 < name_len8 <= len(data) - 5:
                if len(data) == 1 + name_len8 + 4:
                    name_bytes = data[1 : 1 + name_len8]
                    button_id = struct.unpack_from("<i", data, 1 + name_len8)[0]
                    if 0 <= button_id <= 0x7FFFFFFF:
                        return make(
                            name_bytes.decode("utf-8", errors="replace"), button_id
                        )

        # Format C: string (null-terminated) then int32 button_id.
        if len(data) >= 5:
            # Find first null within a reasonable range.
            nul = data.find(b"\x00")
            if 0 <= nul < len(data) - 4:
                # allow padding between string and button
                tail = data[-4:]
                button_id = struct.unpack("<i", tail)[0]
                if 0 <= button_id <= 0x7FFFFFFF:
                    name_bytes = data[:nul]
                    return make(name_bytes.decode("utf-8", errors="replace"), button_id)

        # Fallback: treat whole record as text and use skill_id as button.
        return make(data.decode("utf-8", errors="replace"), skill_id)

    @classmethod
    def _load_from_index(cls) -> None:
        if not cls._index:
            return

        # Pre-size the skills list to the full index length so callers can
        # request any in-range skill id even if the record is missing.
        cls._skills = [None] * len(cls._index.entries)  # type: ignore[list-item]
        cls._skill_map = {}

        # Read every entry in the index; missing entries return None.
        for skill_id in range(len(cls._index.entries)):
            raw = cls._index.read_raw(skill_id)
            if not raw:
                continue
            try:
                info = cls._decode_index_record(skill_id, raw)
            except Exception:
                continue
            cls._skills[skill_id] = info  # type: ignore[index]
            cls._skill_map[info.name.lower()] = info

        # Replace any None slots with placeholder SkillInfo objects.
        for i, v in enumerate(cls._skills):
            if v is None:  # type: ignore[comparison-overlap]
                placeholder = SkillInfo(skill_id=i, name=f"Skill {i}", button_id=i)
                cls._skills[i] = placeholder  # type: ignore[index]

    @classmethod
    def _load_from_stream_bytes(cls, data: bytes) -> None:
        """Best-effort skills.mul stream parsing (when no idx is available)."""
        reader = BinaryReader(data)
        cls._skills = []
        cls._skill_map = {}

        # Try: int32 count then records.
        try:
            count = reader.read_int32()
        except Exception:
            return

        # Reasonable skill counts are usually under a few hundred.
        if not (0 < count <= 500):
            return

        for skill_id in range(count):
            try:
                # Attempt: int32 button, uint16 name_len, name bytes
                button_id = reader.read_int32()
                name_len = reader.read_uint16()
                name_bytes = reader.read(name_len)
                if len(name_bytes) != name_len:
                    break
                name = (
                    name_bytes.decode("utf-8", errors="replace").strip("\x00").strip()
                )
                info = SkillInfo(skill_id=skill_id, name=name, button_id=button_id)
                cls._skills.append(info)
                cls._skill_map[info.name.lower()] = info
            except Exception:
                break

    @classmethod
    def get_skill(cls, skill_id: int) -> Optional[SkillInfo]:
        """Get skill by ID."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= skill_id < len(cls._skills):
            return cls._skills[skill_id]
        return None

    @classmethod
    def find_skill(cls, name: str) -> Optional[SkillInfo]:
        """Find skill by name."""
        if not cls._initialized:
            cls.initialize()

        return cls._skill_map.get(name.lower())
