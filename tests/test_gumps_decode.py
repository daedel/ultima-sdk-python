"""Tests for gump decoding via idx/mul bytes.

These tests do not require an installed Ultima Online client.
"""

from __future__ import annotations

import struct

from ultima_sdk.gumps import Gumps


def test_gumps_get_gump_reads_idx_mul_raw_uo16(tmp_path):
    # Create a fake gumpart.mul entry in the simplified raw format supported:
    # uint16 width, uint16 height, then width*height*2 bytes of 16-bit pixels.
    width = 2
    height = 3

    # Non-zero pixels so `to_image()` produces non-empty output.
    pixels = struct.pack("<" + "H" * (width * height), *([0x7FFF] * (width * height)))
    entry = struct.pack("<HH", width, height) + pixels

    mul_path = tmp_path / "gumpart.mul"
    mul_path.write_bytes(entry)

    # gumpidx.mul uses int32 offset/length/extra.
    idx_path = tmp_path / "gumpidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(entry), 0))

    # Force initialize with our temp paths
    Gumps._initialized = False
    Gumps._index = None
    assert Gumps.initialize(str(idx_path), str(mul_path)) is True

    g = Gumps.get_gump(0)
    assert g is not None
    assert g.width == width
    assert g.height == height
    assert len(g.pixels) == width * height * 2

    img = g.to_image()
    assert img.size == (width, height)
