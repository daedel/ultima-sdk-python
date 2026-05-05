"""SkillGroups example.

Loads skill groups and prints group names with their first skills.
"""

from __future__ import annotations

import argparse

from ultima_sdk.skill_groups import SkillGroups

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    init_files(
        resolve_uo_root(args.uo_root),
        require=True,
        require_any=("skillgrp.mul",),
    )

    SkillGroups.initialize()
    index = 0
    while True:
        group = SkillGroups.get_group(index)
        if group is None:
            break

        print(f"Group[{index}] {group.name!r} skills={len(group.skills)}")
        if group.skills:
            print(f"  first skills: {group.skills[:5]}")

        index += 1
        if index >= 20:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
