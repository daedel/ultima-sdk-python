"""SkillGroups example.

Loads skill groups and prints the group names.
"""

from __future__ import annotations

import argparse

from ultima_sdk.skill_groups import SkillGroups

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True, require_any=("skillgrp.mul",))
    SkillGroups.initialize()

    i = 0
    while True:
        g = SkillGroups.get_group(i)
        if g is None:
            break
        print(f"Group[{i}] {g.name!r} skills={len(g.skills)}")
        i += 1
        if i > 20:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
