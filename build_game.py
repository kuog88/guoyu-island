"""產生闖關遊戲：game/index.html、game/data/g1～g6.json、game/strokes/g1.json。

資料來源：
- lessons_115_1.json：各版本、各年級每課的生字、認讀字、語詞（scrape_lessons.py）
- char_info_all.json、word_zy.json：注音、部首、筆畫，語詞的注音（fetch_info_all.py）
- char_info_g1.json：一年級的注音（含手動校正的多音字）
- stroke_count.json：教育部筆順網的筆畫數（fetch_stroke_count.py）
- radical_alt.json：教育部字典和康熙字典歸部不同的字（make_radical_alt.py）
- sentences_g1.txt：一年級句子填空（自編）
- strokes_g1.json：一年級筆順（fetch_strokes.py）
"""
import json
import os
import re

CN = "零一二三四五六七八九十"
# 教育百科資料裡的錯字
TITLE_FIX = {"為梨花撐傘用": "為梨花撐傘", "寧靜的意樂會": "寧靜的音樂會"}


def cn2int(s):
    if not s:
        return 0
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + CN.index(s[1])
    if "十" in s:
        a, b = s.split("十")
        return CN.index(a) * 10 + (CN.index(b) if b else 0)
    return CN.index(s)


def parse_reading(path):
    """閱讀短文：@ id | 標題、下一行短文、? 題目 | 正確答案 | 錯誤 | 錯誤"""
    out, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            lid, title = [x.strip() for x in line[1:].split("|")]
            cur = out[lid] = {"title": title, "text": "", "qs": []}
        elif line.startswith("?"):
            parts = [x.strip() for x in line[1:].split("|")]
            assert len(parts) == 4, line
            cur["qs"].append(parts)
        else:
            cur["text"] += line
    for lid, r in out.items():
        assert r["text"] and len(r["qs"]) == 3, lid
    return out


BANK_KEYS = {"成語": "idiom", "關聯詞": "conn", "量詞": "measure", "標點": "punct", "句意": "meaning", "換句話說": "rewrite",
             "修辭": "rhet", "句子變身": "transform"}


def parse_bank(path):
    """年級共用題庫：[分類] 下每行一題，欄位用 | 分隔"""
    out, key = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"\[(.+)\]$", line)
        if m and m.group(1) in BANK_KEYS:
            key = BANK_KEYS[m.group(1)]
            out[key] = []
            continue
        parts = [x.strip() for x in line.split("|")]
        out[key].append(parts)
    for k, rows in out.items():
        for r in rows:
            need = {"idiom": 5, "conn": 5, "measure": 3, "punct": 4, "meaning": 4, "rewrite": 4, "rhet": 4, "transform": 5}[k]
            assert len(r) >= need, (k, r)
            if k in ("idiom", "measure"):
                assert "[" in r[2 if k == "idiom" else 0], (k, r)
    return out


def parse_lesson_items(path):
    """各課題目：@ 課 id，W 選詞填空，B 句子積木"""
    out, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            cur = out[line[1:].strip()] = {"fill": [], "build": []}
        elif line.startswith("W "):
            parts = [x.strip() for x in line[2:].split("|")]
            m = re.search(r"\[(.+?)\]", parts[0])
            assert m and len(parts) == 3, line
            cur["fill"].append([parts[0], m.group(1), parts[1], parts[2]])
        elif line.startswith("B "):
            cur["build"].append([[t.strip() for t in alt.split("/")] for alt in line[2:].split("||")])
    return out


def strokes_of(c, dict_n, moe_count):
    """字卡的筆畫數要和孩子實際寫的一樣。字典用部首原形計算（礻算 5 畫、衤算 6 畫），
    筆順網比字典少 1 畫的就用筆順網的；筆順資料比字典多的是資料本身有誤，仍用字典。"""
    n = moe_count.get(c)
    return n if n and dict_n and n == dict_n - 1 else (dict_n or n or 0)


def main():
    lessons = json.load(open("lessons_115_1.json", encoding="utf-8"))
    cinfo = json.load(open("char_info_all.json", encoding="utf-8"))
    wzy = json.load(open("word_zy.json", encoding="utf-8"))
    g1fix = json.load(open("char_info_g1.json", encoding="utf-8"))
    moe_count = json.load(open("stroke_count.json", encoding="utf-8"))
    rad_alt = json.load(open("radical_alt.json", encoding="utf-8"))
    os.makedirs("game/data", exist_ok=True)
    os.makedirs("game/strokes", exist_ok=True)
    stats = {}
    for g in range(1, 7):
        ls = [l for l in lessons if l["grade"] == g]
        chars = set()
        for l in ls:
            chars |= set(l["chars"]) | set(l["readChars"]) | set("".join(l["words"]))
        info = {}
        for c in sorted(chars):
            v = cinfo.get(c) or {}
            z = (g1fix.get(c) or {}).get("zhuyin") if g == 1 else None
            z = z or v.get("zhuyin")
            if z and v.get("radical"):
                info[c] = [z, v["radical"], strokes_of(c, v.get("strokes"), moe_count)]
                if c in rad_alt:
                    info[c].append(rad_alt[c])
        out_lessons, wz = [], {}
        for l in ls:
            words = [w for w in l["words"] if all(c in info for c in w)]
            # 多音字：用這一課語詞裡的讀音
            zy = {}
            for w in words:
                r = wzy.get(w)
                if not r or len(r) != len(w):
                    continue
                wz[w] = r
                for i, c in enumerate(w):
                    if c in l["chars"] and c not in zy and r[i] != info[c][0] and not r[i].startswith("˙"):
                        zy[c] = r[i]
            out_lessons.append({"id": l["id"], "pub": l["pub"], "order": l["order"], "lessonNo": cn2int(l["lesson"]),
                                "title": TITLE_FIX.get(l["title"], l["title"]), "chars": [c for c in l["chars"] if c in info],
                                "readChars": [c for c in l["readChars"] if c in info], "words": words, "zy": zy})
        data = {"grade": g, "lessons": out_lessons, "info": info, "wordZy": wz}
        # 三年級以上的句式題庫（年級共用 + 各版本各課）
        if os.path.exists(f"bank_g{g}.txt"):
            data["bank"] = parse_bank(f"bank_g{g}.txt")
            for pub in ("nani", "kang", "han"):
                p = f"lessons_g{g}_{pub}.txt"
                if not os.path.exists(p):
                    continue
                items = parse_lesson_items(p)
                for l in out_lessons:
                    if l["pub"] == pub:
                        if l["id"] not in items:
                            raise SystemExit(f"{p} 缺少 {l['id']}")
                        l["items"] = items[l["id"]]
        if os.path.exists(f"reading_g{g}.txt"):
            data["reading"] = parse_reading(f"reading_g{g}.txt")
            missing_r = [l["id"] for l in ls if l["id"] not in data["reading"]]
            if missing_r:
                raise SystemExit(f"reading_g{g}.txt 缺少：{missing_r}")
        if g == 1:
            sents = []
            for line in open("sentences_g1.txt", encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#"):
                    s, d = line.split("|")
                    sents.append([s, re.search(r"\[(.)\]", s).group(1), list(d)])
            data["sentences"] = sents
            report = json.load(open("strokes_g1_report.json", encoding="utf-8"))
            skip = {x[0] for x in report["countMismatch"]}
            strokes = {c: v for c, v in json.load(open("strokes_g1.json", encoding="utf-8")).items() if c not in skip}
            json.dump(strokes, open("game/strokes/g1.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        json.dump(data, open(f"game/data/g{g}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        missing = sorted({c for l in ls for c in l["chars"] if c not in info})
        stats[g] = {"lessons": len(ls), "chars": len(info), "words": len(wz), "zyFix": sum(len(x["zy"]) for x in out_lessons), "missing": "".join(missing)}
    import time
    script = open("game_script.js", encoding="utf-8").read().replace("__BUILD__", time.strftime("%Y%m%d%H%M%S"))
    html = open("game_template.html", encoding="utf-8").read().replace("__SCRIPT__", script)
    open("game/index.html", "w", encoding="utf-8").write(html)
    for g, s in stats.items():
        print(g, s)


if __name__ == "__main__":
    main()
