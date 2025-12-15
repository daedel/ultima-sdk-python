"""Skills example.

Loads skills and prints a couple entries.
"""

from __future__ import annotations

import argparse

from ultima_sdk.skills import Skills

from ._common import add_uo_root_arg, init_files, resolve_uo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_uo_root_arg(parser)
    args = parser.parse_args()

    init_files(resolve_uo_root(args.uo_root), require=True)
    Skills.initialize()

    for i in [0, 1, 2, 10, 20, 30]:
        info = Skills.get_skill(i)
        if info:
            print(f"Skill[{i}] name={info.name!r} button={info.button_id}")

    find = Skills.find_skill("magery")
    print("Find 'magery':", getattr(find, "skill_id", None), getattr(find, "name", None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
