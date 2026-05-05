"""Skills example.

Loads skill definitions and looks up a few sample entries.
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
    for skill_id in [0, 1, 2, 10, 20, 30]:
        info = Skills.get_skill(skill_id)
        if info is not None:
            print(f"Skill[{skill_id}] name={info.name!r} button={info.button_id}")

    found = Skills.find_skill("magery")
    print(
        "Find 'magery':",
        getattr(found, "skill_id", None),
        getattr(found, "name", None),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
