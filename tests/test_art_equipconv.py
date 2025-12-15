from __future__ import annotations

import struct

from ultima_sdk.art import Art
from ultima_sdk.equipconv import EquipConv
from ultima_sdk.files import Files


def _write_art_with_missing_0_present_1(tmp_path):
    # art entry in raw test format: u16 width/height + pixels
    width = 44
    height = 44
    pixels = b"\xAA\xBB" * (width * height)
    art_entry = struct.pack("<HH", width, height) + pixels

    mul_path = tmp_path / "art.mul"
    mul_path.write_bytes(art_entry)

    # idx: entry 0 missing (-1,0,0), entry 1 points to offset 0
    idx_path = tmp_path / "artidx.mul"
    idx_path.write_bytes(struct.pack("<iii", -1, 0, 0) + struct.pack("<iii", 0, len(art_entry), 0))

    Art._initialized = False
    Art._index = None
    assert Art.initialize(str(idx_path), str(mul_path)) is True


def test_get_equipped_art_applies_global_equipconv(tmp_path):
    _write_art_with_missing_0_present_1(tmp_path)

    (tmp_path / "equipconv.def").write_text("0 1\n", encoding="utf-8")
    Files.set_directory(str(tmp_path))
    EquipConv._reset_for_tests()

    assert Art.get_art(0) is None

    art = Art.get_equipped_art(0)
    assert art is not None
    assert art.graphic_id == 1


def test_get_equipped_art_applies_body_specific_override(tmp_path):
    _write_art_with_missing_0_present_1(tmp_path)

    # global converts 0->1, but body 400 forces 0->0 (which is missing)
    (tmp_path / "equipconv.def").write_text("0 1\n400 0 0\n", encoding="utf-8")
    Files.set_directory(str(tmp_path))
    EquipConv._reset_for_tests()

    assert Art.get_equipped_art(0, body_id=401) is not None
    assert Art.get_equipped_art(0, body_id=400) is None
