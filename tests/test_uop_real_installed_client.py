from __future__ import annotations

import os

import pytest

from ultima_sdk.art import Art
from ultima_sdk.files import Files
from ultima_sdk.map import Map
from ultima_sdk.sound import Sound


def _get_installed_uo_root() -> str | None:
    # Prefer the same env vars used by Files.initialize(), but allow explicit override.
    return (
        os.getenv("ULTIMA_ONLINE_DIR")
        or os.getenv("UO_ROOT")
        or os.getenv("ULTIMA_SDK_UO_ROOT")
    )


def _require_real_installed_client() -> str:
    if os.getenv("ULTIMA_SDK_REAL_UOP_TESTS") != "1":
        pytest.skip("Set ULTIMA_SDK_REAL_UOP_TESTS=1 to enable real installed-client tests")

    root = _get_installed_uo_root()
    if not root:
        pytest.skip("Set UO_ROOT (or ULTIMA_ONLINE_DIR) to your installed client directory")

    if not os.path.isdir(root):
        pytest.skip("UO_ROOT directory does not exist")

    return root


@pytest.mark.slow
def test_installed_art_legacy_uop_static_art_decodes():
    root = _require_real_installed_client()

    Files.set_directory(root)
    Art.initialize()

    # Static art lives at >= 0x4000. Try a small range to find a decodable tile.
    decoded = False
    for art_id in range(0x4000, 0x4020):
        try:
            art = Art.get_art(art_id)
            if art is None:
                continue
            img = art.to_image()
            assert img.size[0] > 0 and img.size[1] > 0
            decoded = True
            break
        except Exception:
            continue

    assert decoded, "Could not decode any static art in 0x4000..0x401F from installed client"


@pytest.mark.slow
def test_installed_map0_uop_can_read_tile():
    root = _require_real_installed_client()

    Files.set_directory(root)
    Map.initialize()

    m = Map.get_map(0)
    assert m is not None
    tile = m.get_tile(0, 0)

    # Tile should expose at least an id/graphic and elevation.
    assert tile is not None
    assert isinstance(tile, tuple)
    assert len(tile) == 2
    tile_id, z = tile
    assert isinstance(tile_id, int)
    assert isinstance(z, int)
    # Be permissive: different maps can have different ranges, but these should be sane.
    assert 0 <= tile_id <= 0x3FFF
    assert -128 <= z <= 127


@pytest.mark.slow
def test_installed_sound_legacy_uop_decodes_to_wav():
    root = _require_real_installed_client()

    Files.set_directory(root)
    Sound.initialize()

    s = Sound.get_sound(0)
    assert s is not None
    assert s.data[:4] == b"RIFF"
    assert s.data[8:12] == b"WAVE"
