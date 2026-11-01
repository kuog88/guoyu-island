"""讀 lessons_115_1.json（本學期）與 lessons_114_2.json（上一個下學期），計算三版本生字重疊。

輸出：
- overlap.json：報告用的統計數字
- char_bank.csv：每個生字在三版本第一次出現的位置（共用題庫的對照表）
"""
import csv
import json
from collections import defaultdict
from itertools import combinations

PUBS = ["nani", "kang", "han"]
NAME = {"nani": "南一", "kang": "康軒", "han": "翰林"}
UP = json.load(open("lessons_115_1.json", encoding="utf-8"))
DOWN = json.load(open("lessons_114_2.json", encoding="utf-8"))
ALL = UP + DOWN


def sem_key(l):
    """學習先後：1上=1.0, 1下=1.5, 2上=2.0 ..."""
    return l["grade"] + (0.5 if l["year"].endswith("_2") else 0)


def label(l):
    sem = "下" if l["year"].endswith("_2") else "上"
    n = l["order"] if (l["grade"] == 1 and sem == "上" and l["pub"] == "nani") else l["order"] + 1
    return f"{l['grade']}{sem}L{n}"


def pct(a, b):
    return round(a / b * 100, 1) if b else 0


# 每個生字在各版本第一次出現（含上、下學期）
first = defaultdict(dict)
for l in sorted(ALL, key=lambda l: (sem_key(l), l["order"])):
    for c in l["chars"]:
        first[c].setdefault(l["pub"], l)


def known(pub, upto):
    """某版本學到 upto（含）為止的生字集合"""
    return {c for c in first if pub in first[c] and sem_key(first[c][pub]) <= upto}


# A. 本學期同一冊的重疊（只看 115 上）
volume = []
for g in range(1, 7):
    s = {p: {c for l in UP if l["pub"] == p and l["grade"] == g for c in l["chars"]} for p in PUBS}
    union = set().union(*s.values())
    inter = s["nani"] & s["kang"] & s["han"]
    volume.append({"grade": g, "count": {p: len(v) for p, v in s.items()}, "union": len(union),
                   "all3": len(inter), "all3Pct": pct(len(inter), len(union)),
                   "pairPct": {f"{a}-{b}": pct(len(s[a] & s[b]), len(s[a] | s[b])) for a, b in combinations(PUBS, 2)}})

# B. 累積重疊：學到 g 上為止，A 版本學過的字，B 版本也學過的比例
cumulative = []
for g in range(1, 7):
    k = {p: known(p, g) for p in PUBS}
    inter = k["nani"] & k["kang"] & k["han"]
    union = set().union(*k.values())
    cumulative.append({"grade": g, "count": {p: len(v) for p, v in k.items()}, "union": len(union),
                       "all3": len(inter), "all3Pct": pct(len(inter), len(union)),
                       "pairPct": {f"{a}-{b}": pct(len(k[a] & k[b]), len(k[a] | k[b])) for a, b in combinations(PUBS, 2)}})

# C. 每課生字「同年級其他版本到本學期結束時也學過」的比例（換版本時可以直接算已學會）
lesson_reuse = []
for l in UP:
    others = [p for p in PUBS if p != l["pub"]]
    row = {"id": l["id"], "pub": l["pub"], "grade": l["grade"], "label": label(l), "title": l["title"], "n": len(l["chars"])}
    for p in others:
        kp = known(p, l["grade"])
        row[p] = pct(sum(c in kp for c in l["chars"]), len(l["chars"]))
    lesson_reuse.append(row)

# D. 三版本生字的時間差：同一個字，最早和最晚的版本差幾個學期
spread = defaultdict(int)
for c, d in first.items():
    if len(d) == 3:
        ks = [sem_key(l) for l in d.values()]
        spread[round((max(ks) - min(ks)) * 2)] += 1

span_count = defaultdict(int)
for c, d in first.items():
    span_count[len(d)] += 1

# E. 課對課高重疊配對（只列出明顯的）
pairs = []
for a, b in combinations(UP, 2):
    if a["pub"] == b["pub"] or not a["chars"] or not b["chars"]:
        continue
    ca, cb = set(a["chars"]), set(b["chars"])
    cov = len(ca & cb) / min(len(ca), len(cb))
    if cov >= 0.3:
        pairs.append({"a": f"{NAME[a['pub']]}{label(a)} {a['title']}", "b": f"{NAME[b['pub']]}{label(b)} {b['title']}",
                      "pct": round(cov * 100), "common": "".join(sorted(ca & cb))})
pairs.sort(key=lambda p: -p["pct"])

# 同名或同故事課的實際重疊
named = [("kang-1上-02", "han-1上-05"), ("kang-2上-06", "han-2上-02"), ("kang-4上-08", "han-4上-01"),
         ("kang-6上-08", "nani-6上-08"), ("nani-6上-02", "han-6上-09")]
byid = {l["id"]: l for l in ALL}
named_out = []
for x, y in named:
    a, b = byid[x], byid[y]
    ca, cb = set(a["chars"]), set(b["chars"])
    named_out.append({"a": f"{NAME[a['pub']]}{label(a)} {a['title']}", "b": f"{NAME[b['pub']]}{label(b)} {b['title']}",
                      "pct": round(len(ca & cb) / min(len(ca), len(cb)) * 100), "common": "".join(sorted(ca & cb)),
                      "commonWords": sorted(set(a["words"]) & set(b["words"]))})

up_chars = {c for l in UP for c in l["chars"]}
summary = {
    "lessonsUp": len(UP), "lessonsDown": len(DOWN),
    "charEntriesUp": sum(len(l["chars"]) for l in UP),
    "uniqueUp": len(up_chars),
    "uniqueAll": len(first),
    "inVersions": {str(k): v for k, v in sorted(span_count.items())},
    "semesterGap": {str(k): v for k, v in sorted(spread.items())},
}
json.dump({"summary": summary, "volume": volume, "cumulative": cumulative, "lessonReuse": lesson_reuse,
           "pairs": pairs, "named": named_out},
          open("overlap.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

with open("char_bank.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["生字", "幾個版本有教", "最早學期", "最晚學期", "南一", "康軒", "翰林"])
    rows = []
    for c, d in first.items():
        ks = [sem_key(l) for l in d.values()]
        fmt = lambda k: f"{int(k)}{'下' if k % 1 else '上'}"
        rows.append([c, len(d), fmt(min(ks)), fmt(max(ks))] +
                    [f"{label(d[p])} {d[p]['title']}" if p in d else "" for p in PUBS] + [min(ks)])
    for r in sorted(rows, key=lambda r: (r[-1], -r[1])):
        w.writerow(r[:-1])

print(json.dumps(summary, ensure_ascii=False))
for v in volume:
    print("vol", v)
for v in cumulative:
    print("cum", v)
for p in named_out:
    print(p)
print(len(pairs), pairs[:5])
avg = defaultdict(list)
for r in lesson_reuse:
    for p in PUBS:
        if p in r:
            avg[r["grade"]].append(r[p])
print({g: round(sum(v) / len(v), 1) for g, v in avg.items()})
