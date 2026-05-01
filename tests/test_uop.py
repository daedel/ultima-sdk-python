from __future__ import annotations

import struct
import zlib


from ultima_sdk.uop import UopBackedIndex, UopFile, create_hash


def _build_uop_single_entry(*, pattern: str, entry_id: int, payload: bytes, flag: int = 0, has_extra: bool = False) -> bytes:
    """Build a minimal UOP with a single entry.

    This is a synthetic fixture to validate parsing + hash lookup.
    """
    # Header is 28 bytes.
    header_size = 28
    block_offset = header_size

    # Block header: int32 filesCount, int64 nextBlock
    files_count = 1
    next_block = 0

    # Entry record is 34 bytes.
    entry_record_size = 34
    entry_record_offset = block_offset + 12

    # Data will start after block header + entry record.
    data_offset = entry_record_offset + entry_record_size

    extra_bytes = b""
    if has_extra:
        extra_bytes = struct.pack("<ii", 123, 456)

    stored_payload = extra_bytes + payload

    # For this fixture we keep everything uncompressed.
    comp_len = len(stored_payload)
    decomp_len = len(stored_payload) if flag != 1 else len(payload)

    virtual_name = pattern.replace("{0:D8}", f"{entry_id:08d}")
    virtual_name = virtual_name.replace("{0:D6}", f"{entry_id:06d}")
    h = create_hash(virtual_name)

    # UOP header fields.
    magic = 0x50594D
    version = 4
    ts = 0
    next_block_ptr = block_offset
    block_size = 0
    count = 1

    out = bytearray()
    out += struct.pack("<IIIqIi", magic, version, ts, next_block_ptr, block_size, count)
    out += struct.pack("<Iq", files_count, next_block)

    # Entry: offset points to the *header* start; header_len tells where data starts.
    # We set header_len=0 and offset=data_offset.
    entry_offset = data_offset
    header_len = 0
    data_hash = 0

    out += struct.pack(
        "<qiiiQIh",
        entry_offset,
        header_len,
        comp_len,
        decomp_len,
        h,
        data_hash,
        flag,
    )

    out += stored_payload
    return bytes(out)


def test_uop_hash_matches_self_consistency():
    # Basic smoke: stable, deterministic value.
    s = "build/artlegacymul/00000000.tga"
    h1 = create_hash(s)
    h2 = create_hash(s)
    assert h1 == h2
    assert isinstance(h1, int)
    assert 0 <= h1 < (1 << 64)


def test_uop_reads_raw_uncompressed(tmp_path):
    pattern = "build/artlegacymul/{0:D8}.tga"
    payload = b"HELLO_UOP"

    uop_bytes = _build_uop_single_entry(pattern=pattern, entry_id=5, payload=payload, has_extra=False)
    p = tmp_path / "artlegacymul.uop"
    p.write_bytes(uop_bytes)

    u = UopFile(str(p), pattern)
    assert u.read_raw(5) == payload
    assert u.read_raw(6) is None


def test_uop_has_extra_skips_prefix(tmp_path):
    pattern = "build/gumpartlegacymul/{0:D8}.tga"
    payload = b"PAYLOAD_AFTER_EXTRA"

    uop_bytes = _build_uop_single_entry(pattern=pattern, entry_id=0, payload=payload, has_extra=True)
    p = tmp_path / "gumpartlegacymul.uop"
    p.write_bytes(uop_bytes)

    idx = UopBackedIndex(str(p), pattern, has_extra=True)
    assert idx.read_raw(0) == payload


def test_uop_unsupported_bwt_flag_raises(tmp_path):
    pattern = "build/artlegacymul/{0:D8}.tga"

    # Build a tiny synthetic BWT buffer that decodes to b"A" * 4.
    # The BWT decoder consumes:
    # - 4 bytes header (unused)
    # - a MTF-coded stream, where the last code byte is a sentinel (no output)
    # The MTF output is then interpreted by the internal stage:
    # - first 1024 bytes: 256 int32 little-endian counts
    # - bytes after that: indices used by the decoder
    counts = [0] * 256
    counts[65] = 4  # 'A'
    mtf_target = bytearray(struct.pack("<256i", *counts))
    mtf_target += b"\x00\x00\x00\x00"  # setup + 3 indices, all zero

    # MTF-encode mtf_target into code bytes.
    table = list(range(256))
    codes = bytearray()
    for b in mtf_target:
        idx = table.index(b)
        codes.append(idx)
        if idx:
            table.pop(idx)
            table.insert(0, b)
    codes.append(0)  # sentinel

    bwt_buffer = b"\x00\x00\x00\x00" + bytes(codes)
    compressed = zlib.compress(bwt_buffer)

    # Build a UOP containing the zlib-compressed BWT payload, flagged as 3.
    header_size = 28
    block_offset = header_size
    entry_record_size = 34
    entry_record_offset = block_offset + 12
    data_offset = entry_record_offset + entry_record_size

    comp_len = len(compressed)
    decomp_len = len(bwt_buffer)

    virtual_name = pattern.replace("{0:D8}", f"{0:08d}")
    h = create_hash(virtual_name)

    magic = 0x50594D
    version = 4
    ts = 0
    next_block_ptr = block_offset
    block_size = 0
    count = 1

    out = bytearray()
    out += struct.pack("<IIIqIi", magic, version, ts, next_block_ptr, block_size, count)
    out += struct.pack("<Iq", 1, 0)
    out += struct.pack(
        "<qiiiQIh",
        data_offset,
        0,
        comp_len,
        decomp_len,
        h,
        0,
        3,
    )
    out += compressed

    p = tmp_path / "bwt.uop"
    p.write_bytes(bytes(out))

    u = UopFile(str(p), pattern)
    assert u.read_raw(0) == b"A" * 4
