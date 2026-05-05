"""Animations example.

Loads a creature animation and writes the first frame as an image.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.animations import Animations

from ._common import (
    add_out_arg,
    add_uo_root_arg,
    ensure_out_dir,
    init_files,
    resolve_uo_root,
    save_uo16_image,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    parser.add_argument("--body", type=int, default=1, help="Body id to load")
    parser.add_argument("--action", type=int, default=0, help="Action index")
    parser.add_argument("--direction", type=int, default=0, help="Direction index")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Animations.initialize()
    animation = Animations.get_animation(args.body, args.action, args.direction)
    if animation is None or not animation.frames:
        print("Animation not found")
        return 1

    frame = animation.frames[0]
    out_path = Path(out_dir) / f"animation_body{args.body}_action{args.action}_dir{args.direction}_frame0.png"
    saved = save_uo16_image(frame.width, frame.height, frame.pixels, out_path)
    print(f"Wrote {saved} ({frame.width}x{frame.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
