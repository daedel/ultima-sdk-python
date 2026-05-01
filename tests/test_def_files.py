import struct

from ultima_sdk.animations import Animations
from ultima_sdk.files import Files


def _build_single_frame_anim_entry(pixel: int) -> bytes:
    center_x = 0
    center_y = 0
    width = 1
    height = 1

    frame_header = struct.pack("<hhhh", center_x, center_y, width, height)

    # For 1 line, RLE data starts after header (8) + line table (4)
    line_offset = 8 + 4
    line_table = struct.pack("<i", line_offset)

    rle = struct.pack("<hhHhh", 0, 1, pixel & 0xFFFF, 0, 0)

    frame = frame_header + line_table + rle

    frame_offset = 4 + 4
    header = struct.pack("<ii", 1, frame_offset)

    return header + frame


def _write_single_entry_idx_mul(tmp_path, base: str, entry: bytes) -> None:
    (tmp_path / f"{base}.mul").write_bytes(entry)
    (tmp_path / f"{base}.idx").write_bytes(struct.pack("<iii", 0, len(entry), 0))


def _reset_animations_state() -> None:
    Animations._initialized = False
    Animations._index_sets = {}
    Animations._cache = {}
    Animations._body_conv = None
    Animations._body_def = None


def test_bodyconv_def_selects_anim2_set(tmp_path):
    # anim and anim2 both exist with different pixel values; bodyconv.def forces anim2.
    _write_single_entry_idx_mul(
        tmp_path, "anim", _build_single_frame_anim_entry(0x1111)
    )
    _write_single_entry_idx_mul(
        tmp_path, "anim2", _build_single_frame_anim_entry(0x2222)
    )

    (tmp_path / "bodyconv.def").write_text("0\t0\t-1\t-1\t-1\n", encoding="utf-8")

    Files.set_directory(str(tmp_path))
    _reset_animations_state()
    assert Animations.initialize() is True

    anim = Animations.get_animation(body=0, action=0, direction=0)
    assert anim is not None
    assert anim.frames[0].pixels == struct.pack("<H", 0x2222)


def test_body_def_translates_requested_body(tmp_path):
    # Requesting body=5 translates to body=0, letting us keep a tiny idx fixture.
    _write_single_entry_idx_mul(
        tmp_path, "anim", _build_single_frame_anim_entry(0x7FFF)
    )

    (tmp_path / "body.def").write_text("5 { 0 }\n", encoding="utf-8")

    Files.set_directory(str(tmp_path))
    _reset_animations_state()
    assert Animations.initialize() is True

    anim = Animations.get_animation(body=5, action=0, direction=0)
    assert anim is not None
    assert anim.body_id == 5
    assert anim.frames[0].pixels == struct.pack("<H", 0x7FFF)
