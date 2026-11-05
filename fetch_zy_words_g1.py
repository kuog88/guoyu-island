"""一年級全文注音：把 make_zy_g1.py 斷出來的詞（zy_g1_words.txt）到教育百科查最新讀音，存成 word_zy_pedia_g1.json。
已經查過的會略過。查不到（教育百科沒收）的記成 null，改用辭典檔的讀音。"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")
from fetch_info_all import word_info

OUT = "word_zy_pedia_g1.json"
have = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
words = [w for w in open("zy_g1_words.txt", encoding="utf-8").read().split() if w not in have]
with ThreadPoolExecutor(6) as ex:
    for w, r in ex.map(word_info, words):
        have[w] = r
json.dump(dict(sorted(have.items())), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("查了", len(words), "個詞，查不到", sum(1 for v in have.values() if not v))
