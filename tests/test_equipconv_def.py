from ultima_sdk.equipconv import EquipConv
from ultima_sdk.files import Files


def test_equipconv_global_mapping(tmp_path):
    (tmp_path / "equipconv.def").write_text(
        "# global mapping\n0x2006 0x3000\n",
        encoding="utf-8",
    )

    Files.set_directory(str(tmp_path))
    EquipConv._reset_for_tests()

    assert EquipConv.initialize() is True
    assert EquipConv.convert(0x2006) == 0x3000
    assert EquipConv.convert(0x1234) == 0x1234


def test_equipconv_per_body_overrides_global(tmp_path):
    (tmp_path / "equipconv.def").write_text(
        "# body-specific mapping wins\n"
        "0x2006 0x3000\n"
        "400 0x2006 0x4000\n",
        encoding="utf-8",
    )

    Files.set_directory(str(tmp_path))
    EquipConv._reset_for_tests()

    assert EquipConv.initialize() is True

    assert EquipConv.convert(0x2006) == 0x3000
    assert EquipConv.convert(0x2006, body_id=400) == 0x4000
    assert EquipConv.convert(0x2006, body_id=401) == 0x3000


def test_equipconv_missing_file_is_noop(tmp_path):
    Files.set_directory(str(tmp_path))
    EquipConv._reset_for_tests()

    assert EquipConv.initialize() is False
    assert EquipConv.convert(0x2006) == 0x2006
    assert EquipConv.try_convert(0x2006) is None
