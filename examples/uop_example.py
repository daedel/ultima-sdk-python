"""UOP example.

Builds a tiny synthetic UOP with one stored (uncompressed) entry and reads it back.
"""

from __future__ import annotations

import argparse
import struct
import tempfile
from pathlib import Path

from ultima_sdk.uop import UopFile, create_hash


def _format_virtual_name(pattern: str, entry_id: int) -> str:
    # The SDK accepts C#-style patterns like "{0:D8}".
    # For this tiny example, implement just the common D8/D6 substitutions.
    return (
        pattern
        .replace("{0:D8}", f"{int(entry_id):08d}")
        .replace("{0:D6}", f"{int(entry_id):06d}")
        .replace("{0}", str(int(entry_id)))
    )


def _build_uop_single_entry(pattern: str, entry_id: int, payload: bytes) -> bytes:
    """Build a minimal UOP with a single stored (uncompressed) entry."""
    header_size = 28
    block_offset = header_size

    # Block header: int32 filesCount, int64 nextBlock
    files_count = 1
    next_block = 0

    # Entry record is 34 bytes.
    entry_record_size = 34
    entry_record_offset = block_offset + 12
    data_offset = entry_record_offset + entry_record_size

    comp_len = len(payload)
    decomp_len = len(payload)

    virtual_name = _format_virtual_name(pattern, entry_id)
    h = create_hash(virtual_name)

    # UOP header fields (matches ultima_sdk.uop.UopFile.parse)
    magic = 0x50594D
    version = 4
    ts = 0
    next_block_ptr = block_offset
    block_size = 0
    count = 1

    out = bytearray()
    out += struct.pack("<IIIqIi", magic, version, ts, next_block_ptr, block_size, count)
    out += struct.pack("<Iq", files_count, next_block)

    entry_offset = data_offset
    header_len = 0
    data_hash = 0
    flag = 0

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

    out += payload
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", type=int, default=0)
    args = parser.parse_args()

    pattern = "build/example/{0:D8}.dat"
    payload = b"Hello UOP!"

    uop_bytes = _build_uop_single_entry(pattern, int(args.id), payload)

    with tempfile.TemporaryDirectory() as td:
        uop_path = Path(td) / "example.uop"
        uop_path.write_bytes(uop_bytes)
        u = UopFile(str(uop_path), pattern)
        raw = u.read_raw(int(args.id))
        print(f"read_raw({args.id}) -> {raw!r}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
