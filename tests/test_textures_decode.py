"""Tests for texture decoding via idx/mul bytes.

These tests do not require an installed Ultima Online client.
"""

from __future__ import annotations

import struct

from ultima_sdk.textures import Textures


def test_textures_get_texture_reads_idx_mul_64x64(tmp_path):
    # texmaps.mul entry is typically raw 16-bit pixels (no header)
    width = 64
    height = 64
    pixels = struct.pack("<" + "H" * (width * height), *([0x7FFF] * (width * height)))

    mul_path = tmp_path / "texmaps.mul"
    mul_path.write_bytes(pixels)

    idx_path = tmp_path / "texidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(pixels), 0))

    Textures._initialized = False
    Textures._index = None
    assert Textures.initialize(str(idx_path), str(mul_path)) is True

    t = Textures.get_texture(0)
    assert t is not None
    assert (t.width, t.height) == (width, height)
    assert len(t.pixels) == width * height * 2

    img = t.to_image()
    assert img.size == (width, height)
