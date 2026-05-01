"""
SkillGroups module - Manages skill grouping information.
"""

from typing import List, Optional

import struct

from .files import Files
from .exceptions import FileAccessException


class SkillGroup:
    """Represents a group of skills."""

    def __init__(self, group_id: int, name: str):
        self.group_id = group_id
        self.name = name
        self.skills: List[int] = []


class SkillGroups:
    """Static class for managing skill groups."""

    _groups: List[SkillGroup] = []
    _initialized = False

    @classmethod
    def initialize(cls, path: str | None = None) -> bool:
        """Initialize skill group data."""
        if cls._initialized:
            if path is None:
                return True

        try:
            if path is None:
                path = Files.get_file_path("skillgrp.mul")
            if path:
                cls._load_groups(path)
                cls._initialized = True
                return True
        except Exception as e:
            raise FileAccessException(f"Failed to initialize skill groups: {e}")

        return False

    @classmethod
    def _load_groups(cls, path: str) -> None:
        """Load skill group data."""
        with open(path, "rb") as f:
            data = f.read()

        cls._groups = cls._parse_skillgrp_bytes(data)

    @staticmethod
    def _parse_skillgrp_bytes(data: bytes) -> List[SkillGroup]:
        """Parse the `skillgrp.mul` file.

        Reference layout (as used by UOFiddler/Ultima SDK):
        - int32 count OR (int32 -1, int32 count) for Unicode mode
        - (count-1) fixed-width group name slots (17 bytes ASCII or 34 bytes UTF-16LE)
        - trailing int32 list (either per-skill group mapping or skill-id stream)
        """
        if len(data) < 4:
            return []

        header0 = struct.unpack_from("<i", data, 0)[0]
        unicode_mode = False
        count = header0
        start = 4
        str_len = 17

        if header0 == -1:
            if len(data) < 8:
                return []
            unicode_mode = True
            count = struct.unpack_from("<i", data, 4)[0]
            start = 8
            str_len = 34

        if count <= 0 or count > 512:
            return []

        groups: List[SkillGroup] = [SkillGroup(0, "Misc")]

        names_end = start + ((count - 1) * str_len)
        if names_end > len(data):
            return groups

        for i in range(count - 1):
            entry_off = start + (i * str_len)
            raw = data[entry_off : entry_off + str_len]
            if unicode_mode:
                chars: List[str] = []
                for j in range(0, len(raw), 2):
                    code_unit = raw[j] | (raw[j + 1] << 8)
                    if code_unit == 0:
                        break
                    chars.append(chr(code_unit))
                name = "".join(chars)
            else:
                nul = raw.find(b"\x00")
                if nul == -1:
                    nul = len(raw)
                name = raw[:nul].decode("ascii", errors="replace")

            groups.append(SkillGroup(i + 1, name))

        # Tail section: int32 list.
        tail: List[int] = []
        off = names_end
        while off + 4 <= len(data):
            tail.append(struct.unpack_from("<i", data, off)[0])
            off += 4

        if tail:
            # Heuristic A: per-skill group mapping
            if all(0 <= v < len(groups) for v in tail):
                for skill_id, group_id in enumerate(tail):
                    groups[group_id].skills.append(skill_id)
            else:
                # Heuristic B: skill-id stream with -1 separators
                group_idx = 0
                for v in tail:
                    if v == -1:
                        group_idx += 1
                        if group_idx >= len(groups):
                            break
                        continue
                    groups[group_idx].skills.append(v)

        return groups

    @classmethod
    def get_group(cls, group_id: int) -> Optional[SkillGroup]:
        """Get skill group by ID."""
        if not cls._initialized:
            cls.initialize()

        if 0 <= group_id < len(cls._groups):
            return cls._groups[group_id]
        return None
