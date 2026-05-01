"""Tests for light decoding via idx/mul bytes.

These tests do not require an installed Ultima Online client.
"""

from __future__ import annotations

import struct

from ultima_sdk.light import Light


def test_light_get_light_reads_idx_mul_uo16_square(tmp_path):
    # Create a 16x16 UO16 buffer (2 bytes per pixel).
    width = 16
    height = 16
    pixels = struct.pack("<" + "H" * (width * height), *([0x7FFF] * (width * height)))

    mul_path = tmp_path / "light.mul"
    mul_path.write_bytes(pixels)

    idx_path = tmp_path / "lightidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(pixels), 0))

    Light._initialized = False
    Light._index = None
    Light._lights = []
    assert Light.initialize(str(idx_path), str(mul_path)) is True

    light = Light.get_light(0)
    assert light is not None
    assert (light.width, light.height) == (width, height)
    assert len(light.pixels) == width * height * 2

    img = light.to_image()
    assert img.size == (width, height)


def test_light_get_light_reads_idx_mul_intensity_square(tmp_path):
    # Create a 8-bit 16x16 intensity buffer (1 byte per pixel).
    width = 16
    height = 16
    pixels = bytes([128] * (width * height))

    mul_path = tmp_path / "light.mul"
    mul_path.write_bytes(pixels)

    idx_path = tmp_path / "lightidx.mul"
    idx_path.write_bytes(struct.pack("<iii", 0, len(pixels), 0))

    Light._initialized = False
    Light._index = None
    Light._lights = []
    assert Light.initialize(str(idx_path), str(mul_path)) is True

    light = Light.get_light(0)
    assert light is not None
    assert (light.width, light.height) == (width, height)
    assert len(light.pixels) == width * height

    img = light.to_image()
    assert img.size == (width, height)
