"""Optional smoke tests against a real Ultima Online client install.

These tests are skipped unless `UO_ROOT` (or `ULTIMA_ONLINE_DIR`) is set and
required files exist. They help validate that our decoders match real client
file formats (not just synthetic fixtures).
"""

from __future__ import annotations

import os

import pytest

from ultima_sdk.files import Files
from ultima_sdk.gumps import Gumps
from ultima_sdk.light import Light
from ultima_sdk.sound import Sound
from ultima_sdk.textures import Textures


def _uo_root() -> str | None:
    return os.environ.get("UO_ROOT") or os.environ.get("ULTIMA_ONLINE_DIR")


@pytest.mark.skipif(_uo_root() is None, reason="Requires UO_ROOT/ULTIMA_ONLINE_DIR")
def test_smoke_gumps_can_decode_one_entry():
    root = _uo_root()
    assert root is not None

    Files.set_directory(root)

    idx = Files.get_file_path("gumpidx.mul")
    mul = Files.get_file_path("gumpart.mul")
    if not idx or not mul:
        pytest.skip("gumpidx.mul/gumpart.mul not found in UO_ROOT")

    # Reset state for deterministic behavior.
    Gumps._initialized = False
    Gumps._index = None
    assert Gumps.initialize(idx, mul) is True

    # Try a few ids; different installs can have gaps.
    for gump_id in (0, 1, 2, 10, 100):
        g = Gumps.get_gump(gump_id)
        if g is None:
            continue

        # Basic sanity checks (should not crash / produce nonsense dimensions)
        assert g.width > 0 and g.height > 0
        assert len(g.pixels) == g.width * g.height * 2

        # Rendering should work (Pillow is a dependency).
        img = g.to_image()
        assert img.size == (g.width, g.height)
        return

    pytest.skip("No decodable gump entries found in first few ids")


@pytest.mark.skipif(_uo_root() is None, reason="Requires UO_ROOT/ULTIMA_ONLINE_DIR")
def test_smoke_textures_can_decode_one_entry():
    root = _uo_root()
    assert root is not None

    Files.set_directory(root)

    idx = Files.get_file_path("texidx.mul")
    mul = Files.get_file_path("texmaps.mul")
    if not idx or not mul:
        pytest.skip("texidx.mul/texmaps.mul not found in UO_ROOT")

    Textures._initialized = False
    Textures._index = None
    assert Textures.initialize(idx, mul) is True

    for texture_id in (0, 1, 2, 10, 100):
        t = Textures.get_texture(texture_id)
        if t is None:
            continue

        assert t.width > 0 and t.height > 0
        assert len(t.pixels) == t.width * t.height * 2

        img = t.to_image()
        assert img.size == (t.width, t.height)
        return

    pytest.skip("No decodable texture entries found in first few ids")


@pytest.mark.skipif(_uo_root() is None, reason="Requires UO_ROOT/ULTIMA_ONLINE_DIR")
def test_smoke_sound_can_decode_one_entry():
    root = _uo_root()
    assert root is not None

    Files.set_directory(root)

    idx = Files.get_file_path("soundidx.mul")
    mul = Files.get_file_path("sound.mul")
    if not idx or not mul:
        pytest.skip("soundidx.mul/sound.mul not found in UO_ROOT")

    Sound._initialized = False
    Sound._index = None
    assert Sound.initialize(idx, mul) is True

    for sound_id in (0, 1, 2, 10, 100):
        try:
            s = Sound.get_sound(sound_id)
        except Exception:
            # Some ids may not be valid / may not be WAV in certain installs.
            continue

        if s is None:
            continue

        assert s.data[:4] == b"RIFF"
        assert s.data[8:12] == b"WAVE"
        return

    pytest.skip("No decodable WAV sound entries found in first few ids")


@pytest.mark.skipif(_uo_root() is None, reason="Requires UO_ROOT/ULTIMA_ONLINE_DIR")
def test_smoke_light_can_decode_one_entry():
    root = _uo_root()
    assert root is not None

    Files.set_directory(root)

    idx = Files.get_file_path("lightidx.mul")
    mul = Files.get_file_path("light.mul")
    if not idx or not mul:
        pytest.skip("lightidx.mul/light.mul not found in UO_ROOT")

    Light._initialized = False
    Light._index = None
    Light._lights = []
    assert Light.initialize(idx, mul) is True

    for light_id in (0, 1, 2, 10, 100):
        try:
            light = Light.get_light(light_id)
        except Exception:
            continue
        if light is None:
            continue
        assert light.width > 0 and light.height > 0
        # Either 8-bit intensity or 16-bit pixels.
        assert len(light.pixels) in (light.width * light.height, light.width * light.height * 2)
        img = light.to_image()
        assert img.size == (light.width, light.height)
        return

    pytest.skip("No decodable light entries found in first few ids")
