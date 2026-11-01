"""抓教育部筆順網的筆畫數（g0v/zh-stroke-data，依教育部常用國字標準字體筆順），輸出 stroke_count.json：{字: 筆畫數}。

字典的「總筆畫」用部首原形計算（例如「礻」算 5 畫），和孩子實際寫的筆數不一定一樣，
所以字卡和描寫都改用這裡的筆畫數。可以重複執行，已經抓過的會略過。
"""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests

URL = "https://raw.githubusercontent.com/g0v/zh-stroke-data/master/json/{:x}.json"
S = requests.Session()


def count(ch):
    for attempt in range(4):
        try:
            r = S.get(URL.format(ord(ch)), timeout=30)
            if r.status_code == 404:
                return ch, None
            if r.ok:
                return ch, len(r.json())
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1 + attempt)
    return ch, None


def main():
    lessons = json.load(open("lessons_115_1.json", encoding="utf-8"))
    chars = set()
    for l in lessons:
        chars |= set(l["chars"]) | set(l["readChars"]) | set("".join(l["words"]))
    out = json.load(open("stroke_count.json", encoding="utf-8")) if os.path.exists("stroke_count.json") else {}
    todo = sorted(c for c in chars if c not in out)
    print("chars", len(chars), "todo", len(todo), flush=True)
    with ThreadPoolExecutor(8) as ex:
        for c, n in ex.map(count, todo):
            if n:
                out[c] = n
    json.dump(out, open("stroke_count.json", "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True)
    print("missing", "".join(sorted(c for c in chars if c not in out)))


if __name__ == "__main__":
    main()
