"""Exceptions example.

Shows how to catch SDK exception types.
"""

from __future__ import annotations

from ultima_sdk.exceptions import FileAccessException, WaveFormatException


def main() -> int:
    try:
        raise FileAccessException("Example file access failure")
    except FileAccessException as exc:
        print(f"Caught FileAccessException: {exc}")

    try:
        raise WaveFormatException("Example invalid WAV data")
    except WaveFormatException as exc:
        print(f"Caught WaveFormatException: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
