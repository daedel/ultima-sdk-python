"""Body converter and body table readers.

Parses ``Bodyconv.def`` and ``Body.def`` from the UO client data
directory and provides body-ID translation utilities used by the
animation system.

Ported from NerdyGamers/UOPython (bodies.py) with adaptations:
  - Uses ``Files.get_file_path`` instead of a settings shim
  - No auto-execute on import
  - Type annotations throughout
  - ``get_true_body`` reverse-lookup preserved
"""
from __future__ import annotations

from typing import Optional

from ultima_sdk.files import Files


def _safe_get(lst: list[int], index: int, default: int = -1) -> int:
    try:
        return lst[index]
    except IndexError:
        return default


class BodyConverter:
    """Maps body IDs across the four anim file sets via ``Bodyconv.def``.

    Tables 1-4 correspond to anim2.mul/uop through anim5.mul/uop.
    """

    _loaded: bool = False
    _TABLE_1: list[int] = []
    _TABLE_2: list[int] = []
    _TABLE_3: list[int] = []
    _TABLE_4: list[int] = []

    @classmethod
    def load(cls) -> None:
        """Parse ``Bodyconv.def`` and populate the four translation tables."""
        path = Files.get_file_path("Bodyconv.def")
        max1 = max2 = max3 = max4 = 0
        list1: list[int] = []
        list2: list[int] = []
        list3: list[int] = []
        list4: list[int] = []

        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                fields = line.split()
                try:
                    orig  = int(fields[0]) if len(fields) > 0 else -1
                    anim2 = int(fields[1]) if len(fields) > 1 else -1
                    anim3 = int(fields[2]) if len(fields) > 2 else -1
                    anim4 = int(fields[3]) if len(fields) > 3 else -1
                    anim5 = int(fields[4]) if len(fields) > 4 else -1
                except (ValueError, IndexError):
                    continue

                if anim2 >= 0:
                    anim2 = 122 if anim2 == 68 else anim2
                    max1 = max(max1, orig)
                    list1 += [orig, anim2]
                if anim3 >= 0:
                    max2 = max(max2, orig)
                    list2 += [orig, anim3]
                if anim4 >= 0:
                    max3 = max(max3, orig)
                    list3 += [orig, anim4]
                if anim5 >= 0:
                    max4 = max(max4, orig)
                    list4 += [orig, anim5]

        cls._TABLE_1 = [-1] * (max1 + 1)
        cls._TABLE_2 = [-1] * (max2 + 1)
        cls._TABLE_3 = [-1] * (max3 + 1)
        cls._TABLE_4 = [-1] * (max4 + 1)

        for i in range(0, len(list1), 2):
            cls._TABLE_1[list1[i]] = list1[i + 1]
        for i in range(0, len(list2), 2):
            cls._TABLE_2[list2[i]] = list2[i + 1]
        for i in range(0, len(list3), 2):
            cls._TABLE_3[list3[i]] = list3[i + 1]
        for i in range(0, len(list4), 2):
            cls._TABLE_4[list4[i]] = list4[i + 1]

        cls._loaded = True

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._loaded:
            cls.load()

    @classmethod
    def contains(cls, body: int) -> bool:
        """Return ``True`` if *body* appears in any conversion table."""
        cls._ensure_loaded()
        if body < 0:
            return False
        for tbl in (cls._TABLE_1, cls._TABLE_2, cls._TABLE_3, cls._TABLE_4):
            if _safe_get(tbl, body) >= 0:
                return True
        return False

    @classmethod
    def convert(cls, body: int) -> tuple[int, int]:
        """Return ``(new_body_id, file_index)`` for *body*.

        ``file_index`` is 1-based (1 = anim.mul, 2 = anim2.mul, …).
        Falls back to ``(body, 1)`` when no mapping exists.
        """
        cls._ensure_loaded()
        if body < 0:
            return body, 1
        for idx, tbl in enumerate(
            (cls._TABLE_1, cls._TABLE_2, cls._TABLE_3, cls._TABLE_4), start=2
        ):
            new_body = _safe_get(tbl, body)
            if new_body != -1:
                return new_body, idx
        return body, 1

    @classmethod
    def get_true_body(cls, file_type: int, index: int) -> int:
        """Reverse-lookup: given a *file_type* (1-5) and body *index*,
        return the original body ID, or ``-1`` if not found.
        """
        cls._ensure_loaded()
        if file_type < 1 or file_type > 5 or index < 0:
            return -1
        if file_type == 1:
            return index
        tbl = (cls._TABLE_1, cls._TABLE_2, cls._TABLE_3, cls._TABLE_4)[file_type - 2]
        try:
            return tbl.index(index)
        except ValueError:
            return -1


# ---------------------------------------------------------------------------


class BodyTableEntry:
    """A single entry from ``Body.def``."""

    __slots__ = ("old_id", "new_id", "new_hue")

    def __init__(self, old_id: int, new_id: int, new_hue: int) -> None:
        self.old_id = old_id
        self.new_id = new_id
        self.new_hue = new_hue

    def __repr__(self) -> str:  # pragma: no cover
        return f"BodyTableEntry(old={self.old_id}, new={self.new_id}, hue={self.new_hue})"


class BodyTable:
    """Hue-replacement table parsed from ``Body.def``."""

    _entries: dict[int, BodyTableEntry] = {}
    _loaded: bool = False

    @classmethod
    def load(cls) -> None:
        """Parse ``Body.def`` and populate the entries dict."""
        path = Files.get_file_path("Body.def")
        cls._entries.clear()
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    i1 = line.index("{")
                    i2 = line.index("}")
                    param1 = line[:i1].strip()
                    param2 = line[i1 + 1:i2].strip()
                    param3 = line[i2 + 1:].strip()
                    if "," in param2:
                        param2 = param2[:param2.index(",")].strip()
                    orig_id = int(param1)
                    repl_id = int(param2)
                    hue     = int(param3)
                    cls._entries[orig_id] = BodyTableEntry(orig_id, repl_id, hue)
                except (ValueError, IndexError):
                    continue
        cls._loaded = True

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._loaded:
            cls.load()

    @classmethod
    def get(cls, body_id: int) -> Optional[BodyTableEntry]:
        """Return the ``BodyTableEntry`` for *body_id*, or ``None``."""
        cls._ensure_loaded()
        return cls._entries.get(body_id)

    @classmethod
    def contains(cls, body_id: int) -> bool:
        cls._ensure_loaded()
        return body_id in cls._entries

    @classmethod
    def all_entries(cls) -> dict[int, BodyTableEntry]:
        cls._ensure_loaded()
        return dict(cls._entries)
