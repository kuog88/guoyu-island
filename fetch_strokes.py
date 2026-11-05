"""產生生字的筆畫資料 strokes_g{n}.json（描寫用的字形與筆順），依臺灣教育部標準。

字形優先用 g0v/zh-stroke-data（教育部常用國字標準字體筆順）的筆畫外框，筆順和寫法都是臺灣標準。
只有在教育部資料的筆畫數有誤時（例如「回」資料多一筆），才改用 hanzi-writer-data（Make Me a Hanzi）
的字形，並依教育部每一筆的起訖點重新排序；兩邊筆畫數都不對的字不做描寫。
筆畫數以 stroke_count.json／字典為準（和字卡一致，見 build_game.py 的 strokes_of）。
"""
import json
import sys
import time
from itertools import permutations
from urllib.parse import quote

import requests

S = requests.Session()


def get_json(url):
    for attempt in range(4):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 404:
                return None
            if r.ok:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(1 + attempt)
    return None


def hw_points(hw):
    """hanzi-writer 座標：1024 方格，y 向上，基線偏移 900"""
    return [((m[0][0] / 1024, (900 - m[0][1]) / 1024), (m[-1][0] / 1024, (900 - m[-1][1]) / 1024)) for m in hw["medians"]]


def moe_points(g):
    """g0v 座標：2150 方格，y 向下"""
    out = []
    for s in g:
        t = s["track"]
        out.append(((t[0]["x"] / 2150, t[0]["y"] / 2150), (t[-1]["x"] / 2150, t[-1]["y"] / 2150)))
    return out


def dist(a, b):
    return ((a[0][0] - b[0][0]) ** 2 + (a[0][1] - b[0][1]) ** 2) ** .5 + ((a[1][0] - b[1][0]) ** 2 + (a[1][1] - b[1][1]) ** 2) ** .5


def assign(moe, hw):
    """回傳 order：教育部第 i 筆對應 hanzi-writer 第 order[i] 筆（匈牙利法，n 小用 scipy 或貪婪）"""
    n = len(moe)
    cost = [[dist(moe[i], hw[j]) for j in range(n)] for i in range(n)]
    try:
        from scipy.optimize import linear_sum_assignment
        r, c = linear_sum_assignment(cost)
        return [int(x) for x in c], sum(cost[i][c[i]] for i in range(n)) / n
    except ImportError:
        used, order = set(), []
        for i in range(n):
            j = min((j for j in range(n) if j not in used), key=lambda j: cost[i][j])
            used.add(j)
            order.append(j)
        return order, sum(cost[i][order[i]] for i in range(n)) / n


def moe_entry(g):
    """g0v 座標（2150 方格，y 向下）換成 hanzi-writer 座標（1024 方格，y 向上，基線 900）"""
    k = 1024 / 2150
    pt = lambda x, y: f"{x * k:.1f} {900 - y * k:.1f}"
    strokes, medians = [], []
    for st in g:
        d = []
        for p in st["outline"]:
            if p["type"] == "Q":
                d.append(f"Q {pt(p['begin']['x'], p['begin']['y'])} {pt(p['end']['x'], p['end']['y'])}")
            elif p["type"] == "C":
                d.append(f"C {pt(p['begin']['x'], p['begin']['y'])} {pt(p['mid']['x'], p['mid']['y'])} {pt(p['end']['x'], p['end']['y'])}")
            else:
                d.append(f"{p['type']} {pt(p['x'], p['y'])}")
        strokes.append(" ".join(d) + " Z")
        medians.append([[round(t["x"] * k, 1), round(900 - t["y"] * k, 1)] for t in st["track"]])
    return {"strokes": strokes, "medians": medians}


def one(ch, want):
    g = get_json(f"https://raw.githubusercontent.com/g0v/zh-stroke-data/master/json/{ord(ch):x}.json")
    if g and len(g) == want:
        return ch, moe_entry(g), None
    hw = get_json(f"https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/{quote(ch)}.json")
    if not hw:
        return ch, None, ("noGlyph", ch)
    if not g:
        return ch, None, ("noMoe", ch)
    entry = {"strokes": hw["strokes"], "medians": hw["medians"]}
    if len(hw["strokes"]) != want or len(g) != want and len(g) != len(hw["strokes"]):
        return ch, None, ("countMismatch", f"{ch}(字典{want}/教育部{len(g)}/MMAH{len(hw['strokes'])})")
    if len(g) != len(hw["strokes"]):
        return ch, entry, ("fallbackGlyph", ch)
    order, avg = assign(moe_points(g), hw_points(hw))
    entry = {"strokes": [hw["strokes"][j] for j in order], "medians": [hw["medians"][j] for j in order]}
    return ch, entry, ("fallbackGlyph", f"{ch}({avg:.2f})")


def main():
    """用法：python fetch_strokes.py 1 2 3 4 5 6"""
    from concurrent.futures import ThreadPoolExecutor
    grades = [int(x) for x in sys.argv[1:]] or [1]
    from build_game import strokes_of
    all_lessons = json.load(open("lessons_115_1.json", encoding="utf-8"))
    cinfo = json.load(open("char_info_all.json", encoding="utf-8"))
    moe_count = json.load(open("stroke_count.json", encoding="utf-8"))
    for grade in grades:
        chars = sorted({c for l in all_lessons if l["grade"] == grade for c in l["chars"]})
        want = [strokes_of(c, (cinfo.get(c) or {}).get("strokes"), moe_count) for c in chars]
        out, report = {}, {"fallbackGlyph": [], "countMismatch": [], "noMoe": [], "noGlyph": []}
        with ThreadPoolExecutor(6) as ex:
            for ch, entry, note in ex.map(one, chars, want):
                if note:
                    report[note[0]].append(note[1])
                if entry is not None:
                    out[ch] = entry
        json.dump(out, open(f"strokes_g{grade}.json", "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(report, open(f"strokes_g{grade}_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(grade, len(chars), {k: len(v) for k, v in report.items()}, flush=True)


if __name__ == "__main__":
    main()
