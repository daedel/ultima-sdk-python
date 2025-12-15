import struct

from ultima_sdk.multis import Multis


def _write_idx_mul(tmp_path, record_bytes: bytes):
    idx_path = tmp_path / "multi.idx"
    mul_path = tmp_path / "multi.mul"

    mul_path.write_bytes(record_bytes)

    # Two entries: entry 0 points to offset 0, entry 1 missing.
    idx_bytes = b"".join(
        [
            struct.pack("<iii", 0, len(record_bytes), 0),
            struct.pack("<iii", -1, -1, 0),
        ]
    )
    idx_path.write_bytes(idx_bytes)

    return str(idx_path), str(mul_path)


def test_multis_decode_classic_12b_entries(tmp_path):
    # 2 classic entries => 24 bytes total (not divisible by 16)
    rec = b"".join(
        [
            struct.pack("<HhhhI", 0x1234, 1, 2, 3, 0x10),
            struct.pack("<HhhhI", 0x2000, -1, 0, 5, 0x20),
        ]
    )

    idx_path, mul_path = _write_idx_mul(tmp_path, rec)
    assert Multis.initialize(idx_path=idx_path, mul_path=mul_path) is True

    multi = Multis.get_multi(0)
    assert multi is not None
    assert multi.multi_id == 0
    assert len(multi.components) == 2
    assert multi.components[0].item_id == 0x1234
    assert (multi.components[0].x, multi.components[0].y, multi.components[0].z) == (1, 2, 3)
    assert multi.components[0].flags == 0x10
    assert multi.components[0].unk1 is None


def test_multis_decode_new_16b_entries(tmp_path):
    # 2 new-format entries => 32 bytes total (not divisible by 12)
    rec = b"".join(
        [
            struct.pack("<HhhhII", 0x0100, 0, 0, 0, 0x01, 0x11111111),
            struct.pack("<HhhhII", 0x0101, 5, -5, 7, 0x02, 0x22222222),
        ]
    )

    idx_path, mul_path = _write_idx_mul(tmp_path, rec)
    assert Multis.initialize(idx_path=idx_path, mul_path=mul_path) is True

    multi = Multis.get_multi(0)
    assert multi is not None
    assert len(multi.components) == 2
    assert multi.components[1].item_id == 0x0101
    assert multi.components[1].flags == 0x02
    assert multi.components[1].unk1 == 0x22222222


def test_multis_ambiguous_length_prefers_correct_layout(tmp_path):
    # 4 classic entries => 48 bytes (divisible by both 12 and 16).
    # If decoded as 16-byte entries we'd only get 3 entries and misaligned fields.
    rec = b"".join(
        [
            struct.pack("<HhhhI", 0x1000, 1, 1, 0, 0),
            struct.pack("<HhhhI", 0x1001, 2, 0, 0, 0),
            struct.pack("<HhhhI", 0x1002, 0, 2, 0, 0),
            struct.pack("<HhhhI", 0x1003, -2, -2, 0, 0),
        ]
    )

    idx_path, mul_path = _write_idx_mul(tmp_path, rec)
    assert Multis.initialize(idx_path=idx_path, mul_path=mul_path) is True

    multi = Multis.get_multi(0)
    assert multi is not None
    assert len(multi.components) == 4
    assert [c.item_id for c in multi.components] == [0x1000, 0x1001, 0x1002, 0x1003]
