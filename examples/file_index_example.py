"""FileIndex example with a synthetic idx/mul pair.

Builds a tiny file pair in a temporary directory and reads back raw bytes.
"""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from ultima_sdk.file_index import FileIndex


def main() -> int:
    payload = b"Hello from mul!"

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        mul_path = temp_dir / "example.mul"
        idx_path = temp_dir / "example.idx"

        mul_path.write_bytes(payload)
        idx_path.write_bytes(struct.pack("<iii", 0, len(payload), 0))

        index = FileIndex(str(idx_path), str(mul_path))
        raw = index.read_raw(0)
        print(f"read_raw(0): {raw!r}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
