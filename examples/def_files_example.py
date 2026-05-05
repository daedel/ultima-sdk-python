"""def_files parser example.

Demonstrates parsing BodyConvDef, BodyDef, and EquipConvDef from text.
"""

from __future__ import annotations

from ultima_sdk.def_files import BodyConvDef, BodyDef, EquipConvDef


def main() -> int:
    bodyconv_text = """
# original anim2 anim3 anim4 anim5
400 10 -1 -1 -1
401 -1 20 -1 -1
"""
    bodydef_text = """
# new { old }
5 { 0 }
10 { 20, 0, 0 }
"""
    equipconv_text = """
# old new
0x1234 0x2345
# per-body
400 0x1111 0x2222
"""

    bodyconv = BodyConvDef.from_text(bodyconv_text)
    bodydef = BodyDef.from_text(bodydef_text)
    equipconv = EquipConvDef.from_text(equipconv_text)

    print("BodyConv 400 ->", bodyconv.resolve(400))
    print("BodyDef 5 ->", bodydef.translate_body(5))
    print("EquipConv global 0x1234 ->", hex(equipconv.convert(0x1234)))
    print("EquipConv body 400 0x1111 ->", hex(equipconv.convert(0x1111, body_id=400)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
