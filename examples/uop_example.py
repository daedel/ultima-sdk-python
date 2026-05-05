"""UOP example.

Builds a minimal UOP container with one stored entry and reads it back.
"""

from __future__ import annotations

import argparse
import struct
import tempfile
from pathlib import Path

from ultima_sdk.uop import UopFile, create_hash


def _format_virtual_name(pattern: str, entry_id: int) -> str:
    return (
        pattern.replace("{0:D8}", f"{entry_id:08d}")
        .replace("{0:D6}", f"{entry_id:06d}")
        .replace("{0}", str(entry_id))
    )


def _build_uop_single_entry(pattern: str, entry_id: int, payload: bytes) -> bytes:
    magic = 0x50594D
    version = 4
    timestamp = 0
    next_block = 28
    block_size = 0
    file_count = 1

    virtual_name = _format_virtual_name(pattern, entry_id)
    hash_value = create_hash(virtual_name)
    header = struct.pack("<IIIqIi", magic, version, timestamp, next_block, block_size, file_count)
    block_header = struct.pack("<Iq", file_count, 0)

    entry_offset = next_block + 12 + 34
    record = struct.pack(
        "<QIIIQIH",
        entry_offset,
        0,
        len(payload),
        len(payload),
        hash_value,
        0,
        0,
    )

    return header + block_header + record + payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", type=int, default=0, help="Entry id")
    args = parser.parse_args()

    pattern = "build/example/{0:D8}.dat"
    payload = b"Hello UOP!"
    uop_bytes = _build_uop_single_entry(pattern, args.id, payload)

    with tempfile.TemporaryDirectory() as tmpdir:
        uop_path = Path(tmpdir) / "example.uop"
        uop_path.write_bytes(uop_bytes)

        archive = UopFile(str(uop_path), pattern)
        raw = archive.read_raw(args.id)
        print(f"read_raw({args.id}) -> {raw!r}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
