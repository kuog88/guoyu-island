"""把 reading_g5.txt、reading_g6.txt 排成審閱頁 reading-review.html（給老師、家長看過短文再上線）。"""
import html
import json

from build_game import cn2int, parse_reading

PUB = {"nani": "南一", "kang": "康軒", "han": "翰林"}
lessons = {l["id"]: l for l in json.load(open("lessons_115_1.json", encoding="utf-8"))}
cards = []
total_q = 0
for g in (5, 6):
    for lid, r in parse_reading(f"reading_g{g}.txt").items():
        l = lessons[lid]
        total_q += len(r["qs"])
        qs = "".join(
            f'<li><p class="q">{html.escape(q)}</p><ul class="opts"><li class="ok"><span class="mk" aria-label="正確答案">✓</span>{html.escape(a)}</li>'
            + "".join(f'<li><span class="mk" aria-hidden="true">·</span>{html.escape(d)}</li>' for d in ds) + "</ul></li>"
            for q, a, *ds in r["qs"])
        cards.append(f'''<article class="card" data-g="{g}" data-p="{l["pub"]}" id="{lid}">
  <header><span class="chip {l["pub"]}">{PUB[l["pub"]]}</span><span class="where">{g}上 第{cn2int(l["lesson"])}課〈{html.escape(l["title"])}〉</span><code>{lid}</code></header>
  <h2>{html.escape(r["title"])}</h2>
  <p class="text">{html.escape(r["text"])}</p>
  <p class="len">{len(r["text"])} 字</p>
  <ol class="qs">{qs}</ol>
</article>''')

page = f'''<title>閱讀短文審閱</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@600;900&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>
/* Layout: 單欄審閱稿；上方篩選列置頂，每篇短文一張稿紙卡，正確答案打勾 */
:root{{
  --bg:#f5f6f2; --paper:#fffdf7; --fg:#22281f; --muted:#626b5c; --line:#dfe3d6; --rule:#ebe6d6;
  --ok:#1f7a4d; --ok-bg:#e1f2e8;
  --nani:#c2410c; --nani-bg:#fdeee5; --kang:#1d4ed8; --kang-bg:#e8eefc; --han:#047857; --han-bg:#e2f4ec;
  --display:"Noto Serif TC","Songti TC",serif;
  --read:"DFKai-SB","BiauKai","TW-Kai","Noto Serif TC",serif;
  --ui:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;
}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
  --bg:#141812; --paper:#1d221b; --fg:#e7eae1; --muted:#9aa393; --line:#30382c; --rule:#2a3026;
  --ok:#6fd6a0; --ok-bg:#183626; --nani:#fb923c; --nani-bg:#3a2216; --kang:#7ea4ff; --kang-bg:#1b2645; --han:#4fd1a1; --han-bg:#153328; color-scheme:dark}}}}
:root[data-theme="dark"]{{
  --bg:#141812; --paper:#1d221b; --fg:#e7eae1; --muted:#9aa393; --line:#30382c; --rule:#2a3026;
  --ok:#6fd6a0; --ok-bg:#183626; --nani:#fb923c; --nani-bg:#3a2216; --kang:#7ea4ff; --kang-bg:#1b2645; --han:#4fd1a1; --han-bg:#153328; color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:var(--ui);font-size:15px;line-height:1.7}}
body::before{{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}}
.wrap{{max-width:760px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:20px}}
h1,h2{{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.3}}
h1{{font-size:clamp(24px,4vw,32px);font-weight:900}}
h2{{font-size:20px;font-weight:900}}
p{{margin:0}}
.intro{{display:grid;gap:8px}}
.muted{{color:var(--muted);font-size:14px}}
.bar{{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);padding-block:10px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.bar button{{font:inherit;font-size:14px;padding:4px 14px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:var(--fg);cursor:pointer}}
.bar button[aria-pressed="true"]{{background:var(--fg);color:var(--bg);border-color:var(--fg)}}
.bar button:focus-visible{{outline:2px solid var(--kang);outline-offset:2px}}
.bar .sep{{width:1px;height:22px;background:var(--line)}}
.bar .count{{margin-left:auto;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:18px 18px 16px;display:grid;gap:10px;scroll-margin-top:64px}}
.card header{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:14px}}
.chip{{padding:1px 10px;border-radius:999px;font-weight:700;font-size:13px}}
.chip.nani{{background:var(--nani-bg);color:var(--nani)}}.chip.kang{{background:var(--kang-bg);color:var(--kang)}}.chip.han{{background:var(--han-bg);color:var(--han)}}
.where{{font-weight:700}}
code{{margin-left:auto;font-size:12px;color:var(--muted)}}
.text{{font-family:var(--read);font-size:19px;line-height:2;text-indent:2em;max-width:36em;background-image:repeating-linear-gradient(transparent 0 calc(2em - 1px),var(--rule) calc(2em - 1px) 2em)}}
.len{{font-size:12px;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums}}
.qs{{margin:0;padding-left:1.4em;display:grid;gap:10px}}
.q{{font-weight:700}}
.opts{{list-style:none;margin:4px 0 0;padding:0;display:grid;gap:2px}}
.opts li{{display:flex;gap:8px;align-items:baseline;padding:2px 8px;border-radius:6px;color:var(--muted)}}
.opts li.ok{{background:var(--ok-bg);color:var(--ok);font-weight:700}}
.mk{{width:1em;flex:none;text-align:center}}
</style>

<div class="wrap">
  <div class="intro">
    <h1>閱讀短文審閱</h1>
    <p>闖關遊戲「漂流瓶閱讀」用的 {len(cards)} 篇短文、{total_q} 題，依五、六年級上學期各版本課文的主題自編，不是課文原文。打勾的是正確答案，遊戲中選項順序會打亂。</p>
    <p class="muted">要修改哪一篇，告訴我右上角的代號（例如 kang-6上-07）和想改的地方；也可以直接在頁面上留言。</p>
  </div>
  <nav class="bar" aria-label="篩選">
    <button data-g="all" aria-pressed="true">全部</button><button data-g="5" aria-pressed="false">五上</button><button data-g="6" aria-pressed="false">六上</button>
    <span class="sep" aria-hidden="true"></span>
    <button data-p="all" aria-pressed="true">三版本</button><button data-p="nani" aria-pressed="false">南一</button><button data-p="kang" aria-pressed="false">康軒</button><button data-p="han" aria-pressed="false">翰林</button>
    <span class="count" id="count"></span>
  </nav>
  {"".join(cards)}
</div>
<script>
const f = {{g:"all", p:"all"}};
function apply(){{
  let n = 0;
  document.querySelectorAll(".card").forEach(c => {{
    const show = (f.g === "all" || c.dataset.g === f.g) && (f.p === "all" || c.dataset.p === f.p);
    c.hidden = !show; if (show) n++;
  }});
  document.getElementById("count").textContent = `顯示 ${{n}} 篇`;
  document.querySelectorAll(".bar button").forEach(b => b.setAttribute("aria-pressed", (b.dataset.g ? b.dataset.g === f.g : b.dataset.p === f.p)));
}}
document.querySelectorAll(".bar button").forEach(b => b.onclick = () => {{ if (b.dataset.g) f.g = b.dataset.g; else f.p = b.dataset.p; apply(); }});
apply();
</script>
'''
open("reading-review.html", "w", encoding="utf-8").write(page)
print(len(cards), total_q)
