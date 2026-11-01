"""產生全年級單元製作成果總覽 game-overview.html（讀 game/data 下的各年級資料）。"""
import html
import json
import re

PUB = {"nani": "南一", "kang": "康軒", "han": "翰林"}
GN = "一二三四五六"
esc = html.escape
grades = [json.load(open(f"game/data/g{g}.json", encoding="utf-8")) for g in range(1, 7)]
strokes1 = json.load(open("game/strokes/g1.json", encoding="utf-8"))


def bank(d, l):
    """估計這一課可以出的題目數（每次進關卡會從裡面隨機抽 10～20 題）"""
    info = d["info"]
    words_all = {w for x in d["lessons"] for w in x["words"] if 2 <= len(w) <= 4}
    chars = l["chars"]
    lw = [w for w in l["words"] if 2 <= len(w) <= 4]
    b = {
        "射氣球": len(chars),
        "撈魚拼注音": len(chars),
        "修小橋": sum(1 for c in chars if any(c in w for w in words_all)),
        "部首": sum(1 for c in chars if info[c][1] != c),
        "錯字辨識": sum(1 for w in lw if any(c in chars for c in w)),
        "聽語詞": min(4, len(lw)) if len(lw) >= 3 else 0,
    }
    if d["grade"] == 1:
        b["描一描"] = sum(1 for c in chars if c in strokes1)
        b["句子填空"] = sum(1 for s in d.get("sentences", []) if s[1] in chars)
    return b


total = {"lessons": 0, "chars": 0, "words": 0}
sections = []
for d in grades:
    g = d["grade"]
    ls_all = d["lessons"]
    total["lessons"] += len(ls_all)
    total["chars"] += sum(len(l["chars"]) for l in ls_all)
    total["words"] += sum(len(l["words"]) for l in ls_all)
    reading = d.get("reading", {})
    if g == 1:
        stations = "打開寶箱 → 射氣球 4 題 → 描一描 2 題 → 撈魚拼注音 3 題 → 看注音修小橋 4 題 → 打魔王 5 題（句子填空為主）"
        ranges = "第一次月考：拼音群島（注音，三版本共用）／第二次月考：全部課文"
        extra = "拼音群島 5 座：一個符號、兩個符號、三個符號、聲調貝殼灘、注音大魔王，每座 10～12 題。"
    else:
        stations = "打開寶箱 → 射氣球 4 題 → 撈魚拼注音 3 題 → 看注音修小橋 5 題 → 打魔王 8 題（錯字辨識、部首、聽語詞）"
        ranges = "第一次月考：第 1～6 課／第二次月考：第 7～12 課"
        extra = ("閱讀加強區 3 座：第一次月考範圍（每次 4 篇、12 題）、第二次月考範圍（4 篇、12 題）、全冊閱讀挑戰（5 篇、15 題）。"
                 if reading else "")
    tables = []
    for p in PUB:
        ls = sorted([l for l in ls_all if l["pub"] == p], key=lambda l: l["order"])
        half = (len(ls) + 1) // 2
        rows = []
        for i, l in enumerate(ls):
            b = bank(d, l)
            label = "前導" if g == 1 and p == "nani" and l["order"] == 0 else f"第{l['lessonNo']}課"
            rng = "第二次" if g == 1 else ("第一次" if i < half else "第二次")
            r = reading.get(l["id"])
            rows.append(
                f"<tr><td class='n'>{label}</td><td class='t'>{esc(l['title'])}</td><td class='r'>{rng}</td>"
                f"<td class='c'>{len(l['chars'])}</td><td class='c'>{len(l['readChars']) or '—'}</td><td class='c'>{len(l['words'])}</td>"
                f"<td class='c b'>{sum(b.values())}</td>"
                f"<td class='mix'>{'、'.join(f'{k} {v}' for k, v in b.items() if v)}</td>"
                + (f"<td class='rd'>{esc(r['title'])}</td>" if reading else "") + "</tr>")
        head = ("<tr><th>課次</th><th>課名</th><th>月考</th><th class='c'>生字</th><th class='c'>認讀</th><th class='c'>語詞</th>"
                "<th class='c'>題庫</th><th>題庫組成</th>" + ("<th>閱讀短文</th>" if reading else "") + "</tr>")
        tables.append(f"<div class='tbl' data-p='{p}' {'hidden' if p != 'nani' else ''}><table><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table></div>")
    uniq_chars = len({c for l in ls_all for c in l["chars"]})
    sections.append(f'''<section id="g{g}" class="grade">
  <div class="ghead"><h2>{GN[g-1]}年級上學期</h2>
    <div class="facts"><span><b>{len(ls_all)}</b> 課</span><span><b>{uniq_chars}</b> 個不同生字</span><span><b>{sum(len(l["words"]) for l in ls_all)}</b> 個語詞</span>{f"<span><b>{len(reading)}</b> 篇閱讀</span>" if reading else ""}</div></div>
  <dl class="spec"><dt>月考範圍</dt><dd>{ranges}</dd><dt>每課關卡</dt><dd>{stations}</dd>{f"<dt>另外</dt><dd>{extra}</dd>" if extra else ""}</dl>
  <div class="vers" role="group" aria-label="{GN[g-1]}年級版本">{''.join(f"<button data-p='{p}' aria-pressed='{str(p=='nani').lower()}'>{n}</button>" for p, n in PUB.items())}</div>
  {''.join(tables)}
</section>''')

page = f'''<title>國語闖關島製作成果</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@600;900&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>
/* Layout: 單欄報告；年級導覽置頂，每個年級一段：規格摘要 + 版本切換的課次表 */
:root{{
  --bg:#f3f7f8; --surface:#ffffff; --fg:#1d2b33; --muted:#5b6b73; --line:#d4e3e7; --accent:#e5533d; --accent-bg:#fde9e5;
  --display:"Noto Serif TC","Songti TC",serif; --ui:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;
}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0f1c21;--surface:#172a31;--fg:#e7f1f3;--muted:#9fb4bb;--line:#2a454d;--accent:#ff7a63;--accent-bg:#3d1f1a;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#0f1c21;--surface:#172a31;--fg:#e7f1f3;--muted:#9fb4bb;--line:#2a454d;--accent:#ff7a63;--accent-bg:#3d1f1a;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:var(--ui);font-size:15px;line-height:1.65}}
body::before{{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}}
.wrap{{max-width:1100px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:36px}}
h1,h2{{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.3}}
h1{{font-size:clamp(26px,4vw,36px);font-weight:900}} h2{{font-size:24px;font-weight:900}}
p{{margin:0;max-width:72ch}}
.intro{{display:grid;gap:10px}}
.muted{{color:var(--muted);font-size:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
.stat{{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;display:grid}}
.stat b{{font-family:var(--display);font-size:28px;font-weight:900;font-variant-numeric:tabular-nums;line-height:1.2}}
.stat span{{font-size:13px;color:var(--muted)}}
nav{{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);padding-block:10px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px}}
nav a{{text-decoration:none;color:var(--fg);font-size:14px;padding:4px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface)}}
nav a:focus-visible,.vers button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.grade{{display:grid;gap:14px;scroll-margin-top:64px}}
.ghead{{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:baseline}}
.facts{{display:flex;flex-wrap:wrap;gap:6px 14px;color:var(--muted);font-size:14px}}
.facts b{{color:var(--fg);font-variant-numeric:tabular-nums}}
.spec{{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin:0;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 16px}}
.spec dt{{color:var(--muted);font-size:14px;white-space:nowrap}} .spec dd{{margin:0;min-width:0}}
.vers{{display:flex;gap:6px}}
.vers button{{font:inherit;font-size:14px;padding:4px 16px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer}}
.vers button[aria-pressed="true"]{{background:var(--accent);border-color:var(--accent);color:#fff}}
.tbl{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface)}}
table{{border-collapse:collapse;width:100%;min-width:760px;font-size:14px}}
th,td{{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
tr:last-child td{{border-bottom:0}}
th{{font-size:12px;color:var(--muted);letter-spacing:.04em;white-space:nowrap}}
.c{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.n{{white-space:nowrap;color:var(--muted)}} td.t{{font-weight:700}} td.r{{white-space:nowrap;font-size:13px}}
td.b{{font-weight:900;color:var(--accent)}}
td.mix{{font-size:12px;color:var(--muted);min-width:220px}}
td.rd{{font-size:13px}}
</style>
<div class="wrap">
  <div class="intro">
    <h1>國語闖關島製作成果</h1>
    <p>115 學年度上學期，國小一～六年級，南一、康軒、翰林三個版本的每一課都已做成闖關單元。每次進入一課，會從那一課的題庫隨機抽 10～20 題，還不會的字優先出現。</p>
    <p class="muted">「題庫」是這一課可以出的題目數量；「題庫組成」是各種小遊戲各有幾題可抽。生字、語詞來自教育百科 115 學年度資料。</p>
  </div>
  <div class="stats">
    <div class="stat"><b>{total["lessons"]}</b><span>課（6 個年級 × 3 版本）</span></div>
    <div class="stat"><b>{total["chars"]:,}</b><span>生字（各課加總）</span></div>
    <div class="stat"><b>{total["words"]:,}</b><span>語詞（各課加總）</span></div>
    <div class="stat"><b>72</b><span>篇閱讀短文（五、六年級）</span></div>
    <div class="stat"><b>{len(grades[0]["sentences"])}</b><span>句一年級句子填空</span></div>
    <div class="stat"><b>{len(strokes1)}</b><span>個一年級可描寫的字</span></div>
  </div>
  <nav aria-label="年級">{''.join(f'<a href="#g{g}">{GN[g-1]}年級</a>' for g in range(1, 7))}</nav>
  {''.join(sections)}
</div>
<script>
document.querySelectorAll(".grade").forEach(sec => {{
  sec.querySelectorAll(".vers button").forEach(b => b.onclick = () => {{
    sec.querySelectorAll(".vers button").forEach(x => x.setAttribute("aria-pressed", x === b));
    sec.querySelectorAll(".tbl").forEach(t => t.hidden = t.dataset.p !== b.dataset.p);
  }});
}});
</script>
'''
open("game-overview.html", "w", encoding="utf-8").write(page)
print(total)
