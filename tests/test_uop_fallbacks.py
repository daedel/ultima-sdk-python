from __future__ import annotations

import struct

from ultima_sdk.art import Art
from ultima_sdk.gumps import Gumps
from ultima_sdk.sound import Sound
from ultima_sdk.uop import create_hash


def _build_uop_single_entry(*, pattern: str, entry_id: int, payload: bytes, has_extra: bool = False) -> bytes:
    header_size = 28
    block_offset = header_size

    files_count = 1
    next_block = 0

    entry_record_size = 34
    entry_record_offset = block_offset + 12
    data_offset = entry_record_offset + entry_record_size

    extra_bytes = b""
    if has_extra:
        extra_bytes = struct.pack("<ii", 11, 22)

    stored_payload = extra_bytes + payload

    comp_len = len(stored_payload)
    decomp_len = len(stored_payload)

    virtual_name = pattern.replace("{0:D8}", f"{entry_id:08d}")
    virtual_name = virtual_name.replace("{0:D6}", f"{entry_id:06d}")
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
    out += stored_payload
    return bytes(out)


def test_art_initialize_uses_uop_fallback(tmp_path, monkeypatch):
    # Minimal raw art tile (supported by Art._decode_static_art test format)
    w, h = 2, 2
    pixels = b"\x01\x00" * (w * h)
    art_payload = struct.pack("<HH", w, h) + pixels

    uop_path = tmp_path / "artlegacymul.uop"
    uop_path.write_bytes(
        _build_uop_single_entry(
            pattern="build/artlegacymul/{0:D8}.tga",
            entry_id=1,
            payload=art_payload,
        )
    )

    # Force Files.get_file_path lookups.
    def fake_get_file_path(name: str):
        name = name.lower()
        if name == "artlegacymul.uop":
            return str(uop_path)
        if name in ("artidx.mul", "art.mul"):
            return None
        return None

    monkeypatch.setattr("ultima_sdk.art.Files.get_file_path", fake_get_file_path)

    Art._initialized = False
    Art._index = None
    assert Art.initialize() is True

    tile = Art.get_art(1)
    assert tile is not None
    assert tile.width == w and tile.height == h


def test_gumps_initialize_uses_uop_fallback(tmp_path, monkeypatch):
    # Raw test format for gumps: uint16 w/h + pixels
    w, h = 2, 1
    pixels = b"\x02\x00" * (w * h)
    gump_payload = struct.pack("<HH", w, h) + pixels

    uop_path = tmp_path / "gumpartlegacymul.uop"
    uop_path.write_bytes(
        _build_uop_single_entry(
            pattern="build/gumpartlegacymul/{0:D8}.tga",
            entry_id=0,
            payload=gump_payload,
            has_extra=True,
        )
    )

    def fake_get_file_path(name: str):
        name = name.lower()
        if name == "gumpartlegacymul.uop":
            return str(uop_path)
        if name in ("gumpidx.mul", "gumpart.mul"):
            return None
        return None

    monkeypatch.setattr("ultima_sdk.gumps.Files.get_file_path", fake_get_file_path)

    Gumps._initialized = False
    Gumps._index = None
    assert Gumps.initialize() is True

    g = Gumps.get_gump(0)
    assert g is not None
    assert g.width == w and g.height == h


def test_sound_initialize_uses_uop_fallback(tmp_path, monkeypatch):
    # Minimal RIFF/WAVE file (same style as tests/test_sound_decode.py)
    fmt_chunk = (
        b"fmt "
        + struct.pack("<I", 16)
        + struct.pack("<HHIIHH", 1, 1, 8000, 8000 * 2, 2, 16)
    )
    data_chunk = b"data" + struct.pack("<I", 2) + b"\x00\x00"
    riff_payload = b"WAVE" + fmt_chunk + data_chunk
    wav = b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload

    uop_path = tmp_path / "soundlegacymul.uop"
    uop_path.write_bytes(
        _build_uop_single_entry(
            pattern="build/soundlegacymul/{0:D8}.dat",
            entry_id=0,
            payload=wav,
        )
    )

    def fake_get_file_path(name: str):
        name = name.lower()
        if name == "soundlegacymul.uop":
            return str(uop_path)
        if name in ("soundidx.mul", "sound.mul"):
            return None
        return None

    monkeypatch.setattr("ultima_sdk.sound.Files.get_file_path", fake_get_file_path)

    Sound._initialized = False
    Sound._index = None
    assert Sound.initialize() is True

    s = Sound.get_sound(0)
    assert s is not None
    assert s.data[:4] == b"RIFF"
    assert s.data[8:12] == b"WAVE"
