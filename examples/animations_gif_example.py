"""Animations + AnimationEdit example.

Fetches an animation and saves it as an animated GIF.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.animations import Animations

from ._common import add_out_arg, add_uo_root_arg, ensure_out_dir, init_files, resolve_uo_root, save_uo16_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    add_out_arg(parser)
    parser.add_argument("--body", type=int, default=1)
    parser.add_argument("--action", type=int, default=0)
    parser.add_argument("--direction", type=int, default=0)
    parser.add_argument("--duration", type=int, default=100)
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Animations.initialize()
    out_path = Path(out_dir) / f"anim_body{args.body}_act{args.action}_dir{args.direction}.gif"

    try:
        ok = Animations.save_gif(args.body, args.action, args.direction, out_path, duration_ms=args.duration)
        if not ok:
            print("Animation not found")
            return 1
        print(f"Wrote {out_path}")
        return 0
    except ImportError:
        # Pillow missing; fall back to dumping the first frame as PPM.
        anim = Animations.get_animation(args.body, args.action, args.direction)
        if anim is None or not anim.frames:
            print("Animation not found")
            return 1
        frame0 = anim.frames[0]
        ppm_path = out_path.with_suffix(".ppm")
        saved = save_uo16_image(frame0.width, frame0.height, frame0.pixels, ppm_path)
        print(f"Pillow not installed; wrote first frame to {saved}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
