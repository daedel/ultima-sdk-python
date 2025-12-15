"""Exceptions example.

Demonstrates catching SDK exceptions.
"""

from __future__ import annotations

from ultima_sdk.exceptions import FileAccessException, WaveFormatException


def main() -> int:
    try:
        raise FileAccessException("Example failure")
    except FileAccessException as e:
        print("Caught FileAccessException:", e)

    try:
        raise WaveFormatException("Not a wave")
    except WaveFormatException as e:
        print("Caught WaveFormatException:", e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
