"""FileIndex example with a tiny synthetic idx/mul pair.

Run:
  python -m examples.file_index_example
"""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from ultima_sdk.file_index import FileIndex


def main() -> int:
    payload = b"Hello from mul!"

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        mul_path = td_path / "example.mul"
        idx_path = td_path / "example.idx"
        mul_path.write_bytes(payload)

        # On-disk .idx uses 3 x int32 per entry.
        idx_path.write_bytes(struct.pack("<iii", 0, len(payload), 0))

        idx = FileIndex(str(idx_path), str(mul_path))
        raw = idx.read_raw(0)
        print(f"read_raw(0): {raw!r}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
