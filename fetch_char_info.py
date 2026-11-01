"""從教育百科字典抓單字的注音（第一個讀音）、部首、總筆畫，輸出 char_info_g1.json。

用法：python fetch_char_info.py 1
只抓指定年級 115 上課文用到的字（生字、認讀字、語詞裡的字）。
多音字只取字典第一個讀音，要在 OVERRIDE 手動指定課文用的讀音。
"""
import json
import re
import sys
import time

import requests

TONE = {"1": "", "2": "ˊ", "3": "ˇ", "4": "ˋ"}
# 多音字：一年級課文常用的讀音
OVERRIDE = {
    "的": "˙ㄉㄜ", "了": "˙ㄌㄜ", "呢": "˙ㄋㄜ", "嗎": "˙ㄇㄚ", "麼": "˙ㄇㄜ", "個": "ㄍㄜˋ",
    "子": "ㄗˇ", "長": "ㄔㄤˊ", "和": "ㄏㄢˋ", "好": "ㄏㄠˇ", "都": "ㄉㄡ", "地": "ㄉㄧˋ",
    "少": "ㄕㄠˇ", "什": "ㄕㄣˊ", "啊": "ㄚ", "哪": "ㄋㄚˇ", "朵": "ㄉㄨㄛˇ", "尾": "ㄨㄟˇ",
    "為": "ㄨㄟˋ", "那": "ㄋㄚˋ", "這": "ㄓㄜˋ", "們": "˙ㄇㄣ", "裡": "ㄌㄧˇ", "上": "ㄕㄤˋ",
    "下": "ㄒㄧㄚˋ", "大": "ㄉㄚˋ", "小": "ㄒㄧㄠˇ", "家": "ㄐㄧㄚ", "看": "ㄎㄢˋ", "要": "ㄧㄠˋ",
    "說": "ㄕㄨㄛ", "空": "ㄎㄨㄥ", "分": "ㄈㄣ", "千": "ㄑㄧㄢ", "相": "ㄒㄧㄤ", "像": "ㄒㄧㄤˋ",
    "吐": "ㄊㄨˇ", "把": "ㄅㄚˇ", "外": "ㄨㄞˋ", "巴": "ㄅㄚ", "得": "˙ㄉㄜ", "著": "˙ㄓㄜ",
    "沒": "ㄇㄟˊ",
}
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0"


def info(ch):
    for attempt in range(4):
        r = S.get("https://pedia.cloud.edu.tw/Entry/Detail", params={"title": ch}, timeout=30)
        if r.ok and "zhuyin-h-item" in r.text:
            break
        time.sleep(1 + attempt)
    html = r.text
    m = re.search(r'zhuyin-h-item tone-(\d)-\d">\s*<span class="top">(.*?)</span>\s*<span class="bottom">(.*?)</span>', html)
    zy = None
    if m:
        tone, top, bottom = m.groups()
        zy = ("˙" + bottom) if tone == "5" or top.strip() == "˙" else bottom + TONE.get(tone, "")
    rad = re.search(r'<span class="field">部首</span>\s*<span class="value">\s*<a[^>]*>(.*?)</a>', html)
    strokes = re.search(r'<span class="field">總筆畫</span>\s*<span class="value"><strong>(\d+)</strong>', html)
    return {"zhuyin": OVERRIDE.get(ch, zy), "dictZhuyin": zy,
            "radical": rad.group(1) if rad else None,
            "strokes": int(strokes.group(1)) if strokes else None}


def main():
    grade = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    lessons = [l for l in json.load(open("lessons_115_1.json", encoding="utf-8")) if l["grade"] == grade]
    chars = set()
    for l in lessons:
        chars |= set(l["chars"]) | set(l["readChars"]) | set("".join(l["words"]))
    out = {}
    for ch in sorted(chars):
        out[ch] = info(ch)
        print(ch, out[ch])
        time.sleep(0.2)
    json.dump(out, open(f"char_info_g{grade}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
