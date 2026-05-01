import struct

from ultima_sdk.files import Files
from ultima_sdk.map import Map


def _build_single_block_map(
    tile_overrides: dict[tuple[int, int], tuple[int, int]],
) -> bytes:
    # One 8x8 block => 196 bytes
    out = bytearray(struct.pack("<i", 0))  # block header
    for y in range(8):
        for x in range(8):
            tile_id, z = tile_overrides.get((x, y), (0, 0))
            out += struct.pack("<Hb", tile_id, z)
    assert len(out) == 196
    return bytes(out)


def test_map_reads_land_tile_from_single_block_file(tmp_path):
    d = tmp_path
    (d / "map0.mul").write_bytes(_build_single_block_map({(3, 5): (0x1234, -7)}))

    Files.set_directory(str(d))
    assert Map.initialize() is True

    m = Map.get_map(0)
    assert m is not None

    tile = m.get_tile(3, 5)
    assert tile == (0x1234, -7)

    assert m.get_tile(7, 7) == (0, 0)
    assert m.get_tile(8, 0) is None
