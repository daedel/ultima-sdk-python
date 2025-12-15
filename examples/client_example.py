"""Client example (Windows-only).

Checks whether the Ultima Online client window is detected.
If it's running, tries to bring it to front.
"""

from __future__ import annotations

from ultima_sdk.client import Client


def main() -> int:
    running = Client.is_running()
    print("Client running:", running)
    if not running:
        print("Start the UO client first if you want to test window interaction.")
        return 0

    ok = Client.bring_to_top()
    print("bring_to_top:", ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
