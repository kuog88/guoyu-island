"""從教育百科「生字詞彙表」抓 115 學年度上學期國語三版本各課的生字、認讀字、語詞，輸出 lessons.json。"""
import json
import re
import sys
import time
from html import unescape

import requests

BASE = "https://pedia.cloud.edu.tw"
PRESSES = {"南一版": "nani", "康軒版": "kang", "翰林版": "han"}
# 用法：python scrape_lessons.py 115_1 lessons_115_1.json
YEAR = sys.argv[1] if len(sys.argv) > 1 else "115_1"
OUT = sys.argv[2] if len(sys.argv) > 2 else "lessons.json"
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0"


def get(url, params=None):
    for attempt in range(4):
        r = S.get(url, params=params, timeout=30)
        if r.ok and "<tbody" in r.text or r.ok and "textname" in r.text:
            return r.text
        time.sleep(1 + attempt)
    r.raise_for_status()
    return r.text


def list_lessons(press, grade):
    html = get(f"{BASE}/Bookmark/Textword",
               {"category": "國語", "year": YEAR, "degree": grade, "press": press})
    return re.findall(r'class="textname[^"]*" id="(\d+)">\s*<strong>(.*?)</strong>', html)


def lesson_items(text_id):
    html = get(f"{BASE}/Bookmark/TCollection", {"TextNameId": text_id})
    body = html.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    rows = re.findall(r'<td class="type[^"]*">\s*<span>(.*?)</span>.*?<td class="word_class[^"]*"><a[^>]*>(.*?)</a>', body, re.S)
    return [(unescape(t).strip(), unescape(w).strip()) for t, w in rows]


def main():
    out = []
    for press, code in PRESSES.items():
        for grade in range(1, 7):
            for idx, (tid, title) in enumerate(list_lessons(press, grade)):
                items = lesson_items(tid)
                m = re.match(r"第(.+?)課：(.*)", unescape(title))
                out.append({
                    "id": f"{code}-{grade}{'上' if YEAR.endswith('_1') else '下'}-{idx:02d}",
                    "year": YEAR,
                    "pub": code, "grade": grade, "order": idx,
                    "lesson": m.group(1) if m else None,
                    "title": (m.group(2) if m else unescape(title)).strip(),
                    "chars": [w for t, w in items if t == "生字"],
                    "readChars": [w for t, w in items if t == "認讀字"],
                    "words": [w for t, w in items if t == "語詞"],
                    "sourceId": tid,
                })
                print(code, grade, title, len(items))
                time.sleep(0.3)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
