"""Sound example.

Fetches a sound and writes it as a WAV file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.sound import Sound

from ._common import (
    add_out_arg,
    add_uo_root_arg,
    ensure_out_dir,
    init_files,
    resolve_uo_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    parser.add_argument("--id", type=int, default=0, help="Sound id (default: 0)")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Sound.initialize()
    s = Sound.get_sound(int(args.id))
    if s is None:
        print("Sound not found")
        return 1

    name = s.name or f"sound_{int(args.id):05d}.wav"
    if not name.lower().endswith(".wav"):
        name += ".wav"
    out_path = Path(out_dir) / name
    out_path.write_bytes(s.data)
    print(f"Wrote {out_path} ({len(s.data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
