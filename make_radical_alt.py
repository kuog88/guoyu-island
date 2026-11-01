"""比對部首：教育部字典（char_info_all.json）和 Unicode Unihan 的康熙部首（kRSUnicode），輸出 radical_alt.json。

有些字教育部字典和康熙字典歸的部首不同（例如「最」教育部歸冂部、康熙歸曰部，「初」教育部歸衣部、康熙歸刀部），
課本和考卷可能用其中任何一種。這些字在字卡上兩種都列出來，也不拿來出部首題，免得孩子照課本答反而被判錯。

用法：python make_radical_alt.py <Unihan_IRGSources.txt 的路徑>
（Unihan.zip 從 https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip 下載）
"""
import json
import re
import sys
import unicodedata

SAME = {"靑": "青"}  # 異體寫法，算同一個部首


def main():
    rs = {}
    for line in open(sys.argv[1], encoding="utf-8"):
        if "\tkRSUnicode\t" not in line:
            continue
        cp, _, v = line.rstrip("\n").split("\t")
        rads = []
        for x in v.split():
            r = unicodedata.normalize("NFKC", chr(0x2F00 + int(re.match(r"\d+", x).group()) - 1))
            r = SAME.get(r, r)
            if r not in rads:
                rads.append(r)
        rs[chr(int(cp[2:], 16))] = rads
    info = json.load(open("char_info_all.json", encoding="utf-8"))
    out = {}
    for c, v in sorted(info.items()):
        r, u = v.get("radical"), rs.get(c, [])
        alt = [x for x in u if x != r]
        if r and alt:
            out[c] = alt
    json.dump(out, open("radical_alt.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(out), " ".join(f"{c}:{info[c]['radical']}/{''.join(a)}" for c, a in out.items()))


if __name__ == "__main__":
    main()
