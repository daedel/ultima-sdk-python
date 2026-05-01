"""Legacy example (kept for backwards compatibility).

Prefer:
  python -m examples.files_example --uo-root "..."
"""

from __future__ import annotations

from .files_example import main

if __name__ == "__main__":
    raise SystemExit(main())
