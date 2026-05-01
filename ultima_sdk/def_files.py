"""Parsers for Ultima Online .def text tables.

These files are shipped with the client and provide translation tables that
influence how resources are resolved.

We keep parsing intentionally tolerant:
- ignore blank lines and comments
- accept whitespace or tab separation where applicable
- accept missing optional columns/fields
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


def _strip_comment(line: str) -> str:
    # UO .def files commonly use '#' for comments.
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()


def _parse_int(token: str) -> int:
    token = token.strip()
    if not token:
        raise ValueError("empty int")

    # Some community files use '$' for hex.
    if token.startswith("$"):
        token = "0x" + token[1:]

    # Stop at common separators.
    for sep in [",", ";"]:
        if sep in token:
            token = token.split(sep, 1)[0].strip()

    return int(token, 0)


@dataclass(frozen=True)
class BodyConvResult:
    file_type: int
    body: int


class BodyConvDef:
    """Parser for `bodyconv.def`.

    Format (typical): tab-separated columns
        original    anim2   anim3   anim4   anim5

    Missing values are treated as -1.
    If a mapping exists for a given body, the first matching anim-set column
    (anim2..anim5) determines the file set.

    file_type mapping:
      1 -> anim.mul
      2 -> anim2.mul
      3 -> anim3.mul
      4 -> anim4.mul
      5 -> anim5.mul
    """

    def __init__(self) -> None:
        self._table2: Dict[int, int] = {}
        self._table3: Dict[int, int] = {}
        self._table4: Dict[int, int] = {}
        self._table5: Dict[int, int] = {}

    @classmethod
    def from_text(cls, text: str) -> "BodyConvDef":
        inst = cls()
        inst._load_text(text)
        return inst

    def _load_text(self, text: str) -> None:
        for raw_line in text.splitlines():
            line = _strip_comment(raw_line)
            if not line:
                continue

            # Spec is tab-separated, but many files contain mixed whitespace.
            parts = [p for p in line.replace("\t", " ").split(" ") if p]
            if not parts:
                continue

            try:
                original = _parse_int(parts[0])
            except Exception:
                continue

            def _col(i: int) -> int:
                try:
                    return _parse_int(parts[i])
                except Exception:
                    return -1

            a2 = _col(1)
            a3 = _col(2)
            a4 = _col(3)
            a5 = _col(4)

            if a2 != -1:
                self._table2[original] = a2
            if a3 != -1:
                self._table3[original] = a3
            if a4 != -1:
                self._table4[original] = a4
            if a5 != -1:
                self._table5[original] = a5

    def resolve(self, body: int) -> BodyConvResult:
        if body in self._table2:
            return BodyConvResult(file_type=2, body=self._table2[body])
        if body in self._table3:
            return BodyConvResult(file_type=3, body=self._table3[body])
        if body in self._table4:
            return BodyConvResult(file_type=4, body=self._table4[body])
        if body in self._table5:
            return BodyConvResult(file_type=5, body=self._table5[body])
        return BodyConvResult(file_type=1, body=body)


class BodyDef:
    """Parser for `body.def`.

    The client uses this table to translate requested body IDs.

    Common format examples (varies by shard/tools):
      5 { 0 }
      400 { 0 } 0
      10 { 20, 0, 0 }

    We parse only the body-id translation reliably and tolerate extra fields.
    """

    def __init__(self) -> None:
        self._map: Dict[int, int] = {}

    @classmethod
    def from_text(cls, text: str) -> "BodyDef":
        inst = cls()
        inst._load_text(text)
        return inst

    def _load_text(self, text: str) -> None:
        for raw_line in text.splitlines():
            line = _strip_comment(raw_line)
            if not line:
                continue

            # Brace form: NEW { OLD, ... } ...
            if "{" in line and "}" in line:
                try:
                    left, rest = line.split("{", 1)
                    inside, _after = rest.split("}", 1)
                    new_id = _parse_int(left.strip().split()[0])
                    inside = inside.strip()
                    if not inside:
                        continue
                    old_id = _parse_int(inside)
                    self._map[new_id] = old_id
                except Exception:
                    continue
                continue

            # Fallback: just two ints on the line.
            parts = [p for p in line.replace("\t", " ").split(" ") if p]
            if len(parts) < 2:
                continue
            try:
                new_id = _parse_int(parts[0])
                old_id = _parse_int(parts[1])
                self._map[new_id] = old_id
            except Exception:
                continue

    def translate_body(self, body: int) -> int:
        return self._map.get(body, body)

    def try_translate_body(self, body: int) -> Optional[int]:
        return self._map.get(body)

    def translate_body_and_hue(
        self, body: int, hue: Optional[int]
    ) -> Tuple[int, Optional[int]]:
        # Hue rules vary by client; we only guarantee body translation.
        return (self.translate_body(body), hue)


class EquipConvDef:
    """Parser for `equipconv.def`.

    This file provides item-id conversion rules used by clients to adjust
    equipped/paperdoll item art across body types and client generations.

    The format is not fully standardized across all shards/tools; we support the
    two most common patterns:

    - Global mapping (2 columns):
        old_item_id  new_item_id
    - Per-body mapping (3 columns):
        body_id  old_item_id  new_item_id

    Comments (`# ...`) and blank lines are ignored.
    Extra tokens on a line are ignored.
    """

    def __init__(self) -> None:
        self._global: Dict[int, int] = {}
        self._by_body: Dict[int, Dict[int, int]] = {}

    @classmethod
    def from_text(cls, text: str) -> "EquipConvDef":
        inst = cls()
        inst._load_text(text)
        return inst

    def _load_text(self, text: str) -> None:
        for raw_line in text.splitlines():
            line = _strip_comment(raw_line)
            if not line:
                continue

            parts = [p for p in line.replace("\t", " ").split(" ") if p]
            if len(parts) < 2:
                continue

            # Prefer 3-column form when present.
            if len(parts) >= 3:
                try:
                    body_id = _parse_int(parts[0])
                    old_id = _parse_int(parts[1])
                    new_id = _parse_int(parts[2])
                except Exception:
                    continue
                self._by_body.setdefault(body_id, {})[old_id] = new_id
                continue

            try:
                old_id = _parse_int(parts[0])
                new_id = _parse_int(parts[1])
            except Exception:
                continue
            self._global[old_id] = new_id

    def try_convert(
        self, item_id: int, *, body_id: Optional[int] = None
    ) -> Optional[int]:
        if body_id is not None:
            m = self._by_body.get(int(body_id))
            if m is not None and int(item_id) in m:
                return int(m[int(item_id)])
        if int(item_id) in self._global:
            return int(self._global[int(item_id)])
        return None

    def convert(self, item_id: int, *, body_id: Optional[int] = None) -> int:
        mapped = self.try_convert(item_id, body_id=body_id)
        return int(item_id) if mapped is None else int(mapped)
