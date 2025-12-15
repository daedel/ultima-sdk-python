"""animations.py example.

Fetches an animation and saves the first frame as PNG/PPM.

Run (needs client files + Pillow optional):
  python -m examples.animations_example --uo-root "C:\\Path\\To\\UO" --body 1 --action 0 --direction 0 --out out
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
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Animations.initialize()
    anim = Animations.get_animation(args.body, args.action, args.direction)
    if anim is None or not anim.frames:
        print("Animation not found")
        return 1

    print(f"Frames: {len(anim.frames)}")
    frame0 = anim.frames[0]
    out_path = Path(out_dir) / f"anim_body{args.body}_act{args.action}_dir{args.direction}_frame0.png"
    saved = save_uo16_image(frame0.width, frame0.height, frame0.pixels, out_path)
    print(f"Wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
