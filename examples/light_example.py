"""Light example.

Tries to decode a light resource and write it as PNG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultima_sdk.light import Light
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
    parser.add_argument("--id", type=int, default=0, help="Light id (default: 0)")
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    out_dir = ensure_out_dir(args.out)

    Light.initialize()

    candidates = [int(args.id)] + list(range(0, 128))

    for light_id in candidates:
        try:
            light = Light.get_light(light_id)
            if light is None:
                continue

            out_path = Path(out_dir) / f"light_{light_id:04d}.png"
            saved = save_uo16_image(light.width, light.height, light.pixels, out_path)
            print(f"Decoded light {light_id} -> {saved} ({light.width}x{light.height})")
            return 0
        except Exception:
            continue

    print("Could not decode any light in 0..127.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
