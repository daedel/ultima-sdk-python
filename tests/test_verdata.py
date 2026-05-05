"""Tests for verdata.mul parsing and patch application."""

import struct

from ultima_sdk.file_index import FileIndex
from ultima_sdk.verdata import Verdata


def test_art_get_art_uses_verdata_patch(tmp_path):
    """Integration-level check: Art.get_art() returns verdata override bytes."""
    from ultima_sdk.files import Files
    from ultima_sdk.art import Art
    from ultima_sdk.verdata_ids import IDS as VERDATA_IDS

    # Create a minimal verdata.mul with a single patch for art.mul block 0.
    # Patch payload uses Art's supported "raw" fixture format:
    # uint16 width, uint16 height, then width*height*2 bytes UO16 pixels.
    width, height = 1, 1
    pixel_uo16 = 0x7FFF
    patch_bytes = struct.pack("<HHH", width, height, pixel_uo16)

    count = 1
    table_off = 4
    data_off = table_off + (count * 20)
    header = struct.pack("<i", count)
    entry = struct.pack(
        "<iiiii",
        VERDATA_IDS.ART_MUL,
        0,  # block_id
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
