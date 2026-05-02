"""Skills module - Manages skill information and data."""

from typing import List, Optional, Dict
import struct

from .binary_extensions import BinaryReader
from .file_index import FileIndex
from .files import Files
from .exceptions import FileAccessException
from .verdata_ids import IDS as VERDATA_IDS


class SkillInfo:
    """Information about a skill."""

    def __init__(
        self,
        skill_id: int,
        name: str,
        button_id: int,
        action: int = 0,
        icon_id: int = 0,
    ):
        self.skill_id = skill_id
        self.name = name
        self.button_id = button_id
        self.action = action
        self.icon_id = icon_id


class Skills:
    """Static class for managing skill data.

    Supported formats:
    1. Vanilla fixed-width skills.mul stream:
       35 bytes per entry:
         uint16 skill_id
         uint8  action
         uint16 icon_id
         char[30] name

    2. Indexed / ServUO-style records:
       - uint16 name_len + name + int32 button_id
       - uint8  name_len + name + int32 button_id
       - null-terminated string + trailing int32 button_id
    """

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
            with open(mul_path, "rb") as f:
                data = f.read()
            cls._load_from_stream_bytes(data)

    @staticmethod
    def _make_skill(
        skill_id: int,
        name: str,
        button_id: int,
        action: int = 0,
        icon_id: int = 0,
    ) -> SkillInfo:
        name = name.strip("\x00").strip()
        if not name:
            name = f"Skill {skill_id}"
        return SkillInfo(
            skill_id=skill_id,
            name=name,
            button_id=button_id,
            action=action,
            icon_id=icon_id,
        )

    @staticmethod
    def _decode_index_record(skill_id: int, data: bytes) -> SkillInfo:
        """Decode a single indexed skill record.

        Supports several practical record layouts used by custom tooling.
        """
        if not data:
            raise ValueError("Empty skill record")

        # Format A: uint16 name_len, name bytes, int32 button_id
        if len(data) >= 6:
            name_len = struct.unpack_from("<H", data, 0)[0]
            if 0 < name_len <= len(data) - 6 and len(data) == 2 + name_len + 4:
                name_bytes = data[2 : 2 + name_len]
                button_id = struct.unpack_from("<i", data, 2 + name_len)[0]
                if 0 <= button_id <= 0x7FFFFFFF:
                    return Skills._make_skill(
                        skill_id,
                        name_bytes.decode("utf-8", errors="replace"),
                        button_id,
                    )

        # Format B: uint8 name_len, name bytes, int32 button_id
        if len(data) >= 5:
            name_len8 = data[0]
            if 0 < name_len8 <= len(data) - 5 and len(data) == 1 + name_len8 + 4:
                name_bytes = data[1 : 1 + name_len8]
                button_id = struct.unpack_from("<i", data, 1 + name_len8)[0]
                if 0 <= button_id <= 0x7FFFFFFF:
                    return Skills._make_skill(
                        skill_id,
                        name_bytes.decode("utf-8", errors="replace"),
                        button_id,
                    )

        # Format C: null-terminated string then trailing int32 button_id
        if len(data) >= 5:
            nul = data.find(b"\x00")
            if 0 <= nul < len(data) - 4:
                button_id = struct.unpack("<i", data[-4:])[0]
                if 0 <= button_id <= 0x7FFFFFFF:
                    return Skills._make_skill(
                        skill_id,
                        data[:nul].decode("utf-8", errors="replace"),
                        button_id,
                    )

        # Fallback: treat whole record as text
        return Skills._make_skill(
            skill_id,
            data.decode("utf-8", errors="replace"),
            skill_id,
        )

    @classmethod
    def _load_from_index(cls) -> None:
        """Load from idx/mul pair.

        This path is treated as custom/indexed data, not vanilla fixed-35-byte skills.mul.
        """
        if not cls._index:
            return

        cls._skills = [None] * len(cls._index.entries)  # type: ignore[list-item]
        cls._skill_map = {}

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

        for i, v in enumerate(cls._skills):
            if v is None:  # type: ignore[comparison-overlap]
                placeholder = SkillInfo(
                    skill_id=i,
                    name=f"Skill {i}",
                    button_id=i,
                )
                cls._skills[i] = placeholder  # type: ignore[index]

    @staticmethod
    def _looks_like_vanilla_fixed_stream(data: bytes) -> bool:
        """Check whether data matches classic 35-byte fixed records."""
        entry_size = 35
        if not data or len(data) % entry_size != 0:
            return False

        count = len(data) // entry_size
        if count <= 0 or count > 500:
            return False

        plausible = 0
        for i in range(min(count, 8)):
            off = i * entry_size
            skill_id, action, icon_id = struct.unpack_from("<HBH", data, off)
            name_bytes = data[off + 5 : off + 35]
            name = (
                name_bytes.split(b"\x00", 1)[0]
                .decode("latin-1", errors="ignore")
                .strip()
            )

            if skill_id < 1000 and action < 32 and len(name) > 0:
                plausible += 1

        return plausible >= max(1, min(count, 3))

    @classmethod
    def _load_vanilla_fixed_stream(cls, data: bytes) -> None:
        """Load classic fixed 35-byte skills.mul entries."""
        entry_size = 35
        count = len(data) // entry_size

        cls._skills = []
        cls._skill_map = {}

        for i in range(count):
            off = i * entry_size
            skill_id, action, icon_id = struct.unpack_from("<HBH", data, off)
            name_bytes = data[off + 5 : off + 35]
            name = (
                name_bytes.split(b"\x00", 1)[0]
                .decode("latin-1", errors="replace")
                .strip()
            )

            # Prefer stored skill_id if sane, otherwise use ordinal position.
            resolved_skill_id = skill_id if 0 <= skill_id < 0xFFFF else i

            info = cls._make_skill(
                resolved_skill_id,
                name,
                button_id=icon_id,
                action=action,
                icon_id=icon_id,
            )

            # Keep list indexed by ordinal stream position for predictable access.
            while len(cls._skills) <= i:
                cls._skills.append(
                    SkillInfo(
                        skill_id=len(cls._skills),
                        name=f"Skill {len(cls._skills)}",
                        button_id=len(cls._skills),
                    )
                )

            cls._skills[i] = info
            cls._skill_map[info.name.lower()] = info

    @classmethod
    def _load_from_stream_bytes(cls, data: bytes) -> None:
        """Load skills.mul when no idx is available.

        Prefers classic vanilla 35-byte fixed-width parsing when detected,
        otherwise falls back to the previous best-effort custom stream parser.
        """
        cls._skills = []
        cls._skill_map = {}

        if not data:
            return

        # First: classic vanilla fixed-width format
        if cls._looks_like_vanilla_fixed_stream(data):
            cls._load_vanilla_fixed_stream(data)
            return

        # Fallback: custom stream format
        reader = BinaryReader(data)

        try:
            count = reader.read_int32()
        except Exception:
            return

        if not (0 < count <= 500):
            return

        for skill_id in range(count):
            try:
                button_id = reader.read_int32()
                name_len = reader.read_uint16()
                name_bytes = reader.read(name_len)
                if len(name_bytes) != name_len:
                    break
                name = (
                    name_bytes.decode("utf-8", errors="replace").strip("\x00").strip()
                )
                info = cls._make_skill(skill_id, name, button_id)
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
