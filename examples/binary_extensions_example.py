"""BinaryReader/BinaryWriter example.

Demonstrates reading and writing primitive values with the SDK helper classes.
"""

from __future__ import annotations

from ultima_sdk.binary_extensions import BinaryReader, BinaryWriter


def main() -> int:
    writer = BinaryWriter()
    writer.write_uint16(0xBEEF)
    writer.write_int32(-123)
    writer.write_string("hello", null_terminated=True)

    data = writer.get_buffer() or b""
    reader = BinaryReader(data)

    value_uint16 = reader.read_uint16()
    value_int32 = reader.read_int32()
    value_str = reader.read_string(null_terminated=True)

    print(f"uint16: 0x{value_uint16:04X}")
    print(f"int32: {value_int32}")
    print(f"string: {value_str!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
