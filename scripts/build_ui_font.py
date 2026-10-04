"""Build the licensed UI subset with fonttools[woff]; retain the full plotting font."""

import hashlib
import json
from pathlib import Path

from fontTools import __version__ as fonttools_version
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "envevidence/assets/fonts"


def main():
    codepoints = set()
    for first in range(0xA1, 0xFF):
        for second in range(0xA1, 0xFF):
            try:
                codepoints.update(map(ord, bytes([first, second]).decode("gb2312")))
            except UnicodeDecodeError:
                pass
    options = subset.Options()
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14, 16, 17]
    font = TTFont(FONTS / "NotoSansCJKsc-Regular.otf")
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=codepoints)
    sub.subset(font)
    for entry in font["name"].names:
        if entry.nameID in (1, 4, 6, 16):
            name = "EnvSansCJK-Regular" if entry.nameID == 6 else "Env Sans CJK"
            entry.string = name.encode(entry.getEncoding())
        elif entry.nameID == 3:
            entry.string = "EnvSansCJK-UI-Regular-1.0".encode(entry.getEncoding())
    cff = font["CFF "].cff
    cff.fontNames = ["EnvSansCJK-Regular"]
    cff.topDictIndex[0].FamilyName = "Env Sans CJK"
    cff.topDictIndex[0].FullName = "Env Sans CJK Regular"
    font.flavor = "woff2"
    output = FONTS / "EnvSansCJK-UI.woff2"
    font.save(output)
    source = json.loads((FONTS / "SOURCE.json").read_text(encoding="utf-8"))
    record = {
        "source": source, "derivation": "GB2312 repertoire; UI subset; renamed Env Sans CJK",
        "tool": f"fontTools {fonttools_version}", "license": "OFL.txt",
        "codepoints": len(codepoints), "bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    (FONTS / "UI-CJK-SOURCE.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"UI font: {record['bytes']} bytes; {record['codepoints']} codepoints")


if __name__ == "__main__":
    main()
