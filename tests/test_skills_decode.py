import struct

from ultima_sdk.skills import Skills


def _make_indexed_record(name: str, button_id: int) -> bytes:
    name_bytes = name.encode("utf-8")
    return struct.pack("<H", len(name_bytes)) + name_bytes + struct.pack("<i", button_id)


def test_skills_loads_from_idx_mul(tmp_path):
    # Build skills.mul with two records at different offsets.
    rec0 = _make_indexed_record("Alchemy", 100)
    rec1 = _make_indexed_record("Magery", 200)

    mul = rec0 + rec1
    mul_path = tmp_path / "skills.mul"
    mul_path.write_bytes(mul)

    # skills.idx entries are (int32 offset, int32 length, int32 extra)
    idx_path = tmp_path / "skills.idx"
    idx_bytes = b"".join(
        [
            struct.pack("<iii", 0, len(rec0), 0),
            struct.pack("<iii", len(rec0), len(rec1), 0),
            struct.pack("<iii", -1, -1, 0),
        ]
    )
    idx_path.write_bytes(idx_bytes)

    assert Skills.initialize(idx_path=str(idx_path), mul_path=str(mul_path)) is True

    s0 = Skills.get_skill(0)
    assert s0 is not None
    assert s0.name == "Alchemy"
    assert s0.button_id == 100

    s1 = Skills.find_skill("magery")
    assert s1 is not None
    assert s1.skill_id == 1
    assert s1.button_id == 200

    # Missing entry should be None (out of range) or placeholder if in range.
    s2 = Skills.get_skill(2)
    assert s2 is not None
    assert s2.skill_id == 2
