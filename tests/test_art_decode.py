"""Tests for real Art decoding via idx/mul bytes.

These tests do not require an installed Ultima Online client.
"""

from __future__ import annotations

import struct

from ultima_sdk.art import Art


def test_art_get_art_reads_idx_mul(tmp_path):
    # Create a fake art.mul entry in the "raw" format we support:
    # uint16 width, uint16 height, then width*height*2 bytes of 16-bit pixels.
    width = 44
    height = 44
    pixels = b"\x00" * (width * height * 2)
    art_entry = struct.pack("<HH", width, height) + pixels

    mul_path = tmp_path / "art.mul"
    mul_path.write_bytes(art_entry)

    # Create a fake artidx.mul with one entry pointing at offset 0.
    # artidx uses int32 offset/length/extra.
    idx_path = tmp_path / "artidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(art_entry), 0))

    # Force initialize with our temp paths
    Art._initialized = False
    Art._index = None
    assert Art.initialize(str(idx_path), str(mul_path)) is True

    art = Art.get_art(0)
    assert art is not None
    assert art.width == width
    assert art.height == height
    assert len(art.pixels) == width * height * 2

    # Rendering helper should produce an image
    img = art.to_image()
    assert img.size == (width, height)
