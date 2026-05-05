"""Sound example.

Loads a sound entry and writes it to a WAV file.
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
    parser.add_argument("--id", type=int, default=0, help="Sound id")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Sound.initialize()
    sound = Sound.get_sound(args.id)
    if sound is None:
        print(f"Sound id {args.id} not found")
        return 1

    name = sound.name or f"sound_{args.id:05d}.wav"
    if not name.lower().endswith(".wav"):
        name += ".wav"

    out_path = Path(out_dir) / name
    out_path.write_bytes(sound.data)
    print(f"Wrote {out_path} ({len(sound.data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
