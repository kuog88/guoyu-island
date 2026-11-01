"""把三至六年級的句式題庫（bank_g*.txt、lessons_g*_*.txt）排成審閱頁 bank-review-g3.html。"""
import html
import json
import os
import re

from build_game import cn2int, parse_bank, parse_lesson_items

esc = html.escape
PUB = {"nani": "南一", "kang": "康軒", "han": "翰林"}
GN = {3: "三", 4: "四", 5: "五", 6: "六"}
lessons = {l["id"]: l for l in json.load(open("lessons_115_1.json", encoding="utf-8"))}


def blanks(s, fill=None):
    """把 [ ] 換成底線；fill 有值時依序填進答案（關聯詞用「…」分段）"""
    parts = iter((fill or "").split("…")) if fill and s.count("[") > 1 else iter([fill or ""] * 9)
    return re.sub(r"\[[^\]]*\]", lambda m: f'<u>{esc(next(parts, "")) if fill else "　　"}</u>', esc(s))


def opts(ok, *bad):
    return f'<span class="ok">✓ {esc(ok)}</span>' + "".join(f'<span class="no">{esc(b)}</span>' for b in bad if b)


def table(head, rows):
    return f"<div class='tbl'><table><thead><tr>{''.join(f'<th>{h}</th>' for h in head)}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def grade_section(g):
    bank = parse_bank(f"bank_g{g}.txt")
    secs = []
    hi = g >= 5
    rows = [f"<tr><td class='big'>{esc(r[0])}</td><td>{esc(r[1])}</td><td>{blanks(r[2], r[0])}</td><td class='o'>{opts(r[0], r[3], r[4])}</td>"
            + (f"<td class='mis'>{esc(r[6]) if len(r) > 6 else ''}</td>" if hi else "")
            + f"<td class='m'>{esc(r[5].replace(',', '、')) if len(r) > 5 and r[5] else '共用'}</td></tr>" for r in bank["idiom"]]
    secs.append(("idiom", "成語", f"{len(bank['idiom'])} 個，標了課次的是課文裡的成語，會優先出在那一課。" + ("高年級每課 4 題：拼圖、情境選用 2 題、找出用對的句子（用到「誤用例句」）。" if hi else "每課 3 題：拼圖 1 題、情境選用 2 題。"),
                 table(["成語", "意思", "例句", "選項"] + (["誤用例句（故意用錯）"] if hi else []) + ["出處"], rows)))
    secs.append(("conn", "關聯詞火車", f"{len(bank['conn'])} 題，每課 2 題。",
                 table(["句子", "選項", "關係"], [f"<tr><td>{blanks(r[0], r[1])}</td><td class='o'>{opts(r[1], r[2], r[3])}</td><td class='m'>{esc(r[4])}</td></tr>" for r in bank["conn"]])))
    if "measure" in bank:
        secs.append(("measure", "量詞配對", f"{len(bank['measure'])} 組，每題抽 3 組連連看。",
                     table(["題目", "選項"], [f"<tr><td class='big'>{blanks(r[0], re.search(r'\[(.+?)\]', r[0]).group(1))}</td><td class='o'>{opts(re.search(r'\[(.+?)\]', r[0]).group(1), r[1], r[2])}</td></tr>" for r in bank["measure"]])))
    if "rhet" in bank:
        secs.append(("rhet", "修辭偵探", f"{len(bank['rhet'])} 題，每課 3 題。",
                     table(["句子", "選項"], [f"<tr><td>{esc(r[0])}</td><td class='o'>{opts(r[1], r[2], r[3])}</td></tr>" for r in bank["rhet"]])))
    if "transform" in bank:
        secs.append(("transform", "句子變身", f"{len(bank['transform'])} 題，每課 2 題。",
                     table(["題型", "題目", "選項"], [f"<tr><td class='m'>{esc(r[0])}</td><td>{esc(r[1])}</td><td class='o'>{opts(r[2], r[3], r[4])}</td></tr>" for r in bank["transform"]])))
    for key, name in (("punct", "標點符號"), ("meaning", "句意理解"), ("rewrite", "換句話說")):
        secs.append((key, name, f"{len(bank[key])} 題，放在句子魔王裡。",
                     table(["題目", "選項"], [f"<tr><td>{blanks(r[0], r[1]) if '[' in r[0] else esc(r[0])}</td><td class='o'>{opts(r[1], r[2], r[3])}</td></tr>" for r in bank[key]])))
    cards = []
    for pub in PUB:
        p = f"lessons_g{g}_{pub}.txt"
        if not os.path.exists(p):
            continue
        for lid, it in parse_lesson_items(p).items():
            l = lessons[lid]
            fills = "".join(f"<li>{blanks(f[0], f[1])}<div class='o'>{opts(f[1], f[2], f[3])}</div></li>" for f in it["fill"])
            builds = "".join(f"<li>{' ／ '.join(esc(t) for t in b[0])}" + (f"<div class='muted'>也接受：{' ／ '.join(esc(t) for t in b[1])}</div>" if len(b) > 1 else "") + "</li>" for b in it["build"])
            cards.append(f'''<article class="card" data-p="{pub}" id="{lid}"><header><span class="chip {pub}">{PUB[pub]}</span><b>{g}上 第{cn2int(l["lesson"])}課〈{esc(l["title"])}〉</b><code>{lid}</code></header>
  <p class="muted">課文語詞：{esc("、".join(l["words"]))}</p>
  <h3>選詞填空（同樣的句子也用來出錯字偵探）</h3><ol>{fills}</ol>
  <h3>句子積木</h3><ol>{builds}</ol></article>''')
    total = sum(len(v) for v in bank.values())
    nav = "".join(f'<a href="#g{g}-{k}">{n}</a>' for k, n, *_ in secs) + f'<a href="#g{g}-lessons">各課題目</a>'
    body = "".join(f'<section id="g{g}-{k}"><h2>{n}</h2><p class="muted">{note}</p>{t}</section>' for k, n, note, t in secs)
    return total, len(cards), f'''<div class="grade" id="g{g}" {'hidden' if g != 3 else ''}>
  <p class="muted">{GN[g]}年級共用題庫 {total} 題（三個版本共用），加上三個版本 {len(cards)} 課各 5 句選詞填空、3 題句子積木。</p>
  <div class="subnav">{nav}</div>{body}
  <section id="g{g}-lessons"><h2>{GN[g]}年級各課題目</h2>
    <div class="pf" role="group" aria-label="版本">{''.join(f'<button data-p="{p}" aria-pressed="{str(p == "nani").lower()}">{n}</button>' for p, n in PUB.items())}</div>
    {''.join(cards)}</section></div>'''


parts = [grade_section(g) for g in (3, 4, 5, 6)]
total = sum(p[0] for p in parts)
nlessons = sum(p[1] for p in parts)
page = f'''<title>句式題庫審閱</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@600;900&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>
/* Layout: 單欄審閱稿；最上方切年級，年級內有分類導覽；共用題庫用表格，各課題目用卡片並可切版本 */
:root{{
  --bg:#f5f6f2; --paper:#fffdf7; --fg:#22281f; --muted:#626b5c; --line:#dfe3d6;
  --ok:#1f7a4d; --ok-bg:#e1f2e8; --no:#8a8f84; --mark:#c2410c; --mis:#b42318;
  --kang:#1d4ed8; --kang-bg:#e8eefc; --nani:#c2410c; --nani-bg:#fdeee5; --han:#047857; --han-bg:#e2f4ec;
  --display:"Noto Serif TC","Songti TC",serif; --read:"DFKai-SB","BiauKai","TW-Kai","Noto Serif TC",serif;
  --ui:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;
}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141812;--paper:#1d221b;--fg:#e7eae1;--muted:#9aa393;--line:#30382c;--ok:#6fd6a0;--ok-bg:#183626;--no:#7d8476;--mark:#fb923c;--mis:#ff8a80;--kang:#7ea4ff;--kang-bg:#1b2645;--nani:#fb923c;--nani-bg:#3a2216;--han:#4fd1a1;--han-bg:#153328;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141812;--paper:#1d221b;--fg:#e7eae1;--muted:#9aa393;--line:#30382c;--ok:#6fd6a0;--ok-bg:#183626;--no:#7d8476;--mark:#fb923c;--mis:#ff8a80;--kang:#7ea4ff;--kang-bg:#1b2645;--nani:#fb923c;--nani-bg:#3a2216;--han:#4fd1a1;--han-bg:#153328;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:var(--ui);font-size:15px;line-height:1.7}}
body::before{{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}}
.wrap{{max-width:1040px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:22px}}
h1,h2,h3{{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.3}}
h1{{font-size:clamp(24px,4vw,32px);font-weight:900}} h2{{font-size:21px;font-weight:900}} h3{{font-size:15px;font-weight:600}}
p{{margin:0;max-width:74ch}}
.muted{{color:var(--muted);font-size:14px}}
.gtabs{{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);padding-block:10px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px}}
.gtabs button,.pf button{{font:inherit;font-size:15px;font-weight:700;padding:4px 16px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:var(--fg);cursor:pointer}}
.gtabs button[aria-pressed="true"],.pf button[aria-pressed="true"]{{background:var(--fg);color:var(--bg);border-color:var(--fg)}}
button:focus-visible,a:focus-visible{{outline:2px solid var(--kang);outline-offset:2px}}
.grade{{display:grid;gap:26px}}
.subnav{{display:flex;flex-wrap:wrap;gap:6px}}
.subnav a{{text-decoration:none;color:var(--fg);font-size:13px;padding:2px 10px;border-radius:999px;border:1px solid var(--line);background:var(--paper)}}
section{{display:grid;gap:10px;scroll-margin-top:70px}}
.tbl{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--paper)}}
table{{border-collapse:collapse;width:100%;min-width:680px;font-size:14px}}
th,td{{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
tr:last-child td{{border-bottom:0}}
th{{font-size:12px;color:var(--muted);white-space:nowrap}}
td.big{{font-family:var(--read);font-size:18px;white-space:nowrap}}
td.m{{font-size:12px;color:var(--muted);white-space:nowrap}}
td.mis{{font-size:13px;color:var(--mis)}}
u{{text-decoration:none;border-bottom:2px solid var(--mark);color:var(--mark);padding:0 2px}}
.o{{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:13px}}
.o .ok{{color:var(--ok);font-weight:700;background:var(--ok-bg);padding:0 6px;border-radius:4px}}
.o .no{{color:var(--no)}}
.pf{{display:flex;gap:6px}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:16px;display:grid;gap:8px;scroll-margin-top:70px}}
.card header{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.chip{{padding:1px 10px;border-radius:999px;font-weight:700;font-size:13px}}
.chip.kang{{background:var(--kang-bg);color:var(--kang)}}.chip.nani{{background:var(--nani-bg);color:var(--nani)}}.chip.han{{background:var(--han-bg);color:var(--han)}}
code{{margin-left:auto;font-size:12px;color:var(--muted)}}
.card ol{{margin:0;padding-left:1.4em;display:grid;gap:6px}}
.card li{{font-family:var(--read);font-size:17px}}
.card li .o,.card li .muted{{font-family:var(--ui)}}
</style>
<div class="wrap">
  <div style="display:grid;gap:8px">
    <h1>句式題庫審閱</h1>
    <p>國語闖關島三至六年級的句式題目，全部自編，只參考考卷的題型格式。共用題庫 {total} 題，加上三個版本 {nlessons} 課的選詞填空和句子積木（{nlessons * 8} 題）。綠底打勾的是正確答案，遊戲中選項順序會打亂。</p>
    <p class="muted">要改哪一題，告訴我年級、分類和題目開頭幾個字，或課的代號（例如 kang-5上-04）；也可以直接在頁面上留言。</p>
  </div>
  <nav class="gtabs" aria-label="年級">{''.join(f'<button data-g="{g}" aria-pressed="{str(g == 3).lower()}">{GN[g]}年級</button>' for g in (3, 4, 5, 6))}</nav>
  {''.join(p[2] for p in parts)}
</div>
<script>
document.querySelectorAll(".gtabs button").forEach(b => b.onclick = () => {{
  document.querySelectorAll(".gtabs button").forEach(x => x.setAttribute("aria-pressed", x === b));
  document.querySelectorAll(".grade").forEach(g => g.hidden = g.id !== "g" + b.dataset.g);
  window.scrollTo(0, 0);
}});
document.querySelectorAll(".grade").forEach(sec => {{
  const apply = p => {{
    sec.querySelectorAll(".pf button").forEach(x => x.setAttribute("aria-pressed", x.dataset.p === p));
    sec.querySelectorAll(".card").forEach(c => c.hidden = c.dataset.p !== p);
  }};
  sec.querySelectorAll(".pf button").forEach(b => b.onclick = () => apply(b.dataset.p));
  apply("nani");
}});
</script>
'''
open("bank-review-g3.html", "w", encoding="utf-8").write(page)
print(total, nlessons)
