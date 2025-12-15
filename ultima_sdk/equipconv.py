"""EquipConv module - loads and applies `equipconv.def`.

The Ultima SDK (C#) exposes these tables as static helpers; this module follows
that style.

We intentionally keep behavior conservative:
- If `equipconv.def` is missing/unreadable, conversion is a no-op.
- Supports global and per-body conversion rules (see `def_files.EquipConvDef`).
"""

from __future__ import annotations

from typing import Optional

from .def_files import EquipConvDef
from .files import Files


class EquipConv:
    """Static class for equipment conversion rules."""

    _initialized = False
    _table: Optional[EquipConvDef] = None

    @classmethod
    def initialize(cls, path: str | None = None) -> bool:
        if cls._initialized:
            return cls._table is not None

        cls._initialized = True
        cls._table = None

        if path is None:
            path = Files.get_file_path("equipconv.def")
        if not path:
            return False

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                cls._table = EquipConvDef.from_text(f.read())
            return True
        except Exception:
            cls._table = None
            return False

    @classmethod
    def try_convert(cls, item_id: int, *, body_id: int | None = None) -> Optional[int]:
        if not cls._initialized:
            cls.initialize()
        if cls._table is None:
            return None
        return cls._table.try_convert(int(item_id), body_id=body_id)

    @classmethod
    def convert(cls, item_id: int, *, body_id: int | None = None) -> int:
        if not cls._initialized:
            cls.initialize()
        if cls._table is None:
            return int(item_id)
        return cls._table.convert(int(item_id), body_id=body_id)

    @classmethod
    def _reset_for_tests(cls) -> None:
        cls._initialized = False
        cls._table = None
