"""Tests for verdata.mul parsing and patch application."""
import struct

from ultima_sdk.file_index import FileIndex
from ultima_sdk.verdata import Verdata


def test_art_get_art_uses_verdata_patch(tmp_path):
    """Integration-level check: Art.get_art() returns verdata override bytes."""
    from ultima_sdk.files import Files
    from ultima_sdk.art import Art
    from ultima_sdk.verdata_ids import IDS as VERDATA_IDS

    # Patch payload in MUL static art format:
    # 4-byte ignored header, uint16 width, uint16 height,
    # height*uint16 lookup table, then RLE rows (x_offset, run, pixels..., 0,0 sentinel).
    width, height = 1, 1
    pixel_uo16 = 0x7FFF
    mul_header = b'\x00' * 4
    wh = struct.pack("<HH", width, height)
    lookup = struct.pack("<H", 0)  # row 0 starts at pixel_data offset 0
    rle_row = struct.pack("<HH", 0, width) + struct.pack(f"<{width}H", pixel_uo16) + struct.pack("<HH", 0, 0)

    patch_bytes = mul_header + wh + lookup + rle_row
    count = 1
    table_off = 4
    data_off = table_off + (count * 20)
    header = struct.pack("<i", count)
    entry = struct.pack(
        "<iiiii",
        VERDATA_IDS.ART_MUL,
        0x4000,  # block_id: first static art tile (0x4000 = static tile 0)
        data_off,
        len(patch_bytes),
        0,
    )
    (tmp_path / "verdata.mul").write_bytes(header + entry + patch_bytes)

    # Create dummy artidx/art files so Art.initialize() can build its FileIndex.
    # The idx entry is missing (-1), so without verdata the read would return None.
    (tmp_path / "artidx.mul").write_bytes(struct.pack("<iii", -1, -1, -1))
    (tmp_path / "art.mul").write_bytes(b"")

    # Ensure all singletons are in a clean state.
    Files.set_directory(str(tmp_path))
    Verdata._initialized = False
    Verdata._entries = {}
    Verdata._path = None
    Art._initialized = False
    Art._index = None
    Art._patch_cache = {}

    # Initialize Art so it can find artidx.mul/art.mul.
    Art.initialize(
        idx_path=str(tmp_path / "artidx.mul"),
        mul_path=str(tmp_path / "art.mul"),
    )

    # Initialize Verdata and apply patches so Art._patch_cache is populated.
    Verdata.initialize(str(tmp_path / "verdata.mul"))
    Verdata.apply()

    art = Art.get_art(16384)
    assert art is not None
    assert art.width == 1
    assert art.height == 1


def test_verdata_reads_patch_bytes(tmp_path):
    patch_bytes = b"\x01\x02\x03\x04"
    file_id = 99
    block_id = 5

    count = 1
    table_off = 4
    data_off = table_off + (count * 20)

    header = struct.pack("<i", count)
    entry = struct.pack("<iiiii", file_id, block_id, data_off, len(patch_bytes), 0)
    blob = header + entry + patch_bytes

    path = tmp_path / "verdata.mul"
    path.write_bytes(blob)

    # Fresh init
    Verdata._initialized = False
    Verdata._entries = {}
    Verdata._path = None

    assert Verdata.initialize(str(path)) is True
    assert Verdata.has_patch(file_id, block_id) is True
    assert Verdata.read_patch(file_id, block_id) == patch_bytes


def test_fileindex_read_raw_uses_verdata_patch(tmp_path):
    patch_bytes = b"patched"
    file_id = 123
    block_id = 7

    count = 1
    table_off = 4
    data_off = table_off + (count * 20)

    header = struct.pack("<i", count)
    entry = struct.pack("<iiiii", file_id, block_id, data_off, len(patch_bytes), 0)
    blob = header + entry + patch_bytes

    path = tmp_path / "verdata.mul"
    path.write_bytes(blob)

    Verdata._initialized = False
    Verdata._entries = {}
    Verdata._path = None
    Verdata.initialize(str(path))

    # No idx/mul needed: verdata patch should be returned before idx lookup.
    fi = FileIndex(file_id=file_id)
    assert fi.read_raw(block_id) == patch_bytes
