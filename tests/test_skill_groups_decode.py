import struct

from ultima_sdk.skill_groups import SkillGroups


def _build_skillgrp_ascii(group_names: list[str], tail: list[int]) -> bytes:
    # group_names excludes the implicit "Misc" group.
    count = 1 + len(group_names)
    out = bytearray(struct.pack("<i", count))

    for name in group_names:
        buf = bytearray(17)
        b = name.encode("ascii", errors="replace")[:16]
        buf[: len(b)] = b
        buf[len(b)] = 0
        out += buf

    for v in tail:
        out += struct.pack("<i", v)

    return bytes(out)


def _build_skillgrp_unicode(group_names: list[str], tail: list[int]) -> bytes:
    count = 1 + len(group_names)
    out = bytearray(struct.pack("<ii", -1, count))

    for name in group_names:
        buf = bytearray(34)
        b = name.encode("utf-16le")[:32]
        buf[: len(b)] = b
        # nul terminator is already zeros in buffer
        out += buf

    for v in tail:
        out += struct.pack("<i", v)

    return bytes(out)


def test_skill_groups_ascii_parses_names_and_sentinel_skill_list(tmp_path):
    data = _build_skillgrp_ascii(
        ["Combat", "Magic"],
        # skill-id stream with -1 group separators
        [0, 1, -1, 10, -1, 20, 21],
    )
    p = tmp_path / "skillgrp.mul"
    p.write_bytes(data)

    assert SkillGroups.initialize(path=str(p)) is True

    g0 = SkillGroups.get_group(0)
    g1 = SkillGroups.get_group(1)
    g2 = SkillGroups.get_group(2)

    assert g0 is not None and g0.name == "Misc" and g0.skills == [0, 1]
    assert g1 is not None and g1.name == "Combat" and g1.skills == [10]
    assert g2 is not None and g2.name == "Magic" and g2.skills == [20, 21]


def test_skill_groups_unicode_parses_names_and_group_mapping_tail(tmp_path):
    data = _build_skillgrp_unicode(
        ["Craft", "Lore"],
        # per-skill group mapping: skill0->0(Misc), skill1->1(Craft), skill2->1, skill3->2
        [0, 1, 1, 2],
    )
    p = tmp_path / "skillgrp.mul"
    p.write_bytes(data)

    assert SkillGroups.initialize(path=str(p)) is True

    g0 = SkillGroups.get_group(0)
    g1 = SkillGroups.get_group(1)
    g2 = SkillGroups.get_group(2)
    assert g0 is not None and g1 is not None and g2 is not None

    assert g0.name == "Misc"
    assert g1.name == "Craft"
    assert g2.name == "Lore"

    assert g0.skills == [0]
    assert g1.skills == [1, 2]
    assert g2.skills == [3]
