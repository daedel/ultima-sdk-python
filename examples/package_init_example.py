"""Package __init__.py example.

Demonstrates package-level exports and version metadata.
"""

from __future__ import annotations

import ultima_sdk
from ultima_sdk.files import Files


def main() -> int:
    print("ultima_sdk.__version__:", getattr(ultima_sdk, "__version__", None))
    print("Exports include Files:", hasattr(ultima_sdk, "Files"))

    try:
        Files.initialize()
    except Exception:
        pass

    print("Files directory:", Files.get_directory())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
