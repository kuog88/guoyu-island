"""一年級全文注音：依教育部《重編國語辭典修訂本》（g0v/moedict-data）的詞語讀音標注多音字與輕聲。

做法和遊戲裡一樣：由左到右找最長的詞，詞典有收的詞就用詞的讀音，沒有就用單字讀音。
人工校對的結果放在 zy_fix_g1.json：
  phrases：詞或片語 → 讀音（空白分隔），優先於辭典
  chars：單字預設讀音（例如句尾的「了」念輕聲）
輸出：
  zy_g1.json            給 build_game.py 放進 data/g1.json（只放和單字預設不同的詞）
  zy_g1_review.txt      逐句列出讀音，多音字標 *，給人工校對
需要：dict-revised.json.xz（https://github.com/g0v/moedict-data）放在 MOE_DICT 指定的位置
"""
import json, lzma, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
MOE_DICT = os.environ.get("MOE_DICT", "fonts_src/dict-revised.json.xz")
HAN = re.compile(r"[㐀-鿿]")
TONE = "ˊˇˋ˙"
MAXW = 6


def norm(z):
    # 辭典用全形空白分隔，輕聲符號放在最前面
    return z.replace("　", " ").strip()


def load_dict():
    d = json.loads(lzma.open(MOE_DICT).read().decode("utf-8"))
    words, chars = {}, {}
    for e in d:
        t = e.get("title", "")
        if not t or not all(HAN.match(c) for c in t):
            continue
        rs = []
        for h in e.get("heteronyms", []):
            b = h.get("bopomofo")
            if not b:
                continue
            b = re.sub(r"（[^）]*）", " ", b)       # （語音）（讀音）等標記
            b = re.sub(r"[^ㄅ-ㄩˊˇˋ˙ ]", " ", norm(b))
            syl = b.split()
            if len(syl) >= len(t):
                rs.append(syl[:len(t)])
        if not rs:
            continue
        if len(t) == 1:
            chars.setdefault(t, [])
            for r in rs:
                if r[0] not in chars[t]:
                    chars[t].append(r[0])
        elif len(t) <= MAXW:
            words.setdefault(t, [])
            for r in rs:
                if r not in words[t]:
                    words[t].append(r)
    # 單字最常見的讀音：看這個字在辭典詞語裡各個讀音出現幾次
    freq = {}
    for w, rs in words.items():
        for i, c in enumerate(w):
            f = freq.setdefault(c, {})
            f[rs[0][i]] = f.get(rs[0][i], 0) + 1
    common = {c: max(f, key=f.get) for c, f in freq.items()}
    for c, rs in chars.items():
        common.setdefault(c, rs[0])
    return words, chars, common


def texts_from_js(path):
    src = open(path, encoding="utf-8").read()
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"(?m)^\s*//.*$", "", src)
    return re.findall(r"[㐀-鿿]+", src)


def collect_texts():
    g1 = json.load(open("game/data/g1.json", encoding="utf-8"))
    out = []
    out += texts_from_js("game_script.js")
    for l in g1["lessons"]:
        out.append(l["title"])
        out += l["words"]
    for s, ans, opts in g1["sentences"]:
        out.append(s.replace("[", "").replace("]", ""))
    return g1, [t for t in dict.fromkeys(out) if HAN.search(t)]


def main():
    words, chars, common = load_dict()
    call = json.load(open("char_info_all.json", encoding="utf-8"))
    fix = json.load(open("zy_fix_g1.json", encoding="utf-8")) if os.path.exists("zy_fix_g1.json") else {"phrases": {}, "chars": {}}
    g1, texts = collect_texts()
    info = g1["info"]
    # 單字預設：人工指定 > 遊戲原本的字卡讀音 > 教育百科 > 辭典詞語裡最常見的讀音
    # 部首題的選項、字卡上的部首也會顯示，一起查讀音
    rads = {x for v in info.values() for x in v[1:2] + v[3:4] if isinstance(x, str)}
    allc = sorted({c for t in texts for c in t if HAN.match(c)} | set(info) | {c for r in rads for c in r if HAN.match(c)})
    cdef = {}
    for c in allc:
        z = fix["chars"].get(c) or (info[c][0] if c in info else None) or (call.get(c) or {}).get("zhuyin") or common.get(c)
        if z:
            cdef[c] = z
    phr = {w: r[0] for w, r in words.items()}
    # 教育百科（教育部最新審訂音）查到的詞語讀音優先於辭典檔（fetch_zy_words_g1.py）
    pedia = json.load(open("word_zy_pedia_g1.json", encoding="utf-8")) if os.path.exists("word_zy_pedia_g1.json") else {}
    for w, r in pedia.items():
        if r:
            phr[w] = r
    # 課文語詞用教育百科的讀音（遊戲裡也是這個優先）
    for w, r in g1["wordZy"].items():
        phr[w] = r
    for w, z in fix["phrases"].items():
        if z is None:          # 辭典裡有、但在句子裡會斷錯的詞，例如「正確的是」的「的是」
            phr.pop(w, None)
            continue
        phr[w] = z.split()
        assert len(phr[w]) == len(w), (w, z)
    lesson_words = set(g1["wordZy"])

    used, review, missing, matched = {}, [], set(), set()
    for t in texts:
        i, segs = 0, []
        while i < len(t):
            for n in range(min(MAXW, len(t) - i), 1, -1):
                w = t[i:i + n]
                if w in phr:
                    matched.add(w)
                    segs.append((w, phr[w]))
                    if [cdef.get(c) for c in w] != phr[w] or w in fix["phrases"]:
                        used[w] = " ".join(phr[w])
                    i += n
                    break
            else:
                c = t[i]
                if c not in cdef:
                    missing.add(c)
                segs.append((c, [cdef.get(c, "?")]))
                i += 1
        line = []
        for w, r in segs:
            poly = any(len(chars.get(c, [])) > 1 for c in w)
            multi = len(w) > 1 and len(words.get(w, [])) > 1 and w not in fix["phrases"]
            line.append(("*" if poly else "") + ("!" if multi else "") + w + "(" + " ".join(r) + ")")
        review.append(t + "\t" + " ".join(line))
    # 課文語詞（教育百科的讀音）一律保留，遊戲裡已經用它標注
    for w in lesson_words:
        used.pop(w, None)
    # 遊戲裡只帶 used + 課文語詞，用同樣的斷詞再跑一次，確認結果一樣
    small = {**{w: z.split() for w, z in used.items()}, **g1["wordZy"]}
    def seg(t, d):
        i, out = 0, []
        while i < len(t):
            for n in range(min(MAXW, len(t) - i), 1, -1):
                if t[i:i + n] in d:
                    out += d[t[i:i + n]]; i += n; break
            else:
                out.append(cdef.get(t[i], "?")); i += 1
        return out
    diff = [t for t in texts if seg(t, small) != seg(t, phr)]
    if diff:
        print("遊戲裡的斷詞和校對表不同：", diff)
    block = sorted(w for w, z in fix["phrases"].items() if z is None)
    json.dump({"phrases": dict(sorted(used.items())), "block": block, "chars": {c: z for c, z in cdef.items() if c not in info or z != info[c][0]}},
              open("zy_g1.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    open("zy_g1_words.txt", "w", encoding="utf-8").write(" ".join(sorted(matched)) + " ")
    open("zy_g1_review.txt", "w", encoding="utf-8").write("\n".join(review) + "\n")
    polyc = sorted(c for c in allc if len(chars.get(c, [])) > 1)
    print("文字段數", len(texts), "用到的字", len(allc), "多音字", len(polyc), "詞表", len(used), "缺讀音", "".join(sorted(missing)))
    print("多音字：", "".join(polyc))


if __name__ == "__main__":
    main()
