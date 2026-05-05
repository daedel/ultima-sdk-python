"""Animations GIF example.

Loads a creature animation and writes it as an animated GIF.
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
    parser.add_argument("--duration", type=int, default=100, help="Frame duration in ms")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Animations.initialize()
    out_path = Path(out_dir) / f"animation_body{args.body}_action{args.action}_dir{args.direction}.gif"

    try:
        ok = Animations.save_gif(
            args.body,
            args.action,
            args.direction,
            out_path,
            duration_ms=args.duration,
        )
        if not ok:
            print("Animation not found")
            return 1
        print(f"Wrote {out_path}")
        return 0
    except ImportError:
        animation = Animations.get_animation(args.body, args.action, args.direction)
        if animation is None or not animation.frames:
            print("Animation not found")
            return 1
        frame = animation.frames[0]
        ppm_path = out_path.with_suffix(".ppm")
        saved = save_uo16_image(frame.width, frame.height, frame.pixels, ppm_path)
        print(f"Pillow not installed; wrote first frame as {saved}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
