"""Client example (Windows-only).

Shows how to detect the UO client window and bring it to the foreground.
"""

from __future__ import annotations

from ultima_sdk.client import Client


def main() -> int:
    running = Client.is_running()
    print(f"Client running: {running}")
    if not running:
        print("Start the Ultima Online client and rerun this example.")
        return 0

    ok = Client.bring_to_top()
    print(f"bring_to_top returned: {ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
