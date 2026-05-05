"""Legacy example entry point.

This module is kept for backwards compatibility and delegates to files_example.
"""

from __future__ import annotations

from .files_example import main


if __name__ == "__main__":
    raise SystemExit(main())
