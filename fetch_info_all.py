"""從教育百科字典抓 1～6 年級 115 上所有用到的字和語詞的注音，以及單字的部首、總筆畫。

輸出：
- char_info_all.json：{字: {zhuyin, radical, strokes}}（注音是字典第一個讀音）
- word_zy.json：{語詞: [每個字的注音]}（語詞第一個讀音，用來決定多音字在課文裡的念法）
可以重複執行，已經抓過的會略過；加 --all 全部重抓。
字典頁面的輕聲標成 tone-0（不是 tone-5），要當輕聲處理。
"""
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import sys

import requests

TONE = {"1": "", "2": "ˊ", "3": "ˇ", "4": "ˋ"}
ITEM = re.compile(r'zhuyin-h-item tone-(\d)-\d">\s*<span class="top">(.*?)</span>\s*<span class="bottom">(.*?)</span>')
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0"


def page(title):
    for attempt in range(5):
        try:
            r = S.get("https://pedia.cloud.edu.tw/Entry/Detail", params={"title": title}, timeout=30)
            if r.ok:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(1.5 * (attempt + 1))
    return ""


def zy_items(html):
    """第一個 <label> 裡的注音，一個字一組"""
    m = re.search(r"<label>(.*?)</label>", html, re.S)
    out = []
    for tone, top, bottom in ITEM.findall(m.group(1) if m else ""):
        out.append(("˙" + bottom) if tone in ("0", "5") or top.strip() == "˙" else bottom + TONE.get(tone, ""))
    return out


def char_info(ch):
    html = page(ch)
    zys = zy_items(html)
    rad = re.search(r'<span class="field">部首</span>\s*<span class="value">\s*<a[^>]*>(.*?)</a>', html)
    st = re.search(r'<span class="field">總筆畫</span>\s*<span class="value"><strong>(\d+)</strong>', html)
    return ch, {"zhuyin": zys[0] if zys else None, "radical": rad.group(1) if rad else None,
                "strokes": int(st.group(1)) if st else None}


def word_info(w):
    zys = zy_items(page(w))
    return w, zys if len(zys) == len(w) else None


def main():
    lessons = json.load(open("lessons_115_1.json", encoding="utf-8"))
    chars, words = set(), set()
    for l in lessons:
        chars |= set(l["chars"]) | set(l["readChars"]) | set("".join(l["words"]))
        words |= {w for w in l["words"] if len(w) >= 2}
    cinfo = json.load(open("char_info_all.json", encoding="utf-8")) if os.path.exists("char_info_all.json") else {}
    winfo = json.load(open("word_zy.json", encoding="utf-8")) if os.path.exists("word_zy.json") else {}
    redo = "--all" in sys.argv
    todo_c = sorted(c for c in chars if redo or c not in cinfo or not cinfo[c].get("zhuyin"))
    todo_w = sorted(w for w in words if redo or w not in winfo)
    print("chars", len(chars), "todo", len(todo_c), "| words", len(words), "todo", len(todo_w), flush=True)
    with ThreadPoolExecutor(5) as ex:
        for i, (c, v) in enumerate(ex.map(char_info, todo_c)):
            cinfo[c] = v if v["zhuyin"] else cinfo.get(c, v)  # 抓失敗時保留舊資料
            if i % 200 == 0:
                print("char", i, flush=True)
                json.dump(cinfo, open("char_info_all.json", "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(cinfo, open("char_info_all.json", "w", encoding="utf-8"), ensure_ascii=False)
        for i, (w, v) in enumerate(ex.map(word_info, todo_w)):
            winfo[w] = v if v else winfo.get(w)
            if i % 200 == 0:
                print("word", i, flush=True)
                json.dump(winfo, open("word_zy.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(winfo, open("word_zy.json", "w", encoding="utf-8"), ensure_ascii=False)
    bad_c = [c for c, v in cinfo.items() if c in chars and not (v["zhuyin"] and v["radical"])]
    bad_w = [w for w in words if not winfo.get(w)]
    print("missing char info", len(bad_c), "".join(bad_c[:80]))
    print("words without zhuyin", len(bad_w), "、".join(bad_w[:40]))


if __name__ == "__main__":
    main()
