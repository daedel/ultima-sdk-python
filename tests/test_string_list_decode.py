import struct

from ultima_sdk.files import Files
from ultima_sdk.string_list import StringList


def _build_cliloc_bytes(entries: dict[int, str], *, header_variant: str = "v2_lang") -> bytes:
    # Common header variants observed in clients:
    # - 6 bytes: int32 version + int16 language/unknown
    # - 4 bytes: int32 version
    # - 0 bytes: no header
    if header_variant == "v2_lang":
        out = bytearray(struct.pack("<ih", 2, 0))
    elif header_variant == "v2":
        out = bytearray(struct.pack("<i", 2))
    elif header_variant == "none":
        out = bytearray()
    else:
        raise ValueError("unknown header_variant")

    for entry_id, text in entries.items():
        payload = text.encode("utf-8")
        out += struct.pack("<iBH", entry_id, 0, len(payload))
        out += payload

    return bytes(out)


def test_string_list_loads_cliloc_enu_from_files_dir(tmp_path):
    d = tmp_path
    (d / "cliloc.enu").write_bytes(_build_cliloc_bytes({1000: "Hello", 1001: "World"}, header_variant="v2_lang"))

    Files.set_directory(str(d))
    assert StringList.initialize() is True

    assert StringList.get_string(1000) == "Hello"
    assert StringList.get_string(1001) == "World"
    assert StringList.get_string(9999) is None


def test_string_list_accepts_other_header_variants(tmp_path):
    p = tmp_path / "cliloc.custom1"
    p.write_bytes(_build_cliloc_bytes({42: "X"}, header_variant="v2"))

    assert StringList.initialize(file_path=str(p)) is True
    assert StringList.get_string(42) == "X"
