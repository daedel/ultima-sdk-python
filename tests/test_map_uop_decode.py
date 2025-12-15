import struct

from ultima_sdk.files import Files
from ultima_sdk.map import Map
from ultima_sdk.uop import create_hash


def _build_single_block_map(tile_overrides: dict[tuple[int, int], tuple[int, int]]) -> bytes:
    # One 8x8 block => 196 bytes
    out = bytearray(struct.pack("<i", 0))  # block header
    for y in range(8):
        for x in range(8):
            tile_id, z = tile_overrides.get((x, y), (0, 0))
            out += struct.pack("<Hb", tile_id, z)
    assert len(out) == 196
    return bytes(out)


def _build_uop_single_entry(*, pattern: str, entry_id: int, payload: bytes) -> bytes:
    header_size = 28
    block_offset = header_size

    files_count = 1
    next_block = 0

    entry_record_size = 34
    entry_record_offset = block_offset + 12
    data_offset = entry_record_offset + entry_record_size

    comp_len = len(payload)
    decomp_len = len(payload)

    virtual_name = pattern.replace("{0:D8}", f"{entry_id:08d}")
    h = create_hash(virtual_name)

    magic = 0x50594D
    version = 4
    ts = 0
    next_block_ptr = block_offset
    block_size = 0
    count = 1

    out = bytearray()
    out += struct.pack("<IIIqIi", magic, version, ts, next_block_ptr, block_size, count)
    out += struct.pack("<Iq", files_count, next_block)
    out += struct.pack("<qiiiQIh", data_offset, 0, comp_len, decomp_len, h, 0, 0)
    out += payload
    return bytes(out)


def test_map_reads_land_tile_from_single_block_uop(tmp_path):
    d = tmp_path

    pattern = "build/map0legacymul/{0:D8}.dat"
    (d / "map0legacymul.uop").write_bytes(
        _build_uop_single_entry(
            pattern=pattern,
            entry_id=0,
            payload=_build_single_block_map({(3, 5): (0x1234, -7)}),
        )
    )

    Files.set_directory(str(d))
    assert Map.initialize() is True

    m = Map.get_map(0)
    assert m is not None

    tile = m.get_tile(3, 5)
    assert tile == (0x1234, -7)

    assert m.get_tile(7, 7) == (0, 0)
    assert m.get_tile(8, 0) is None
