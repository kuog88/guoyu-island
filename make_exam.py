"""📝 月考測驗卷題庫：從各課生字、語詞、句子自動出 是非／選擇／填充 題，輸出 game/exam/g{n}.json。

每個年級、每個版本各一份：{pub: {"grade", "papers", "bank"}}，遊戲在地圖頁用 KGExam.mount 掛上。
題型（每一課）：
  選擇：語詞裡某個字的注音（陷阱：聲調、形近符號）、看注音選國字（陷阱：同音字、形近字）、
        部首、哪一個語詞用字正確／有錯字、哪一個注音不正確、選詞填空（三年級以上）
  是非：部首敘述、語詞注音、語詞用字
  填充：看注音寫國字（點選字卡，陷阱是同音字）、筆畫數、句子填空
一年級第一次月考是注音符號（聲調、二拼、三拼、符號分類），不出國字。
一年級題目的說明文字加注音（行內樣式，因為測驗卷引擎會重設樣式），考的字、選項不加，避免洩漏答案。
所有讀音都排除這個字的其他合法讀音，選擇題保證只有一個正確答案。
需要：game/data/g*.json（build_game.py 產生）、fonts_src/dict-revised.json.xz（辭典，用來排除多音字、檢查假詞）
"""
import json, os, random, re, sys

sys.stdout.reconfigure(encoding="utf-8")
import make_zy_g1

PUBN = {"nani": "南一", "kang": "康軒", "han": "翰林"}
GN = ["", "一", "二", "三", "四", "五", "六"]
TONEK = {1: "", 2: "ˊ", 3: "ˇ", 4: "ˋ", 5: "˙"}
TONEN = {1: "第一聲", 2: "第二聲", 3: "第三聲", 4: "第四聲", 5: "輕聲"}
LOOK = {"ㄅ": "ㄆㄉ", "ㄆ": "ㄅㄊ", "ㄇ": "ㄈㄋ", "ㄈ": "ㄇㄏ", "ㄉ": "ㄊㄅ", "ㄊ": "ㄉㄆ", "ㄋ": "ㄌㄇ", "ㄌ": "ㄋㄖ", "ㄍ": "ㄎㄏ",
        "ㄎ": "ㄍㄏ", "ㄏ": "ㄈㄎ", "ㄐ": "ㄑㄓ", "ㄑ": "ㄐㄔ", "ㄒ": "ㄕㄙ", "ㄓ": "ㄗㄐ", "ㄔ": "ㄘㄑ", "ㄕ": "ㄙㄒ", "ㄖ": "ㄌ",
        "ㄗ": "ㄓㄘ", "ㄘ": "ㄔㄗ", "ㄙ": "ㄕㄒ", "ㄧ": "ㄩ", "ㄨ": "ㄩ", "ㄩ": "ㄧㄨ", "ㄚ": "ㄛ", "ㄛ": "ㄜㄡ", "ㄜ": "ㄛ",
        "ㄝ": "ㄟ", "ㄞ": "ㄟ", "ㄟ": "ㄞㄝ", "ㄠ": "ㄡ", "ㄡ": "ㄠ", "ㄢ": "ㄤ", "ㄣ": "ㄥ", "ㄤ": "ㄢ", "ㄥ": "ㄣ", "ㄦ": "ㄜ"}
INIT = set("ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙ")
MED = set("ㄧㄨㄩ")
FIN = set("ㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ")
RAD_VAR = {"水": "氵", "手": "扌", "人": "亻", "心": "忄", "艸": "艹", "辵": "辶", "阜": "阝左", "邑": "阝右", "犬": "犭", "火": "灬",
           "肉": "月", "衣": "衤", "示": "礻", "玉": "王", "刀": "刂", "竹": "⺮", "食": "飠", "网": "罒", "攴": "攵", "牛": "牜",
           "老": "耂", "糸": "糹", "言": "訁", "金": "釒", "足": "⻊"}
radl = lambda r: f"{r}（{RAD_VAR[r]}）" if r in RAD_VAR else r


def parse(z):
    t = 5 if z.startswith("˙") else 2 if "ˊ" in z else 3 if "ˇ" in z else 4 if "ˋ" in z else 1
    return re.sub("[˙ˊˇˋ]", "", z), t


def fmt(s, t):
    return "˙" + s if t == 5 else s + TONEK[t]


class ZY:
    """一年級說明文字的注音（和遊戲同一套讀音），輸出行內樣式的 HTML"""
    def __init__(self, g1):
        z = json.load(open("zy_g1.json", encoding="utf-8"))
        self.ph = {w: v.split() for w, v in z["phrases"].items()}
        self.ph.update(g1["wordZy"])
        self.ch = {c: v[0] for c, v in g1["info"].items()}
        self.ch.update(z["chars"])

    def read(self, s):
        out, i = [], 0
        while i < len(s):
            for n in range(min(6, len(s) - i), 1, -1):
                if s[i:i + n] in self.ph:
                    out += self.ph[s[i:i + n]]; i += n; break
            else:
                out.append(self.ch.get(s[i], "")); i += 1
        return out

    @staticmethod
    def cell(c, z, post=""):
        b, t = parse(z)
        sy = "".join(f"<span>{x}</span>" for x in b)
        dot = "<span>˙</span>" if t == 5 else ""
        tn = f'<span style="position:absolute;right:0;top:50%;transform:translateY(-50%)">{TONEK[t]}</span>' if t in (2, 3, 4) else ""
        return (f'<span style="display:inline-flex;align-items:center;vertical-align:middle;margin-right:.06em">{c}'
                f'<span style="display:inline-flex;flex-direction:column;align-items:center;font-size:max(.5em,9px);line-height:1.05;'
                f'position:relative;padding-right:.62em;margin-left:.06em;color:#555">{dot}{sy}{tn}</span>{post}</span>')

    def html(self, s):
        r, out = self.read(s), ""
        i = 0
        while i < len(s):
            c = s[i]
            if r[i] and re.match(r"[㐀-鿿]", c):
                post = ""
                while i + 1 < len(s) and s[i + 1] in "，。！？、：；」』）":
                    post += s[i + 1]; i += 1
                out += self.cell(c, r[i - len(post)], post)
            else:
                out += c.replace("<", "&lt;")
            i += 1
        return out


def main():
    rnd = random.Random(20261106)
    words_d, chars_d, _ = make_zy_g1.load_dict()
    realw = set(words_d)
    os.makedirs("game/exam", exist_ok=True)
    g1 = json.load(open("game/data/g1.json", encoding="utf-8"))
    zyh = ZY(g1)
    report = {}
    for g in range(1, 7):
        D = json.load(open(f"game/data/g{g}.json", encoding="utf-8"))
        info, wzy = D["info"], D["wordZy"]
        realw |= set(wzy)
        T = (lambda s: zyh.html(s)) if g == 1 else (lambda s: s)   # 說明文字（可以加注音）

        VAL = {}
        for w, r in wzy.items():
            for i, x in enumerate(w):
                if i < len(r):
                    VAL.setdefault(x, set()).add(r[i])

        def valid(c):
            v = VAL.setdefault(c, set())
            if not v or c not in DONE:
                DONE.add(c)
                v |= set(chars_d.get(c, []))
                if c in info:
                    v.add(info[c][0])
            return v
        DONE = set()

        def reading(w, l):
            if w in wzy and len(wzy[w]) == len(w):
                return wzy[w]
            return [l["zy"].get(c) or info[c][0] for c in w]

        def zy_variants(c, z):
            """和 z 很像、但不是 c 任何讀音的注音（陷阱：聲調、形近符號）"""
            b, t = parse(z)
            ok = {parse(x) for x in valid(c)}
            out = []
            for t2 in [1, 2, 3, 4, 5]:
                if t2 != t:
                    out.append((b, t2))
            for i, x in enumerate(b):
                for y in LOOK.get(x, ""):
                    out.append((b[:i] + y + b[i + 1:], t))
            out = [o for o in dict.fromkeys(out) if o not in ok]
            # 聲調錯一個、符號錯一個、兩個都錯，混著放
            tone = [o for o in out if o[0] == b]
            sym = [o for o in out if o[0] != b]
            rnd.shuffle(tone); rnd.shuffle(sym)
            pick = (tone[:2] + sym[:1]) if sym else tone[:3]
            if len(pick) < 3:
                pick += [o for o in tone + sym if o not in pick][:3 - len(pick)]
            return [fmt(*o) for o in pick]

        for pub in ("nani", "kang", "han"):
            ls = sorted([l for l in D["lessons"] if l["pub"] == pub], key=lambda l: l["order"])
            pool = [c for l in ls for c in l["chars"] if c in info]
            pool = list(dict.fromkeys(pool))
            bank, units, stat = [], [], {}
            CAND = list(dict.fromkeys(pool + list(info)))

            def uname(l):
                return f"前導 {l['title']}" if g == 1 and pub == "nani" and l["order"] == 0 else f"第{l['lessonNo']}課 {l['title']}"

            def add(u, q, trap=False):
                q["unit"] = u
                bank.append(q)
                s = stat.setdefault(u, {"tf": 0, "choice": 0, "fill": 0, "trap": 0})
                s[q["type"]] += 1
                s["trap"] += 1 if trap else 0

            def homo(c, z, w=None, i=None, n=3):
                """看注音選字的錯誤選項：同音不同調的字最優先，再來同部首、筆畫相近的字；不能也念 z，換進語詞也不能變成真的詞"""
                b, t = parse(z)
                def okd(d):
                    if d == c or z in valid(d):
                        return False
                    if w is not None and (w[:i] + d + w[i + 1:]) in realw:
                        return False
                    return True
                cand = [d for d in CAND if okd(d)]
                same = [d for d in cand if any(parse(x)[0] == b for x in valid(d))]
                rad = [d for d in cand if info.get(d, [0, 0])[1] == info[c][1]]
                near = [d for d in cand if abs(info.get(d, [0, 0, 99])[2] - info[c][2]) <= 1]
                out = []
                for grp in (same, rad, near, cand):
                    g2 = grp[:]; rnd.shuffle(g2)
                    for d in g2:
                        if d not in out:
                            out.append(d)
                        if len(out) >= n:
                            return out, bool(same and out[0] in same)
                return out, bool(same)

            # ---------- 一年級第一次月考：注音符號 ----------
            zy_units = []
            if g == 1:
                sylls = sorted({info[c][0] for c in info})
                U = ["注音 1 聲調", "注音 2 二拼音", "注音 3 三拼音", "注音 4 聲母、介音、韻母"]
                zy_units = U
                for z in rnd.sample(sylls, len(sylls)):
                    b, t = parse(z)
                    # 聲調
                    if stat.get(U[0], {}).get("choice", 0) < 14:
                        add(U[0], {"type": "choice", "q": T("「") + z + T("」念第幾聲？"), "choices": [TONEN[k] for k in (1, 2, 3, 4)] if t != 5 else ["第一聲", "第三聲", "第四聲", "輕聲"],
                                   "answer": TONEN[t], "explain": f"{z}：" + ("沒有標調號是第一聲。" if t == 1 else "前面有一點是輕聲。" if t == 5 else f"調號「{TONEK[t]}」是{TONEN[t]}。")}, trap=t in (1, 5))
                    if stat.get(U[0], {}).get("tf", 0) < 8:
                        t2 = t if rnd.random() < .5 else rnd.choice([x for x in (1, 2, 3, 4) if x != t])
                        add(U[0], {"type": "tf", "q": T("「") + z + T("」是") + TONEN[t2] + T("。"), "answer": t2 == t,
                                   "explain": f"{z} 是{TONEN[t]}。"}, trap=t2 != t)
                    if stat.get(U[0], {}).get("fill", 0) < 6 and t != 1:
                        ch = list(dict.fromkeys([z] + [fmt(b, x) for x in (1, 2, 3, 4, 5) if x != t]))[:4]
                        rnd.shuffle(ch)
                        add(U[0], {"type": "fill", "q": T("「") + b + T("」加上") + TONEN[t] + T("，要寫成（　）。"), "answer": z, "chips": ch,
                                   "explain": f"{TONEN[t]}寫成 {z}。" + ("輕聲的點寫在最前面。" if t == 5 else "")}, trap=t == 5)
                    # 拼音
                    n = len(b)
                    if n in (2, 3):
                        u = U[1] if n == 2 else U[2]
                        parts = "＋".join(b)
                        wrong = [fmt(b[:i] + y + b[i + 1:], t) for i, x in enumerate(b) for y in LOOK.get(x, "")]
                        wrong = [x for x in dict.fromkeys(wrong) if x not in sylls or True][:6]
                        rnd.shuffle(wrong)
                        if len(wrong) >= 3 and stat.get(u, {}).get("choice", 0) < 14:
                            add(u, {"type": "choice", "q": T("「") + parts + TONEK[t] + T("」拼起來是哪一個？") if t != 5 else T("「") + "˙" + parts + T("」拼起來是哪一個？"),
                                    "choices": [z] + wrong[:3], "answer": z, "explain": f"{parts} 拼成 {z}。注意形狀很像的符號。"}, trap=True)
                        if stat.get(u, {}).get("tf", 0) < 8:
                            # 題目的拼法要帶聲調，和右邊的答案一致（ㄉ＋ㄨ＋ㄛ＋ˇ＝ㄉㄨㄛˇ）
                            pt = ("˙" if t == 5 else "") + parts + (TONEK[t] if t in (2, 3, 4) else "")
                            r0 = rnd.random()
                            if r0 < .5 or not wrong:
                                shown, why = z, f"{pt} 拼成 {z}，正確。"
                            elif r0 < .75:
                                t2 = rnd.choice([x for x in (1, 2, 3, 4, 5) if x != t])
                                shown, why = fmt(b, t2), f"{pt} 是{TONEN[t]}，拼成 {z}，不是{TONEN[t2]}的 {fmt(b, t2)}。"
                            else:
                                shown, why = wrong[0], f"{pt} 拼成 {z}，不是 {wrong[0]}，要看清楚形狀很像的符號。"
                            assert (shown == z) == (parse(shown) == (b, t))
                            add(u, {"type": "tf", "q": T("「") + pt + T("」拼起來是「") + shown + T("」。"), "answer": shown == z,
                                    "explain": why}, trap=shown != z)
                        if stat.get(u, {}).get("fill", 0) < 7:
                            i = rnd.randrange(n)
                            miss = b[i]
                            opts = list(dict.fromkeys([miss] + list(LOOK.get(miss, "")) + rnd.sample(sorted(INIT | MED | FIN), 6)))
                            opts = [miss] + [o for o in opts if o != miss][:3]
                            rnd.shuffle(opts)
                            q = "＋".join(b[:i] + "（　）" + b[i + 1:])
                            add(u, {"type": "fill", "q": T("") + q + "＝" + b + T("，空格要填哪個符號？"), "answer": miss, "chips": opts,
                                    "explain": f"{'＋'.join(b)}＝{b}。"}, trap=bool(LOOK.get(miss)))
                    # 符號分類
                    u = U[3]
                    if stat.get(u, {}).get("fill", 0) < 7 and n >= 2:
                        add(u, {"type": "fill", "q": T("「") + z + T("」用了（　）個注音符號（調號不算）。"), "answer": str(n),
                                "explain": f"{z} 由 {'、'.join(b)} 組成，共 {n} 個。"}, trap=t == 5)
                kinds = [("聲母", INIT), ("介音", MED), ("韻母", FIN)]
                for k in range(16):
                    nm, st = kinds[k % 3]
                    others = [x for x in INIT | MED | FIN if x not in st]
                    a = rnd.choice(sorted(st))
                    ch = [a] + rnd.sample(sorted(others), 3)
                    add(U[3], {"type": "choice", "q": T("下面哪一個是") + nm + T("？"), "choices": ch, "answer": a,
                               "explain": f"{a} 是{nm}。聲母是 ㄅ～ㄙ，介音是 ㄧ、ㄨ、ㄩ，其他是韻母。"}, trap=nm == "介音")
                for k in range(10):
                    nm, st = kinds[k % 3]
                    x = rnd.choice(sorted(INIT | MED | FIN))
                    ans = x in st
                    add(U[3], {"type": "tf", "q": T("「") + x + T("」是") + nm + T("。"), "answer": ans,
                               "explain": f"{x} 是" + ("聲母" if x in INIT else "介音" if x in MED else "韻母") + "。"}, trap=not ans)

            # ---------- 各課 ----------
            sents = D.get("sentences") or []
            for l in ls:
                u = uname(l)
                units.append(u)
                cs = [c for c in l["chars"] if c in info]
                ws = [w for w in l["words"] if 2 <= len(w) <= 4 and all(c in info for c in w)]
                allw = list(dict.fromkeys(ws + [w for w in wzy if 2 <= len(w) <= 4 and all(c in info for c in w)]))
                rnd.shuffle(cs)
                for k, c in enumerate(cs):
                    inw = [w for w in ws if c in w] or [w for w in allw if c in w]
                    w = rnd.choice(inw) if inw else None
                    i = w.index(c) if w else 0
                    z = reading(w, l)[i] if w else (l["zy"].get(c) or info[c][0])
                    ctx = f"「{w}」的「{c}」" if w else f"「{c}」"
                    # 選擇：注音
                    vs = zy_variants(c, z)
                    if len(vs) == 3:
                        add(u, {"type": "choice", "q": ("「" + w + "」" + T("的") + "「" + c + "」" + T("，正確的注音是哪一個？")) if w else ("「" + c + "」" + T("的正確注音是哪一個？")),
                                "choices": [z] + vs, "answer": z,
                                "explain": f"{ctx}念 {z}。" + ("注意聲調。" if any(parse(v)[0] == parse(z)[0] for v in vs) else "")}, trap=True)
                    # 選擇或填充：看注音選字
                    if w:
                        shown = w[:i] + f"（{z}）" + w[i + 1:]
                        body = T(w[:i]) + f"（{z}）" + T(w[i + 1:])
                    else:
                        shown = body = f"（{z}）"
                    ds, trap = homo(c, z, w, i)
                    if len(ds) == 3:
                        if k % 2 == 0:
                            add(u, {"type": "choice", "q": T("看注音，選出正確的國字：") + body, "choices": [c] + ds, "answer": c,
                                    "explain": f"{shown.replace(f'（{z}）', c)}，{z} 是「{c}」。" + ("其他選項是讀音相近的字，要看清楚聲調和字義。" if trap else "")}, trap=trap)
                        else:
                            chips = [c] + ds
                            rnd.shuffle(chips)
                            add(u, {"type": "fill", "q": T("看注音寫國字：") + body, "answer": c, "chips": chips,
                                    "explain": f"「{w or c}」的 {z} 寫作「{c}」。" + ("小心同音字。" if trap else "")}, trap=trap)
                    # 部首（教育部和課本歸部不同、或無法確定的字不出）
                    r = info[c][1]
                    if len(info[c]) == 3 and r != c:
                        others = [info[x][1] for x in pool if info[x][1] not in (r, x) and len(info[x]) == 3]
                        others = list(dict.fromkeys(others)); rnd.shuffle(others)
                        if k % 3 == 0 and len(others) >= 3:
                            add(u, {"type": "choice", "q": T("「") + c + T("」的部首是哪一個？"), "choices": [radl(r)] + [radl(x) for x in others[:3]],
                                    "answer": radl(r), "explain": f"「{c}」的部首是「{radl(r)}」。"})
                        else:
                            right = rnd.random() < .5 or not others
                            shown_r = r if right else others[0]
                            add(u, {"type": "tf", "q": T("「") + c + T("」的部首是「") + T(radl(shown_r)) + T("」。"), "answer": right,
                                    "explain": f"「{c}」的部首是「{radl(r)}」" + ("。" if right else f"，不是「{radl(shown_r)}」。")}, trap=not right)
                    # 填充：筆畫
                    if k % 2 == 1 or len(cs) < 10:
                        add(u, {"type": "fill", "q": T("「") + c + T("」一共有（　）畫。"), "answer": str(info[c][2]),
                                "explain": f"「{c}」共 {info[c][2]} 畫。" + ("部首的筆畫要算清楚。" if info[c][1] in RAD_VAR else "")}, trap=info[c][1] in RAD_VAR)
                # 語詞
                lw = ws or allw[:4]
                for w in lw:
                    r = reading(w, l)
                    # 是非：注音
                    if rnd.random() < .5:
                        add(u, {"type": "tf", "q": T("「") + w + T("」的注音是「") + " ".join(r) + T("」。"), "answer": True,
                                "explain": f"{w}：{' '.join(r)}。"})
                    else:
                        j = rnd.randrange(len(w))
                        vs = zy_variants(w[j], r[j])
                        if vs:
                            r2 = r[:j] + [vs[0]] + r[j + 1:]
                            add(u, {"type": "tf", "q": T("「") + w + T("」的注音是「") + " ".join(r2) + T("」。"), "answer": False,
                                    "explain": f"「{w[j]}」要念 {r[j]}，不是 {vs[0]}。正確是 {' '.join(r)}。"}, trap=True)
                    # 用字正確／錯字
                    fakes = []
                    for j in rnd.sample(range(len(w)), len(w)):
                        if w[j] not in info:
                            continue
                        ds, _ = homo(w[j], reading(w, l)[j], w, j, n=2)
                        b0 = parse(reading(w, l)[j])[0]
                        # 錯字只用同音（不同調也算）的字，才像孩子真的會寫錯的樣子
                        ds = [d for d in ds if any(parse(x)[0] == b0 for x in valid(d))]
                        for d in ds:
                            f = w[:j] + d + w[j + 1:]
                            if f not in realw and f not in fakes:
                                fakes.append(f)
                        if len(fakes) >= 3:
                            break
                    if fakes:
                        if rnd.random() < .5:
                            add(u, {"type": "tf", "q": T("「") + fakes[0] + T("」這個語詞的用字完全正確。"), "answer": False,
                                    "explain": f"應該寫「{w}」，「{fakes[0]}」有錯字。"}, trap=True)
                        else:
                            add(u, {"type": "tf", "q": T("「") + w + T("」這個語詞的用字完全正確。"), "answer": True,
                                    "explain": f"「{w}」用字正確。"})
                    others = [x for x in lw if x != w]
                    if len(fakes) >= 3:
                        add(u, {"type": "choice", "q": T("下面哪一個語詞的用字完全正確？"), "choices": [w] + fakes[:3], "answer": w,
                                "explain": f"正確的是「{w}」，其他選項有同音或形近的錯字。"}, trap=True)
                    elif len(fakes) >= 1 and len(others) >= 3:
                        add(u, {"type": "choice", "q": T("下面哪一個語詞有錯字？"), "choices": [fakes[0]] + rnd.sample(others, 3), "answer": fakes[0],
                                "explain": f"「{fakes[0]}」應該寫「{w}」。"}, trap=True)
                # 注音不正確的是哪一個
                for _ in range(2):
                    if len(lw) < 4:
                        break
                    pick = rnd.sample(lw, 4)
                    bad = pick[0]; j = rnd.randrange(len(bad))
                    vs = zy_variants(bad[j], reading(bad, l)[j])
                    if not vs:
                        continue
                    rb = reading(bad, l)[:]; rb[j] = vs[0]
                    ch = [f"{bad} {' '.join(rb)}"] + [f"{x} {' '.join(reading(x, l))}" for x in pick[1:]]
                    add(u, {"type": "choice", "q": T("下面哪一個語詞的注音「不正確」？"), "choices": ch, "answer": ch[0],
                            "explain": f"「{bad}」應該是 {' '.join(reading(bad, l))}。"}, trap=True)
                # 選詞填空（三年級以上）
                items = (l.get("items") or {}).get("fill", [])
                allans = [x[1] for ll in ls for x in (ll.get("items") or {}).get("fill", [])]
                for s, a, *wrong in items:
                    extra = [x for x in allans if x not in [a] + wrong and x[0] != a[0]]
                    rnd.shuffle(extra)
                    blank = s.replace(f"[{a}]", "（　）")
                    if len(wrong) >= 2 and extra:
                        add(u, {"type": "choice", "q": "選出最適合填入（　）的語詞：" + blank, "choices": [a] + wrong[:2] + extra[:1], "answer": a,
                                "explain": s.replace("[", "「").replace("]", "」") + " 其他語詞字面很像，但意思不合。"}, trap=True)
                    chips = [a] + wrong[:2]; rnd.shuffle(chips)
                    add(u, {"type": "fill", "q": "在（　）裡填入最適合的語詞：" + blank, "answer": a, "chips": chips,
                            "explain": s.replace("[", "「").replace("]", "」")}, trap=True)
                # 一年級句子填空
                for s, a, wrong in sents:
                    if a in l["chars"]:
                        chips = [a] + list(wrong); rnd.shuffle(chips)
                        add(u, {"type": "fill", "q": T("選字填入句子：") + T(s.split("[")[0]) + "（　）" + T(s.split("]")[1]), "answer": a, "chips": chips,
                                "explain": f"{s.replace('[', '').replace(']', '')}"}, trap=True)
                # 題數不夠 25：認讀字、其他課語詞的注音再補
                extra_c = [c for c in l.get("readChars", []) if c in info]
                while sum(stat.get(u, {}).get(k, 0) for k in ("tf", "choice", "fill")) < 25 and extra_c:
                    c = extra_c.pop()
                    z = info[c][0]; vs = zy_variants(c, z)
                    if len(vs) == 3:
                        add(u, {"type": "choice", "q": T("「") + c + T("」的注音是哪一個？"), "choices": [z] + vs, "answer": z, "explain": f"「{c}」念 {z}。"}, trap=True)

            # ---------- 試卷 ----------
            label = f"{GN[g]}年級{PUBN[pub]}版"
            if g == 1:
                papers = [{"title": f"{label}・第一次月考（注音符號）", "units": zy_units, "count": 45},
                          {"title": f"{label}・第二次月考（課文生字）", "units": units, "count": 45},
                          {"title": f"{label}・全冊總複習", "count": 50}]
            else:
                half = (len(ls) + 1) // 2
                a, b = ls[:half], ls[half:]
                papers = [{"title": f"{label}・第一次月考（第{a[0]['lessonNo']}～{a[-1]['lessonNo']}課）", "units": units[:half], "count": 45},
                          {"title": f"{label}・第二次月考（第{b[0]['lessonNo']}～{b[-1]['lessonNo']}課）", "units": units[half:], "count": 45},
                          {"title": f"{label}・全冊總複習", "count": 50}]
            report[(g, pub)] = stat
            out = {"grade": "國語 上學期", "papers": papers, "bank": bank}
            report.setdefault("files", {}).setdefault(g, {})[pub] = out
        json.dump(report["files"][g], open(f"game/exam/g{g}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    # 摘要
    lines = []
    for (g, pub), stat in [(k, v) for k, v in report.items() if k != "files"]:
        tot = {k: sum(s[k] for s in stat.values()) for k in ("tf", "choice", "fill", "trap")}
        n = tot["tf"] + tot["choice"] + tot["fill"]
        mn = min(s["tf"] + s["choice"] + s["fill"] for s in stat.values())
        lines.append(f"{g}年級 {PUBN[pub]}：{len(stat)} 個單元，{n} 題（是非 {tot['tf']}／選擇 {tot['choice']}／填充 {tot['fill']}），每單元最少 {mn} 題，陷阱題 {round(tot['trap'] / n * 100)}%")
    open("exam_stats.json", "w", encoding="utf-8").write(json.dumps({f"{g}-{p}": s for (g, p), s in [(k, v) for k, v in report.items() if k != "files"]}, ensure_ascii=False, indent=1))
    print("\n".join(lines))


def base_of(z):
    return parse(z)[0]


if __name__ == "__main__":
    main()
