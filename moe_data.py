"""教育部國語辭典公眾授權網的最新資料（https://language.moe.gov.tw/001/Upload/Files/site_content/M0001/respub/）：
  《重編國語辭典修訂本》 dict_revised_2015_20260929
  《國語辭典簡編本》     dict_concised_2014_20260929（給中小學生用，讀音依《國語一字多音審訂表》）
  《國語小字典》         dict_mini_2019_20260929
  《成語典》             dict_idioms_2020_20260929
下載後放在 fonts_src/moe/（不進版本庫），第一次讀取時轉成 fonts_src/moe/moe_cache.json。
"""
import io, json, os, re, zipfile

DIR = "fonts_src/moe"
FILES = {"revised": "dict_revised_2015_20260929.zip", "concised": "dict_concised_2014_20260929.zip", "mini": "dict_mini_2019_20260929.zip", "idioms": "dict_idioms_2020_20260929.zip"}
CACHE = os.path.join(DIR, "moe_cache.json")
VERSION = {k: v.replace(".zip", "") for k, v in FILES.items()}
ZY = re.compile(r"[ㄅ-ㄩˊˇˋ˙]+")


def _rows(name):
    import openpyxl
    z = zipfile.ZipFile(os.path.join(DIR, FILES[name]))
    n = [i for i in z.namelist() if "欄位" not in i][0]
    ws = openpyxl.load_workbook(io.BytesIO(z.read(n)), read_only=True).active
    it = ws.iter_rows(values_only=True)
    head = next(it)
    for r in it:
        yield dict(zip(head, r))


def _syl(s, n):
    """注音字串 → 每個字一組；長度不符回傳 None"""
    if not s:
        return None
    s = re.sub(r"（[^）]*）|\([^)]*\)", " ", str(s))
    parts = ZY.findall(s.replace("　", " "))
    return parts[:n] if len(parts) >= n else None


def _dict(name):
    words, chars = {}, {}
    for r in _rows(name):
        t = (r["字詞名"] or "").strip()
        if not t:
            continue
        n = len(t)
        rs = []
        main = _syl(r["注音一式"], n)
        if main:
            rs.append(main)
        var = _syl(r["變體注音"], n)
        if var:
            rs.append(var)
        if n == 1:
            c = chars.setdefault(t, {"zy": [], "rad": None, "n": None})
            for x in rs:
                if x[0] not in c["zy"]:
                    c["zy"].append(x[0])
            c["rad"] = c["rad"] or (r["部首字"] or "").strip() or None
            c["n"] = c["n"] or r["總筆畫數"]
        else:
            w = words.setdefault(t, [])
            for x in rs:
                if x not in w:
                    w.append(x)
    return words, chars


def build():
    words, chars = _dict("revised")
    cwords, cchars = _dict("concised")
    mini = {}
    for r in _rows("mini"):
        c = (r["單字"] or "").strip()
        if not c:
            continue
        m = mini.setdefault(c, {"zy": [], "rad": (r["部首"] or "").strip(), "n": int(r["總筆畫數"] or 0)})
        z = ZY.findall(str(r["注音"] or ""))
        if z and z[0] not in m["zy"]:
            m["zy"].append(z[0])
    idioms = {}
    for r in _rows("idioms"):
        t = (r["成語"] or "").strip()
        if t:
            mean = re.sub(r"_x000D_|\s+", " ", str(r["釋義"] or "")).strip()
            idioms[t] = {"zy": str(r["注音"] or "").replace("　", " "), "mean": mean, "near": r["近義成語"] or "", "opp": r["反義成語"] or ""}
    data = {"version": VERSION, "words": words, "chars": chars, "cwords": cwords, "cchars": cchars, "mini": mini, "idioms": idioms}
    json.dump(data, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return data


_D = None


def load():
    global _D
    if _D is None:
        _D = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else build()
    return _D


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    d = build()
    print({k: len(v) for k, v in d.items() if k != "version"}, d["version"])
    for w in ["窗戶", "玻璃", "操場", "熟悉", "蹣跚", "確鑿", "朋友", "大家"]:
        print(w, d["words"].get(w), d["cwords"].get(w))
    for c in "祛袪襬充響和":
        print(c, d["chars"].get(c), d["mini"].get(c))
