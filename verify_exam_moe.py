"""把三～六年級月考題庫的每一題答案，和教育部最新資料比對：
  注音：《國語辭典簡編本》2026-09-29（沒收再看《重編國語辭典修訂本》）
  部首：簡編本／修訂本（radical_textbook.json 列的課本歸部除外）
  筆畫：《國字標準字體筆順學習網》2025（stroke_moe2025.json，數筆順動畫的筆數）
  用字：正確語詞要在辭典或課文語詞裡，錯字語詞不能是辭典裡的詞
輸出 verify_exam_moe.txt；有問題的題目列在最前面。"""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
import moe_data

D = moe_data.load()
CW, RW, CC, RC = D["cwords"], D["words"], D["cchars"], D["chars"]
SM = json.load(open("stroke_moe2025.json", encoding="utf-8"))
TB = json.load(open("radical_textbook.json", encoding="utf-8"))
RADV = {"氵": "水", "扌": "手", "亻": "人", "忄": "心", "艹": "艸", "辶": "辵", "阝左": "阜", "阝右": "邑", "犭": "犬", "灬": "火", "月": "肉",
        "衤": "衣", "礻": "示", "王": "玉", "刂": "刀", "⺮": "竹", "飠": "食", "罒": "网", "攵": "攴", "牜": "牛", "耂": "老", "糹": "糸",
        "訁": "言", "釒": "金", "⻊": "足"}


def creads(c):
    return set(CC.get(c, {}).get("zy", [])) | set(RC.get(c, {}).get("zy", []))


def wreads(w, lesson):
    r = [tuple(x) for x in CW.get(w, [])] or [tuple(x) for x in RW.get(w, [])]
    if not r and w in lesson:
        r = [tuple(lesson[w])]
    return r


def rad_of(c):
    if c in TB["textbook"]:
        return TB["textbook"][c]
    return CC.get(c, {}).get("rad") or RC.get(c, {}).get("rad")


def radname(s):
    m = re.match(r"(.+?)（(.+)）", s)
    return m.group(1) if m else s


bad, ok, skip = [], 0, []
for g in range(3, 7):
    lesson = {}
    lesson.update(json.load(open(f"game/data/g{g}.json", encoding="utf-8"))["wordZy"])
    D_ = json.load(open(f"game/data/g{g}.json", encoding="utf-8"))
    words_ok = set(CW) | set(RW) | set(lesson) | {w for l in D_["lessons"] for w in l.get("words", [])}
    for pub, B in json.load(open(f"game/exam/g{g}.json", encoding="utf-8")).items():
        for q in B["bank"]:
            t, a, s = q["type"], q["answer"], q["q"]
            tag = f"{g}-{pub} {q['unit']}｜{s}｜{q.get('choices') or q.get('chips') or ''}｜答案 {a}"
            prob = None
            if (m := re.match(r"「(.+?)」的「(.)」，正確的注音是哪一個？", s)):
                w, c = m.groups(); i = w.index(c)
                rs = wreads(w, lesson)
                if rs and a not in {r[i] for r in rs}:
                    prob = f"注音和辭典不同：{[' '.join(r) for r in rs]}"
                elif not rs and a not in creads(c):
                    prob = f"單字讀音不在辭典：{sorted(creads(c))}"
                for o in q["choices"]:
                    if o != a and rs and o in {r[i] for r in rs}:
                        prob = f"錯誤選項 {o} 其實也是辭典讀音"
            elif (m := re.match(r"「(.)」的正確注音是哪一個？", s)):
                c = m.group(1)
                if a not in creads(c):
                    prob = f"讀音不在辭典：{sorted(creads(c))}"
                for o in q["choices"]:
                    if o != a and o in creads(c):
                        prob = f"錯誤選項 {o} 也是這個字的讀音（沒有語詞可以分辨）"
            elif (m := re.match(r"看注音(?:，選出正確的國字|寫國字)：(.*)（(.+?)）(.*)", s)):
                pre, z, post = m.groups()
                w = pre + a + post
                rs = wreads(w, lesson) if len(w) > 1 else []
                if rs:
                    if z not in {r[len(pre)] for r in rs}:
                        prob = f"語詞讀音不符：{[' '.join(r) for r in rs]}"
                elif z not in creads(a):
                    prob = f"單字讀音不符：{sorted(creads(a))}"
                for o in (q.get("choices") or q.get("chips") or []):
                    if o != a and z in creads(o):
                        if not rs or (pre + o + post) in words_ok:
                            prob = f"錯誤選項「{o}」也念 {z}"
            elif (m := re.match(r"「(.)」的部首是哪一個？", s)):
                c = m.group(1)
                if radname(a) != rad_of(c):
                    prob = f"部首和辭典不同：{rad_of(c)}"
            elif (m := re.match(r"「(.)」的部首是「(.+)」。", s)):
                c, r = m.groups()
                if (radname(r) == rad_of(c)) != a:
                    prob = f"部首是非題答案不符：辭典 {rad_of(c)}"
            elif (m := re.match(r"「(.)」一共有（　）畫。", s)):
                c = m.group(1); n = SM.get(c)
                dn = CC.get(c, {}).get("n") or RC.get(c, {}).get("n")
                if isinstance(n, list):
                    # 筆順網動畫實際筆數；少數字動畫多拆一筆（寓、慰、瞞），以三部辭典一致的筆畫數為準
                    if str(a) not in {str(n[0]), str(dn)}:
                        prob = f"筆畫不同：筆順網動畫 {n[0]}、網頁標示 {n[1]}、簡編本 {dn}"
                else:
                    skip.append(f"筆順網沒收：{c}（題目 {a} 畫）")
            elif (m := re.match(r"「(.+?)」的注音是「(.+)」。", s)):
                w, z = m.groups(); rs = wreads(w, lesson)
                if rs and ((tuple(z.split()) in rs) != a):
                    prob = f"語詞注音是非題不符：{[' '.join(r) for r in rs]}"
            elif (m := re.match(r"「(.+?)」這個語詞的用字完全正確。", s)):
                w = m.group(1)
                if (w in words_ok) != a:
                    prob = f"用字是非題不符（辭典{'有' if w in words_ok else '沒有'}這個詞）"
            elif s.startswith("下面哪一個語詞的用字完全正確"):
                if a not in words_ok:
                    prob = "正確答案不在辭典"
                for o in q["choices"]:
                    if o != a and o in words_ok:
                        prob = f"錯誤選項「{o}」是辭典裡的詞"
            elif s.startswith("下面哪一個語詞有錯字"):
                if a in words_ok:
                    prob = f"答案「{a}」其實是辭典裡的詞"
                for o in q["choices"]:
                    if o != a and o not in words_ok:
                        prob = f"選項「{o}」不在辭典（可能也算錯字）"
            elif s.startswith("下面哪一個語詞的注音「不正確」"):
                for o in q["choices"]:
                    w, z = o.split(" ", 1); rs = wreads(w, lesson)
                    good = tuple(z.split()) in rs
                    if (o == a) == good and rs:
                        prob = f"「{o}」判斷和辭典不符：{[' '.join(r) for r in rs]}"
            else:
                skip.append("沒有自動比對的題型：" + s[:30])
                continue
            if prob:
                bad.append(f"{tag}｜{prob}")
            else:
                ok += 1
lines = [f"比對通過 {ok} 題；有問題 {len(bad)} 題；沒有比對 {len(skip)} 題", ""] + bad + ["", "＝沒有比對的＝"] + sorted(set(skip))
open("verify_exam_moe.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines[:60]))
