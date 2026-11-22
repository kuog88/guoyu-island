"""向教育部《國字標準字體筆順學習網》2025 查每個字的筆畫數。
網頁 dictView.jsp?ID=<Unicode 十進位> 裡嵌著筆順動畫的 XML：
  anim：動畫的 <Stroke> 個數（實際寫幾筆，例如「社」7）
  meta：網頁標示的筆畫數（字典算法，礻算 5 畫，例如「社」8）
輸出 stroke_moe2025.json：{字: [anim, meta]}；網站沒有收的字是 null。已查過的會略過。"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
sys.stdout.reconfigure(encoding="utf-8")
OUT = "stroke_moe2025.json"
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"


def one(c):
    for k in range(4):
        try:
            r = S.get("https://stroke-order.learningweb.moe.edu.tw/dictView.jsp", params={"ID": ord(c), "la": 0}, timeout=30)
            if r.ok:
                anim = r.text.count("<Stroke>")
                m = re.search(r'name="Description" content="' + re.escape(c) + r',(\d+) 畫', r.text)
                if not anim and not m:
                    return c, None
                return c, [anim or None, int(m.group(1)) if m else None]
        except requests.RequestException:
            pass
        time.sleep(1 + k)
    return c, "error"


have = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
have = {c: v for c, v in have.items() if v != "error"}
chars = set()
for g in range(1, 7):
    chars |= set(json.load(open(f"game/data/g{g}.json", encoding="utf-8"))["info"])
todo = sorted(c for c in chars if c not in have)
with ThreadPoolExecutor(6) as ex:
    for i, (c, n) in enumerate(ex.map(one, todo)):
        have[c] = n
        if i % 300 == 0:
            json.dump(have, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(dict(sorted(have.items())), open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print("查了", len(todo), "字；沒有收錄", sum(1 for v in have.values() if v is None), "；錯誤", sum(1 for v in have.values() if v == "error"))
