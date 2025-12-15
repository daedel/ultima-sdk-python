"""Tests for animations decoding.

Uses a tiny synthetic anim.idx/anim.mul fixture.
"""

import struct

from ultima_sdk.animations import Animations
from ultima_sdk.files import Files


def _build_single_frame_anim_entry() -> bytes:
    """Build one animation entry with one 1x1 frame.

    Format matches `Animations._decode_animation_entry`:
    - i32 frame_count
    - i32 offsets[frame_count]
    - frame:
      h center_x, h center_y, h width, h height
      i32 line_offsets[height]
      line RLE: (h x_off, h run_len, u16*run_len) ... (0,0)
    """
    center_x = 0
    center_y = 0
    width = 1
    height = 1

    # Frame body
    frame_header = struct.pack("<hhhh", center_x, center_y, width, height)

    # For 1 line, RLE data starts after header (8) + line table (4)
    line_offset = 8 + 4
    line_table = struct.pack("<i", line_offset)

    # One run at x=0, len=1, pixel=0x7FFF, then terminator (0,0)
    rle = struct.pack("<hhHhh", 0, 1, 0x7FFF, 0, 0)

    frame = frame_header + line_table + rle

    # Entry header: 1 frame, offset points to frame start
    frame_offset = 4 + 4  # after count + offsets array
    header = struct.pack("<ii", 1, frame_offset)

    return header + frame


def test_get_animation_decodes_single_frame(tmp_path):
    anim_entry = _build_single_frame_anim_entry()

    (tmp_path / "anim.mul").write_bytes(anim_entry)
    (tmp_path / "anim.idx").write_bytes(struct.pack("<iii", 0, len(anim_entry), 0))

    Files.set_directory(str(tmp_path))

    # Reset Animations state (tests are independent)
    Animations._initialized = False
    Animations._index_sets = {}
    Animations._cache = {}

    assert Animations.initialize() is True

    anim = Animations.get_animation(body=0, action=0, direction=0)
    assert anim is not None
    assert anim.body_id == 0
    assert anim.action == 0
    assert anim.direction == 0
    assert len(anim.frames) == 1

    frame = anim.frames[0]
    assert frame.width == 1
    assert frame.height == 1
    assert frame.pixels == struct.pack("<H", 0x7FFF)


def test_get_animation_missing_files_returns_none(tmp_path):
    Files.set_directory(str(tmp_path))

    Animations._initialized = False
    Animations._index_sets = {}
    Animations._cache = {}

    # No anim files present
    assert Animations.initialize() is False
    assert Animations.get_animation(body=0, action=0, direction=0) is None
