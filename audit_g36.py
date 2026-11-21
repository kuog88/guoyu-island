"""三～六年級題庫健檢：格式、重複、矛盾、題數，以及注音／部首／筆畫和教育部辭典的差異。
輸出 audit_g36_report.txt（給人工複查用）。"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
import make_zy_g1

out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))
words_d, chars_d, _ = make_zy_g1.load_dict()

# 辭典裡單字的部首與筆畫
import lzma
D = json.loads(lzma.open(make_zy_g1.MOE_DICT).read().decode("utf-8"))
crad = {e["title"]: ((e.get("radical") or "").strip() or None, e.get("stroke_count")) for e in D if len(e.get("title", "")) == 1}

total = 0
for g in range(3, 7):
    d = json.load(open(f"game/data/g{g}.json", encoding="utf-8"))
    P(f"\n==== {g} 年級 ====")
    bank = d["bank"]
    seen = {}
    for k, rows in bank.items():
        for r in rows:
            total += 1
            q = r[0]
            if any(not x.strip() for x in r[:4 if k != "transform" else 5]):
                P("空白欄位", k, r)
            if k == "transform":
                opts = r[2:5]
            elif k == "measure":
                opts = [re.search(r"\[(.+?)\]", r[0]).group(1)] + r[1:3]
            elif k == "idiom":
                opts = [r[0], r[3], r[4]]
                if f"[{r[0]}]" not in r[2]:
                    P("成語例句挖空不符", r[:3])
            else:
                opts = r[1:4]
            if len(set(opts)) != len(opts):
                P("選項重複", k, r)
            if k in ("conn", "punct"):
                nb = r[0].count("[]")
                for o in opts:
                    if o.count("…") + 1 != nb:
                        P("空格數和答案段數不符", k, r[0], o)
            key = (k, q if k != "transform" else r[1])
            if key in seen and seen[key] != opts[0]:
                P("同一題答案不同", k, q)
            elif key in seen:
                P("同一題出現兩次", k, q)
            seen[key] = opts[0]
    # 各課 W／B
    for l in d["lessons"]:
        it = l.get("items") or {}
        for s, a, w1, w2 in it.get("fill", []):
            total += 1
            if len({a, w1, w2}) < 3:
                P("選詞填空選項重複", l["id"], s)
        for b in it.get("build", []):
            total += 1
            if any(sorted(x) != sorted(b[0]) for x in b[1:]):
                P("句子積木：替代答案用的積木不同（不會被接受）", l["id"], b)
        if len(it.get("fill", [])) < 5 or len(it.get("build", [])) < 3:
            P("題數偏少", l["id"], l["title"], len(it.get("fill", [])), len(it.get("build", [])))
    # 閱讀
    for lid, r in (d.get("reading") or {}).items():
        for x in r["qs"]:
            total += 1
            if len(set(x[1:])) != len(x[1:]):
                P("閱讀選項重複", lid, x[0])
    # 注音／部首／筆畫：和辭典比對
    info = d["info"]
    for c, v in info.items():
        z, rad, n = v[0], v[1], v[2]
        if chars_d.get(c) and z not in chars_d[c]:
            P("注音不在辭典讀音裡", c, z, chars_d[c])
        dr, dn = crad.get(c, (None, None))
        if dr and dr != rad and not (len(v) > 3):
            P("部首和辭典不同", c, rad, dr)
        if dn and n not in (dn, dn - 1):
            P("筆畫和辭典差太多", c, n, dn)
    for w, r in d["wordZy"].items():
        if w in words_d and r not in words_d[w]:
            P("語詞注音和辭典不同", w, " ".join(r), [" ".join(x) for x in words_d[w]])
    # 各課題數（遊戲字詞）
    for pub in ("nani", "kang", "han"):
        ls = [l for l in d["lessons"] if l["pub"] == pub]
        cs = [len(l["chars"]) for l in ls]
        ws = [len(l["words"]) for l in ls]
        P(f"{pub} 生字數 {cs} 語詞數 {ws}")
    # 題庫分配到各課後的數量（加強練習用全範圍，不看）
    P("共用題庫各類題數", {k: len(v) for k, v in bank.items()})
# 月考卷
for g in range(3, 7):
    ex = json.load(open(f"game/exam/g{g}.json", encoding="utf-8"))
    for pub, B in ex.items():
        c = collections.Counter(q["unit"] for q in B["bank"])
        lo = min(c.values())
        P(f"月考題庫 {g}-{pub}：{len(B['bank'])} 題，單元最少 {lo}，最多 {max(c.values())}", [u for u, n in c.items() if n < 60])
        total += len(B["bank"])
P("\n總題數（含月考卷）", total)
open("audit_g36_report.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out[-40:]))
