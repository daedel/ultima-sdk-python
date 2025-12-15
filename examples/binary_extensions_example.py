"""BinaryReader/BinaryWriter example.

Run:
  python -m examples.binary_extensions_example
"""

from __future__ import annotations

from ultima_sdk.binary_extensions import BinaryReader, BinaryWriter


def main() -> int:
    w = BinaryWriter()
    w.write_uint16(0xBEEF)
    w.write_int32(-123)
    w.write_string("hello", null_terminated=True)
    data = w.stream.getvalue()  # BytesIO

    r = BinaryReader(data)
    a = r.read_uint16()
    b = r.read_int32()
    s = r.read_string(null_terminated=True)

    print(f"uint16: 0x{a:04X}")
    print(f"int32: {b}")
    print(f"string: {s!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
