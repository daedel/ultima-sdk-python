from __future__ import annotations

import os
import struct
from pathlib import Path

import pytest

from ultima_sdk.uop import UopFile


def _get_installed_uo_root() -> str | None:
    return (
        os.getenv("ULTIMA_ONLINE_DIR")
        or os.getenv("UO_ROOT")
        or os.getenv("ULTIMA_SDK_UO_ROOT")
    )


@pytest.mark.slow
def test_real_gumpart_uop_can_decode_one_entry():
    """Optional regression test against a real-world UOP file.

    Enable with:
      `ULTIMA_SDK_REAL_UOP_TESTS=1`

    This test is intentionally lightweight: it finds the first resolvable entry
    by ID and validates that the decoded payload begins with reasonable width/
    height (as used by gump decoding).
    """

    if os.getenv("ULTIMA_SDK_REAL_UOP_TESTS") != "1":
        pytest.skip("Set ULTIMA_SDK_REAL_UOP_TESTS=1 to enable real UOP tests")

    root = _get_installed_uo_root()
    if not root:
        pytest.skip(
            "Set UO_ROOT (or ULTIMA_ONLINE_DIR) to your installed client directory"
        )

    p = Path(root) / "gumpartlegacymul.uop"
    if not p.exists():
        pytest.skip("gumpartlegacymul.uop not found under UO_ROOT")

    pattern = "build/gumpartlegacymul/{0:D8}.tga"
    u = UopFile(str(p), pattern, has_extra=True)

    entry_id = None
    for i in range(20000):
        if u.get_entry(i) is not None:
            entry_id = i
            break

    assert entry_id is not None, "No entries found by ID lookup in first 20k IDs"

    raw = u.read_raw(entry_id)
    assert raw is not None and len(raw) >= 8

    width, height = struct.unpack_from("<II", raw, 0)
    assert 0 < width < 4096
    assert 0 < height < 4096
