"""產生一上生字的筆畫資料 strokes_g1.json，筆順依臺灣教育部標準。

字形（筆畫外框與中線）來自 hanzi-writer-data（Make Me a Hanzi，大陸筆順）。
另外讀取 g0v/zh-stroke-data（教育部常用國字標準字體筆順）每一筆的起點和終點，
把 hanzi-writer 的筆畫一筆一筆對應過去，再依教育部的順序重新排列。
筆畫數對不上的字會列出來，需要人工確認。
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


def one(ch):
    hw = get_json(f"https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/{quote(ch)}.json")
    if not hw:
        return ch, None, ("noGlyph", ch)
    g = get_json(f"https://raw.githubusercontent.com/g0v/zh-stroke-data/master/json/{ord(ch):x}.json")
    entry = {"strokes": hw["strokes"], "medians": hw["medians"]}
    if not g:
        return ch, entry, ("noMoe", ch)
    if len(g) != len(hw["strokes"]):
        return ch, entry, ("countMismatch", f"{ch}({len(hw['strokes'])}/{len(g)})")
    order, avg = assign(moe_points(g), hw_points(hw))
    note = ("lowConfidence", f"{ch}({avg:.2f})") if avg > 0.25 else None
    if order != list(range(len(order))):
        entry = {"strokes": [hw["strokes"][j] for j in order], "medians": [hw["medians"][j] for j in order]}
        note = note or ("reordered", ch)
    return ch, entry, note


def main():
    """用法：python fetch_strokes.py 1 2 3 4 5 6"""
    from concurrent.futures import ThreadPoolExecutor
    grades = [int(x) for x in sys.argv[1:]] or [1]
    all_lessons = json.load(open("lessons_115_1.json", encoding="utf-8"))
    for grade in grades:
        chars = sorted({c for l in all_lessons if l["grade"] == grade for c in l["chars"]})
        out, report = {}, {"reordered": [], "countMismatch": [], "noMoe": [], "noGlyph": [], "lowConfidence": []}
        with ThreadPoolExecutor(6) as ex:
            for ch, entry, note in ex.map(one, chars):
                if note:
                    report[note[0]].append(note[1])
                    if note[0] == "lowConfidence" and entry is not None:
                        pass
                if entry is not None:
                    out[ch] = entry
        json.dump(out, open(f"strokes_g{grade}.json", "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(report, open(f"strokes_g{grade}_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(grade, len(chars), {k: len(v) for k, v in report.items()}, flush=True)


if __name__ == "__main__":
    main()
