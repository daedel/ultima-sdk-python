"""verdata_ids constants example."""

from __future__ import annotations

from ultima_sdk.verdata_ids import IDS


def main() -> int:
    print("Some verdata file ids:")
    print("  ART_MUL:", IDS.ART_MUL)
    print("  GUMPART_MUL:", IDS.GUMPART_MUL)
    print("  SOUND_MUL:", IDS.SOUND_MUL)
    print("  MAP0_MUL:", IDS.MAP0_MUL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
