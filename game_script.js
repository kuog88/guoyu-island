/* 國語闖關島：1～6 年級上學期。各年級資料放在 data/g{n}.json、筆順放在 strokes/g{n}.json，選年級時才載入。 */
const PUB = {nani:"南一", kang:"康軒", han:"翰林"};
const GRADE = ["", "一", "二", "三", "四", "五", "六"];
const STORE = "guoyu-island-v3";
const BUILD = "__BUILD__";
const ORDER = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ";
const LOOKALIKE = {ㄅ:"ㄆㄉ",ㄆ:"ㄅㄊ",ㄇ:"ㄈㄋ",ㄈ:"ㄇㄏ",ㄉ:"ㄊㄅ",ㄊ:"ㄉㄆ",ㄋ:"ㄌㄇ",ㄌ:"ㄋㄖ",ㄍ:"ㄎㄏ",ㄎ:"ㄍㄏ",ㄏ:"ㄈㄎ",ㄐ:"ㄑㄓ",ㄑ:"ㄐㄔ",ㄒ:"ㄕㄙ",ㄓ:"ㄗㄐ",ㄔ:"ㄘㄑ",ㄕ:"ㄙㄒ",ㄖ:"ㄌㄦ",ㄗ:"ㄓㄘ",ㄘ:"ㄔㄗ",ㄙ:"ㄕㄒ",ㄧ:"ㄩㄨ",ㄨ:"ㄧㄩ",ㄩ:"ㄧㄨ",ㄚ:"ㄛㄜ",ㄛ:"ㄜㄡ",ㄜ:"ㄛㄝ",ㄝ:"ㄜㄟ",ㄞ:"ㄟㄠ",ㄟ:"ㄞㄝ",ㄠ:"ㄡㄞ",ㄡ:"ㄠㄛ",ㄢ:"ㄤㄣ",ㄣ:"ㄥㄢ",ㄤ:"ㄢㄥ",ㄥ:"ㄣㄤ",ㄦ:"ㄜㄖ"};
const TONES = [{v:1,k:"ˉ",n:"一聲"},{v:2,k:"ˊ",n:"二聲"},{v:3,k:"ˇ",n:"三聲"},{v:4,k:"ˋ",n:"四聲"},{v:5,k:"˙",n:"輕聲"}];
/* 部首以課本（康熙）歸部為準，旁邊附上孩子在課本看到的偏旁寫法 */
const RAD_VAR = {水:"氵",手:"扌",人:"亻",心:"忄",艸:"艹",辵:"辶",阜:"阝左",邑:"阝右",犬:"犭",火:"灬",肉:"月",衣:"衤",示:"礻",玉:"王",刀:"刂",竹:"⺮",食:"飠",网:"罒",攴:"攵",牛:"牜",老:"耂",糸:"糹",言:"訁",金:"釒",足:"⻊",絲:"糸"};
const radLabel = r => RAD_VAR[r] ? `${r}（${RAD_VAR[r]}）` : r;

/* 目前年級的資料（loadGrade 會換掉） */
let DATA = null, INFO = {}, WZY = {}, STROKES = {}, allGen = [], allWords = [], wordSet = new Set(), CUR_ZY = null;
/* 一年級全文注音用：校對過的詞語讀音（多音字、輕聲）和課本以外的字的讀音 */
let ZYP = {}, ZYC = {};
const canWrite = c => !!STROKES[c] && !!window.HanziWriter;
const showZy = () => DATA && DATA.grade <= 2;

let S = load();
function load(){
  const d = {grade:null, version:null, range:"m1", mastery:{}, stars:{}, cards:[], at:{}};
  try { return Object.assign(d, JSON.parse(localStorage.getItem(STORE) || "{}")); } catch(e){ return d; }
}
function save(){ try { localStorage.setItem(STORE, JSON.stringify(S)); } catch(e){} }

const rand = a => a[Math.floor(Math.random()*a.length)];
const shuffle = a => { a = a.slice(); for (let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; };
const uniq = a => [...new Set(a)];
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const zy = c => (CUR_ZY && CUR_ZY[c]) || (INFO[c] ? INFO[c][0] : "");
function parse(z){
  const light = z.startsWith("˙"), m = z.match(/[ˊˇˋ]/);
  return {syl:[...z.replace(/[˙ˊˇˋ]/g, "")], tone: light ? 5 : m ? {"ˊ":2,"ˇ":3,"ˋ":4}[m[0]] : 1};
}
const base = z => z.replace(/[ˊˇˋ˙]/g, "");
function bpmf(z){
  if (!z) return "";
  const p = parse(z), tk = TONES[p.tone-1].k;
  return `<span class="bpmf" aria-hidden="true">${p.tone===5 ? "<i>˙</i>" : ""}${p.syl.map(x => `<i>${x}</i>`).join("")}${p.tone>1 && p.tone<5 ? `<i class="tn">${tk}</i>` : ""}</span>`;
}
const zc = (inner, z) => `<span class="zc">${inner}${bpmf(z)}</span>`;
/* 一、二年級全文加注音；三年級以上只在要考的地方加 */
const ruby = (c, z, force) => (force || showZy()) && (z || INFO[c]) ? zc(esc(c), z || zy(c)) : esc(c);
const HAN = /[\u3400-\u9fff]/;
const fullZy = () => !!DATA && DATA.grade === 1;
/* 依上下文決定每個字的讀音：由左到右找最長的詞（課文語詞、校對過的詞），找不到再用單字讀音 */
function readText(s){
  const cs = [...s], out = [];
  for (let i = 0; i < cs.length;){
    let n = Math.min(6, cs.length - i);
    for (; n > 1; n--){ const r = WZY[cs.slice(i, i+n).join("")] || ZYP[cs.slice(i, i+n).join("")]; if (r && r.length === n){ out.push(...r); break; } }
    if (n > 1){ i += n; continue; }
    const c = cs[i++];
    out.push((CUR_ZY && CUR_ZY[c]) || ZYC[c] || (INFO[c] ? INFO[c][0] : ""));
  }
  return out;
}
/* 標點黏在前一個字（開頭的引號黏在後一個字），才不會單獨跑到下一行的開頭 */
function zyHTML(s){
  const cs = [...s], r = readText(s);
  let out = "", buf = "", last = null;
  const flush = () => { if (last){ out += `<span class="zc">${last.pre}${esc(last.c)}${bpmf(last.z)}${last.post}</span>`; last = null; } };
  cs.forEach((c,i) => {
    if (r[i] && HAN.test(c)){
      const open = buf.match(/[「『（《〈“‘]+$/);
      if (open) buf = buf.slice(0, -open[0].length);
      flush(); out += esc(buf); buf = "";
      last = {pre:open ? esc(open[0]) : "", c, z:r[i], post:""};
    } else if (last && !buf && /[，。！？、：；」』）》〉…”’]/.test(c)) last.post += esc(c);
    else { flush(); buf += c; }
  });
  flush();
  return out + esc(buf);
}
const rubyText = s => showZy() ? zyHTML(s) : esc(s);
/* 一年級：畫面上所有國字自動加注音。會洩漏答案的地方（選項、要拼的字）加 class="nozy" */
const ZY_SKIP = ".zc,.bpmf,.nozy,script,style,svg";
function zyNode(node){
  const s = node.nodeValue, r = readText(s);
  if (![...s].some((c,i) => r[i] && HAN.test(c))) return;
  const t = document.createElement("template"); t.innerHTML = zyHTML(s);
  node.replaceWith(t.content);
}
function autoZy(root){
  if (!fullZy() || app.dataset.page === "parent") return;
  if (root.nodeType === 3){ if (root.parentElement && !root.parentElement.closest(ZY_SKIP)) zyNode(root); return; }
  if (root.nodeType !== 1 || root.closest(ZY_SKIP)) return;
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {acceptNode:n => n.parentElement.closest(ZY_SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  const list = []; while (w.nextNode()) list.push(w.currentNode);
  list.forEach(zyNode);
}
const wordZy = w => WZY[w] || [...w].map(zy);
const rubyWord = (w, force) => { const z = wordZy(w); return [...w].map((c,i) => ruby(c, z[i], force)).join(""); };
const blankIn = (w, pos) => { const z = wordZy(w); return [...w].map((c,i) => i === pos ? zc(`<span class="blank">？</span>`, z[i]) : ruby(c, z[i])).join(""); };
const known = c => (S.mastery[c] || 0) >= 2;

/* ---------- 聲音 ---------- */
/* 朗讀語音：自動挑裝置上最自然的國語（臺灣）語音，家長也可以在首頁自己換。
   順序：zh-TW 的 Natural／Online（Edge 雲端語音）> Google 國語（臺灣）> Apple 增強版／高品質 > 其他 zh-TW > zh-CN。
   zh-HK、粵語不列入。 */
let voice = null, actx = null, zhVoices = [];
const vlang = v => (v.lang || "").replace("_", "-").toLowerCase();
const isTW = v => /^(zh|cmn)-(hant-)?tw/.test(vlang(v));
const isCantonese = v => /^(zh-hk|zh-mo|yue)/.test(vlang(v)) || /粵|廣東|cantonese/i.test(v.name);
function voiceScore(v){
  let n = isTW(v) ? 100 : /^(zh|cmn)/.test(vlang(v)) ? 20 : 0;
  if (/natural|online|neural/i.test(v.name)) n += 60;
  if (/google/i.test(v.name)) n += 40;
  if (/enhanced|premium|高品質|增強/i.test(v.name)) n += 30;
  if (/美佳|meijia/i.test(v.name)) n += 5;
  return n;
}
function pickVoice(){
  try {
    zhVoices = speechSynthesis.getVoices().filter(v => /^(zh|cmn)/.test(vlang(v)) && !isCantonese(v)).sort((a,b) => voiceScore(b) - voiceScore(a));
    voice = zhVoices.find(v => v.name === S.voiceName) || zhVoices[0] || null;
    const box = document.getElementById("voicebox"); if (box) bindVoice();
  } catch(e){}
}
if ("speechSynthesis" in window){ pickVoice(); speechSynthesis.addEventListener("voiceschanged", pickVoice); }
function say(text){
  try {
    /* 單字前後加停頓，免得第一個音被吃掉 */
    if ([...text].length <= 2) text = `，${text}。`;
    speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text); u.lang = voice ? voice.lang : "zh-TW"; u.rate = .9; u.pitch = 1; if (voice) u.voice = voice;
    duck(true); u.onend = u.onerror = () => duck(false);
    speechSynthesis.speak(u);
  } catch(e){}
}
function sfx(kind){
  try {
    audio();
    const notes = {ok:[660,880], no:[220,180], pop:[900], win:[523,659,784,1046]}[kind];
    notes.forEach((f,i) => {
      const o = actx.createOscillator(), g = actx.createGain(), t = actx.currentTime + i*.11;
      o.type = kind === "no" ? "triangle" : "sine"; o.frequency.value = f;
      g.gain.setValueAtTime(.18, t); g.gain.exponentialRampToValueAtTime(.001, t + .25);
      o.connect(g).connect(actx.destination); o.start(t); o.stop(t + .26);
    });
  } catch(e){}
}
/* 背景音樂：用 Web Audio 即時合成的輕柔循環（不用音樂檔，沒有版權問題）。
   四個和弦一輪，每輪旋律從五聲音階隨機挑，聽起來不會一直重複。 */
const BGM = {on:false, timer:null, bar:0, next:0, gain:null, vol:.07};
const CHORDS = [[48,55,64,71],[45,52,60,67],[41,48,57,64],[43,50,59,65]]; // Cmaj7 Am7 Fmaj7 G7（MIDI）
const PENTA = [60,62,64,67,69,72,74,76];
const BEAT = 60/72;
const hz = m => 440 * Math.pow(2, (m-69)/12);
function audio(){ actx = actx || new (window.AudioContext || window.webkitAudioContext)(); return actx; }
function tone(f, t, len, vol, type){
  const o = actx.createOscillator(), g = actx.createGain();
  o.type = type; o.frequency.value = f;
  g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + Math.min(.08, len/4));
  g.gain.exponentialRampToValueAtTime(.0005, t + len);
  o.connect(g).connect(BGM.gain); o.start(t); o.stop(t + len + .05);
}
function playBar(t){
  const ch = CHORDS[BGM.bar % 4];
  ch.forEach((m,i) => tone(hz(m), t + i*.04, BEAT*4.2, i ? .16 : .22, "sine"));          // 和弦墊底
  [0,1,2,3].forEach(b => { if (Math.random() < .7) tone(hz(rand(PENTA)), t + b*BEAT + (Math.random() < .3 ? BEAT/2 : 0), BEAT*1.6, .2, "triangle"); }); // 旋律
  tone(hz(ch[0]-12), t, BEAT*2, .25, "sine");                                             // 低音
  BGM.bar++;
}
function bgmTick(){
  while (BGM.next < actx.currentTime + 1.5){ playBar(BGM.next); BGM.next += BEAT*4; }
}
function bgmStart(){
  try {
    audio();
    if (!BGM.gain){ BGM.gain = actx.createGain(); BGM.gain.gain.value = 0; BGM.gain.connect(actx.destination); }
    if (actx.state === "suspended") actx.resume();
    if (BGM.on) return;
    BGM.on = true; BGM.next = actx.currentTime + .1;
    BGM.gain.gain.cancelScheduledValues(actx.currentTime);
    BGM.gain.gain.setTargetAtTime(BGM.vol, actx.currentTime, .8);
    bgmTick(); BGM.timer = setInterval(bgmTick, 400);
  } catch(e){}
}
function bgmStop(){
  if (!BGM.on) return;
  BGM.on = false; clearInterval(BGM.timer);
  try { BGM.gain.gain.setTargetAtTime(0, actx.currentTime, .2); } catch(e){}
}
/* 唸題目時把音樂調小聲 */
function duck(down){
  if (!BGM.on) return;
  try { BGM.gain.gain.setTargetAtTime(down ? BGM.vol*.25 : BGM.vol, actx.currentTime, .15); } catch(e){}
}
const musicBtn = document.getElementById("music");
function syncMusicBtn(){ if (musicBtn) musicBtn.setAttribute("aria-pressed", String(S.music === true)); }
if (musicBtn) musicBtn.onclick = e => {
  e.stopPropagation();
  S.music = S.music !== true; save(); syncMusicBtn();
  S.music ? bgmStart() : bgmStop();
};
/* 預設不放音樂，按右下角 ♪ 才會開；打開過的話，下次點畫面時再接著放（瀏覽器規定要先點一下才能出聲音） */
document.addEventListener("pointerdown", () => { if (S.music === true) bgmStart(); }, true);
document.addEventListener("visibilitychange", () => {
  if (!actx) return;
  if (document.hidden) actx.suspend(); else if (BGM.on) actx.resume();
});
syncMusicBtn();

function burst(el){
  if (!el) return;
  const r = el.getBoundingClientRect(), box = document.createElement("div");
  box.className = "burst";
  const cols = ["var(--star)","var(--coral)","var(--ok)","var(--kang)"];
  box.innerHTML = Array.from({length:14}, (_,i) => {
    const a = i/14*Math.PI*2, d = 50 + Math.random()*40;
    return `<i style="left:${r.left+r.width/2}px;top:${r.top+r.height/2}px;background:${cols[i%4]};--x:${Math.cos(a)*d}px;--y:${Math.sin(a)*d}px"></i>`;
  }).join("");
  document.body.appendChild(box); setTimeout(() => box.remove(), 800);
}

/* ---------- 圖案 ---------- */
const AVATAR = `<svg class="avatar" viewBox="0 0 52 60" aria-hidden="true"><ellipse cx="26" cy="56" rx="14" ry="3.5" fill="var(--shadow)"/><path d="M8 30a18 18 0 0 1 36 0v14a10 10 0 0 1-10 10H18A10 10 0 0 1 8 44z" fill="var(--coral)"/><path d="M6 24c4-14 36-14 40 0z" fill="var(--kang)"/><rect x="4" y="22" width="44" height="5" rx="2.5" fill="var(--kang)"/><circle cx="19" cy="35" r="3.2" fill="var(--ink)"/><circle cx="33" cy="35" r="3.2" fill="var(--ink)"/><path d="M21 43q5 4 10 0" stroke="var(--ink)" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>`;
const FISH = c => `<svg viewBox="0 0 90 56" aria-hidden="true"><path d="M70 28 88 12v32z" fill="${c}"/><ellipse cx="40" cy="28" rx="36" ry="24" fill="${c}"/><circle cx="14" cy="22" r="3.5" fill="#1d2b33"/></svg>`;
const BOSS = `<svg class="boss" id="boss" viewBox="0 0 120 110" aria-hidden="true"><path d="M60 8c30 0 52 24 52 54 0 26-14 40-52 40S8 88 8 62C8 32 30 8 60 8z" fill="currentColor"/><path d="M30 14 22 0l18 10zM90 14l8-14-18 10z" fill="currentColor"/><circle cx="42" cy="50" r="11" fill="#fff"/><circle cx="78" cy="50" r="11" fill="#fff"/><circle cx="45" cy="52" r="5" fill="#1d2b33"/><circle cx="75" cy="52" r="5" fill="#1d2b33"/><path d="M38 76q22 16 44 0" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M48 80l4 7 4-6M64 81l4 6 4-7" fill="#fff"/></svg>`;
const FISHCOL = ["#ffb347","#ff8a80","#9ad0f5","#c9a7ff","#9be29b","#ffd56b","#f7a8d0","#8fe3d6"];
const BALLCOL = ["var(--coral)","var(--kang)","var(--han)","var(--boss)"];
const ICON_SPEAK = `<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/></svg>`;

const app = document.getElementById("app");
new MutationObserver(ms => { if (fullZy()) ms.forEach(m => m.addedNodes.forEach(autoZy)); }).observe(app, {childList:true, subtree:true});
let PARENT_PAGE = false; // 設定頁、家長報表是給大人看的，不加注音
function render(html){ app.dataset.page = PARENT_PAGE ? "parent" : ""; PARENT_PAGE = false; app.innerHTML = html; window.scrollTo(0,0); }

/* ---------- 載入年級資料 ---------- */
async function loadGrade(g){
  if (DATA && DATA.grade === g) return true;
  render(`<div class="stage"><div class="say">${AVATAR}<div class="bubble">正在準備${GRADE[g]}年級的島嶼…</div></div></div>`);
  try {
    /* 每次發布都換版本號，避免瀏覽器沿用舊的題庫檔 */
    const r = await fetch(`data/g${g}.json?v=${BUILD}`, {cache:"no-cache"});
    if (!r.ok) throw new Error(r.status);
    DATA = await r.json();
  } catch(e){
    render(`<div class="stage"><div class="bubble">${GRADE[g]}年級的資料沒有載入成功，請檢查網路後再試一次。</div><button class="btn primary" id="again">再試一次</button></div>`);
    document.getElementById("again").onclick = () => boot();
    return false;
  }
  INFO = DATA.info; WZY = DATA.wordZy || {};
  ZYC = DATA.zyChars || {}; ZYP = {};
  for (const [w, z] of Object.entries(DATA.zyPhrases || {})) ZYP[w] = z.split(" ");
  allGen = uniq(DATA.lessons.flatMap(l => l.chars)).filter(c => INFO[c]);
  allWords = uniq(DATA.lessons.flatMap(l => l.words)).filter(w => w.length >= 2 && [...w].every(c => INFO[c]));
  wordSet = new Set(allWords);
  STROKES = {};
  try { const r = await fetch(`strokes/g${g}.json?v=${BUILD}`, {cache:"no-cache"}); if (r.ok) STROKES = await r.json(); } catch(e){}
  return true;
}

/* ---------- 範圍與關卡 ---------- */
const lessonsOf = v => DATA.lessons.filter(l => l.pub === v).sort((a,b) => a.order - b.order);
const lessonLabel = l => l.order === 0 && l.pub === "nani" && DATA.grade === 1 ? "前導" : `第${l.lessonNo}課`;
function ranges(){
  if (DATA.grade === 1) return {m1:{name:"第一次月考", sub:"注音符號、拼音、聲調"}, m2:{name:"第二次月考", sub:"課文生字"}};
  const ls = lessonsOf(S.version), half = Math.ceil(ls.length/2);
  const r = {m1:{name:"第一次月考", sub:`第 ${ls[0].lessonNo}～${ls[half-1].lessonNo} 課`}, m2:{name:"第二次月考", sub:`第 ${ls[half].lessonNo}～${ls[ls.length-1].lessonNo} 課`}};
  if (DATA.bank) r.practice = {name:"加強練習", sub:"成語・句型"};
  if (hasReading()) r.read = {name:"閱讀加強", sub:"漂流瓶短文"};
  return r;
}
function zyLevels(){
  const pool = Object.keys(INFO);
  const by = n => pool.filter(c => parse(INFO[c][0]).syl.length === n);
  return [
    {id:"g1-zy-1", kind:"zy", game:"fish", title:"一個符號的字", glyph:"ㄚ", label:"拼音島 1", chars:by(1)},
    {id:"g1-zy-2", kind:"zy", game:"fish", title:"兩個符號的字", glyph:"ㄅㄚ", label:"拼音島 2", chars:by(2)},
    {id:"g1-zy-3", kind:"zy", game:"fish", title:"三個符號的字", glyph:"ㄏㄨㄚ", label:"拼音島 3", chars:by(3)},
    {id:"g1-zy-t", kind:"zy", game:"tone", title:"聲調貝殼灘", glyph:"ˇ", label:"聲調島", chars:pool},
    {id:"g1-zy-b", kind:"zy", game:"boss", title:"注音大魔王", glyph:"王", label:"魔王島", chars:pool},
  ];
}
function levels(range){
  if (range === "read") return hasReading() ? readingLevels() : [];
  if (range === "practice") return DATA.bank ? practiceLevels() : [];
  if (DATA.grade === 1 && range === "m1") return zyLevels();
  const ls = lessonsOf(S.version).map(l => ({...l, kind:"lesson", glyph:l.chars[0] || l.title[0], label:lessonLabel(l)}));
  if (DATA.grade === 1) return ls;
  const half = Math.ceil(ls.length/2);
  return range === "m1" ? ls.slice(0, half) : range === "m2" ? ls.slice(half) : ls;
}

/* ---------- 設定 ---------- */
function setup(p){
  p = p || {grade:S.grade, version:S.version, range:S.range};
  PARENT_PAGE = true;
  render(`
    <div class="hero"><span class="muted">115 學年度・上學期・南一／康軒／翰林</span><h1>國語闖關島</h1>
      <p class="muted">爸爸媽媽設定一次就好：年級、課本版本、要準備哪一次月考。</p></div>
    <div class="panel"><h2>1. 孩子幾年級？</h2>
      <div class="grades">${[1,2,3,4,5,6].map(g => `<button class="gbtn" data-g="${g}" aria-pressed="${p.grade===g}">${GRADE[g]}年級</button>`).join("")}</div></div>
    <div class="panel"><h2>2. 用哪個版本的課本？</h2>
      <div class="vers">${["nani","kang","han"].map(v => `<button class="ver ${v}" data-v="${v}" aria-pressed="${p.version===v}"><b>${PUB[v]}版</b></button>`).join("")}</div></div>
    <div class="panel"><h2>3. 要準備哪一次月考？</h2>
      <div class="ranges">
        <button class="range" data-r="m1" aria-pressed="${p.range==="m1"}"><b>第一次月考</b><span>${p.grade===1 ? "注音符號、拼音、聲調（三個版本都一樣）" : "前半學期的課"}</span></button>
        <button class="range" data-r="m2" aria-pressed="${p.range==="m2"}"><b>第二次月考</b><span>${p.grade===1 ? "課文生字（依課本版本）" : "後半學期的課"}</span></button></div>
      <p class="muted">各校考試範圍可能不同，在地圖上方可以隨時切換範圍。</p>
      <div class="row"><span class="spacer"></span><button class="btn primary" id="go" ${p.version && p.grade ? "" : "disabled"}>出發去冒險</button></div></div>
    <div class="panel" id="voicebox"></div>
    <p class="muted credit">楷體字型：全字庫正楷體（國家發展委員會，政府資料開放授權）；筆順：教育部常用國字標準字體筆順（g0v/zh-stroke-data）</p>`);
  bindVoice();
  app.querySelectorAll(".gbtn").forEach(b => b.onclick = () => setup({...p, grade:+b.dataset.g}));
  app.querySelectorAll(".ver").forEach(b => b.onclick = () => setup({...p, version:b.dataset.v}));
  app.querySelectorAll(".range").forEach(b => b.onclick = () => setup({...p, range:b.dataset.r}));
  document.getElementById("go").onclick = async () => {
    if (!p.version || !p.grade) return;
    const switched = S.version && S.version !== p.version && S.grade === p.grade;
    Object.assign(S, p); save();
    if (await loadGrade(S.grade)) map(switched);
  };
}

/* 首頁的「試聽／換聲音」 */
function bindVoice(){
  const box = document.getElementById("voicebox");
  if (!box) return;
  if (!("speechSynthesis" in window)){ box.innerHTML = `<h2>🔈 朗讀聲音</h2><p class="muted">這個瀏覽器不支援朗讀，建議用 Edge 或 Chrome 瀏覽器。</p>`; return; }
  const auto = zhVoices[0], label = v => `${v.name}${isTW(v) ? "" : "（大陸口音）"}`;
  box.innerHTML = `<h2>🔈 朗讀聲音</h2>
    <div class="voicerow"><select id="voicesel" aria-label="朗讀聲音">
      <option value="">自動${auto ? `（${esc(label(auto))}）` : ""}</option>
      ${zhVoices.map(v => `<option value="${esc(v.name)}" ${v.name === S.voiceName ? "selected" : ""}>${esc(label(v))}</option>`).join("")}</select>
      <button class="btn small" id="voicetry">試聽</button></div>
    ${zhVoices.some(isTW) ? "" : `<p class="muted">這台裝置的中文語音較少，建議用 Edge 瀏覽器，或在系統設定下載「中文（台灣）」語音。</p>`}`;
  document.getElementById("voicesel").onchange = e => { S.voiceName = e.target.value || undefined; save(); pickVoice(); say("小朋友，我們一起來闖關吧！"); };
  document.getElementById("voicetry").onclick = () => say("小朋友，我們一起來闖關吧！");
}

/* ---------- 地圖 ---------- */
function map(switched){
  CUR_ZY = null;
  const rg = ranges();
  if (!rg[S.range]) S.range = "m1";
  const lv = levels(S.range);
  const mine = new Set(lessonsOf(S.version).flatMap(l => l.chars));
  const cardCount = S.cards.filter(c => mine.has(c)).length;
  const carried = switched ? Object.keys(S.mastery).filter(c => known(c) && mine.has(c)) : [];
  render(`
    <div class="mapbar"><button class="btn small" id="settings">← 國文首頁</button>
      <span class="chip ${S.version}">${GRADE[DATA.grade]}年級・${PUB[S.version]}版</span>
      <span class="spacer"></span>
      <button class="btn small" id="dex">字卡 ${cardCount}/${mine.size}</button>
      <button class="btn small" id="report">家長報表</button></div>
    <div class="tabs">${Object.entries(rg).map(([k,r]) => `<button class="tab" data-r="${k}" aria-pressed="${S.range===k}"><b>${r.name}</b><span>${r.sub}</span></button>`).join("")}</div>
    ${carried.length ? `<div class="carry">換到${PUB[S.version]}版：你已經會 ${carried.length} 個字了，這些字的題目會變少。</div>` : ""}
    <div class="map" id="map">${lv.map((l,i) => {
      const k = l.chars.filter(known).length, st = S.stars[l.id] || 0;
      return `<button class="node ${st ? "done" : ""}" data-i="${i}">
        <span class="island nozy" style="${l.glyph.length>1 ? "font-size:20px" : ""}">${esc(l.glyph)}</span>
        <span style="display:grid;gap:4px;min-width:0"><span class="ttl">${esc(l.title)}</span>
          <span class="meta"><span>${esc(l.label)}</span>
            <span class="stars" aria-label="${st} 顆星">${"★".repeat(st)}<span class="off">${"★".repeat(3-st)}</span></span>
            ${l.items && DATA.bank ? `<span class="tagnew">句型新玩法</span>` : ""}
            ${l.kind === "lesson" ? `<span class="meter" aria-hidden="true"><i style="width:${l.chars.length ? k/l.chars.length*100 : 0}%"></i></span><span>會了 ${k}/${l.chars.length}</span>` : ""}</span></span></button>`;
    }).join("")}<span class="mapavatar" id="me">${AVATAR}</span></div>`);
  const me = document.getElementById("me"), nodes = [...app.querySelectorAll(".node")];
  const key = `${DATA.grade}-${S.version}-${S.range}`;
  const place = i => { const n = nodes[i]; if (!n) return; me.style.left = (n.offsetLeft + n.offsetWidth - 30) + "px"; me.style.top = (n.offsetTop - 26) + "px"; };
  const first = lv.findIndex(l => !S.stars[l.id]);
  place(Math.min(S.at[key] ?? (first < 0 ? 0 : first), lv.length - 1));
  document.getElementById("settings").onclick = () => setup();
  document.getElementById("dex").onclick = dex;
  document.getElementById("report").onclick = () => report();
  app.querySelectorAll(".tab").forEach(b => b.onclick = () => { S.range = b.dataset.r; save(); map(); });
  nodes.forEach((b,i) => b.onclick = () => { place(i); S.at[key] = i; save(); setTimeout(() => start(lv[i], i), 520); });
}
function dex(){
  CUR_ZY = null;
  const all = uniq(lessonsOf(S.version).flatMap(l => l.chars)), got = new Set(S.cards);
  render(`<div class="top"><button class="btn small" id="back">← 地圖</button><span class="spacer"></span></div>
    <div class="panel"><h2>字卡圖鑑</h2><p class="muted">打開寶箱、答對題目就能收集字卡。${GRADE[DATA.grade]}年級${PUB[S.version]}版共 ${all.length} 張，已收集 ${all.filter(c => got.has(c)).length} 張。點收集到的字卡可以練習寫字。</p>
    <div class="dex">${all.map(c => got.has(c) ? (canWrite(c) ? `<button data-c="${esc(c)}" aria-label="練習寫 ${esc(c)}"><span>${zc(esc(c), zy(c))}</span></button>` : `<span>${zc(esc(c), zy(c))}</span>`) : `<span class="no">？</span>`).join("")}</div></div>`);
  document.getElementById("back").onclick = () => map();
  app.querySelectorAll(".dex button").forEach(b => b.onclick = () => writeGame({t:b.dataset.c}, null, true));
}
function collect(c){ if (c && !S.cards.includes(c)) S.cards.push(c); }

/* ---------- 家長報表：只看這台裝置上的紀錄，依目前的年級和版本整理 ---------- */
const logOf = c => (S.log && S.log[c]) || {r:0, w:0, x:{}};
const weakScore = c => { const e = logOf(c); return e.w * 2 - e.r - (known(c) ? 2 : 0); };
function weakChars(chars, n){
  return chars.filter(c => logOf(c).w > 0 && weakScore(c) > 0).sort((a,b) => weakScore(b) - weakScore(a)).slice(0, n);
}
/* 考前複習：用孩子常錯的字臨時組一關，題型和一般課文關卡一樣 */
function reviewLevel(chars, title){
  const ls = lessonsOf(S.version).filter(l => l.chars.some(c => chars.includes(c)));
  const zyMap = Object.assign({}, ...ls.map(l => l.zy || {}));
  return {id:`${DATA.grade}-${S.version}-review`, kind:"lesson", title, label:"複習", glyph:"複", chars,
    readChars:[], words:uniq(ls.flatMap(l => l.words)).filter(w => chars.some(c => w.includes(c))), zy:zyMap};
}
function report(){
  CUR_ZY = null;
  const ls = lessonsOf(S.version), chars = uniq(ls.flatMap(l => l.chars));
  const mastered = chars.filter(known), tried = chars.filter(c => logOf(c).r + logOf(c).w > 0);
  const played = ls.filter(l => S.stars[l.id]);
  const stars = ls.reduce((s,l) => s + (S.stars[l.id] || 0), 0);
  const types = Object.entries(S.types || {}).filter(([,v]) => v.r + v.w > 0);
  const tr = types.reduce((s,[,v]) => s + v.r, 0), tw = types.reduce((s,[,v]) => s + v.w, 0);
  const pct = (a, b) => b ? Math.round(a / b * 100) : 0;
  const last = S.lastPlayed ? new Date(S.lastPlayed) : null;
  /* 月考範圍：一年級第一次月考是拼音群島，用全部一上的字 */
  const rg = ranges();
  const rangeCards = Object.entries(rg).filter(([k]) => k !== "read" && k !== "practice").map(([k, r]) => {
    const lv = levels(k), rc = uniq(lv.flatMap(l => l.chars)).filter(c => DATA.grade === 1 && k === "m1" ? true : chars.includes(c));
    const done = lv.filter(l => S.stars[l.id]).length, m = rc.filter(known).length, weak = weakChars(rc, 12);
    return `<div class="rcard"><div class="row"><b>${r.name}</b><span class="muted">${esc(r.sub)}</span></div>
      <div class="kv"><span>完成關卡</span><b>${done}／${lv.length}</b><span>已學會的字</span><b>${m}／${rc.length}</b></div>
      <div class="meter wide" aria-hidden="true"><i style="width:${pct(m, rc.length)}%"></i></div>
      ${weak.length ? `<p class="muted">還不熟的字：</p><div class="wchips">${weak.map(c => `<span>${esc(c)}</span>`).join("")}</div>
        <button class="btn small primary" data-review="${k}">用這 ${weak.length} 個字練一關</button>` : `<p class="muted">${done ? "這個範圍目前沒有常錯的字。" : "還沒開始玩這個範圍。"}</p>`}</div>`;
  }).join("");
  const weakAll = weakChars(chars, 24);
  PARENT_PAGE = true;
  render(`<div class="top"><button class="btn small" id="back">← 地圖</button><span class="spacer"></span><span class="chip ${S.version}">${GRADE[DATA.grade]}年級・${PUB[S.version]}版</span></div>
    <div class="panel rep">
      <h2>家長報表</h2>
      <p class="muted">只統計這台裝置上的紀錄。${last ? `最近一次答對題目：${last.getMonth()+1} 月 ${last.getDate()} 日 ${String(last.getHours()).padStart(2,"0")}:${String(last.getMinutes()).padStart(2,"0")}` : "還沒有作答紀錄。"}</p>
      <div class="kpis">
        <div><b>${played.length}<small>／${ls.length}</small></b><span>完成的課</span></div>
        <div><b>${stars}<small>／${ls.length*3}</small></b><span>星星</span></div>
        <div><b>${mastered.length}<small>／${chars.length}</small></b><span>已學會的生字</span></div>
        <div><b>${pct(tr, tr+tw)}<small>%</small></b><span>答對率（共 ${tr+tw} 題）</span></div>
      </div>
    </div>
    <div class="panel rep"><h2>月考準備</h2><div class="rcards">${rangeCards}</div></div>
    <div class="panel rep"><h2>常錯的字</h2>
      ${weakAll.length ? `<div class="tbl"><table><thead><tr><th>字</th><th>注音</th><th class="c">答錯</th><th class="c">答對</th><th>常選成</th><th>在哪一課</th></tr></thead><tbody>
        ${weakAll.map(c => { const e = logOf(c), conf = Object.entries(e.x || {}).sort((a,b) => b[1]-a[1]).slice(0,2).map(([x]) => x).join("、");
          const l = ls.find(l => l.chars.includes(c));
          return `<tr><td class="big">${esc(c)}</td><td>${esc(zy(c))}</td><td class="c bad">${e.w}</td><td class="c">${e.r}</td><td>${esc(conf) || "—"}</td><td class="muted">${l ? `${lessonLabel(l)}〈${esc(l.title)}〉` : ""}</td></tr>`; }).join("")}
        </tbody></table></div>
        <button class="btn primary" id="reviewAll">用常錯的字練一關</button>`
      : `<p class="muted">${tried.length ? "目前沒有常錯的字，表現很穩定！" : "孩子玩過關卡後，這裡會列出常答錯的字。"}</p>`}
      <p class="muted">已經練過 ${tried.length} 個字，還有 ${chars.length - tried.length} 個字還沒出現過。</p></div>
    <div class="panel rep"><h2>題型表現</h2>
      ${types.length ? `<div class="bars">${types.sort((a,b) => pct(a[1].r, a[1].r+a[1].w) - pct(b[1].r, b[1].r+b[1].w)).map(([k,v]) => { const p = pct(v.r, v.r+v.w);
        return `<div class="brow"><span>${KIND_NAME[k] || k}</span><div class="meter wide"><i class="${p < 70 ? "low" : ""}" style="width:${p}%"></i></div><b>${p}%</b><span class="muted">${v.r+v.w} 題</span></div>`; }).join("")}</div>
        <p class="muted">由弱到強排列，紅色是答對率低於 70% 的題型。各年級累計。</p>` : `<p class="muted">還沒有作答紀錄。</p>`}</div>
    <div class="panel rep"><h2>每一課的進度</h2>
      <div class="tbl"><table><thead><tr><th>課次</th><th>課名</th><th>星星</th><th class="c">會了</th><th>最常錯</th></tr></thead><tbody>
      ${ls.map(l => { const st = S.stars[l.id] || 0, k = l.chars.filter(known).length, w = weakChars(l.chars, 3).join("、");
        return `<tr><td class="muted">${lessonLabel(l)}</td><td>${esc(l.title)}</td><td class="stars">${"★".repeat(st)}<span class="off">${"★".repeat(3-st)}</span></td><td class="c">${k}／${l.chars.length}</td><td class="bad">${esc(w) || (st ? "—" : "")}</td></tr>`; }).join("")}
      </tbody></table></div></div>
    <div class="panel rep"><h2>重新開始</h2><p class="muted">清除這台裝置上所有年級的星星、字卡和作答紀錄，設定會保留。</p>
      <div class="row"><button class="btn small" id="reset">清除紀錄</button><button class="btn small danger" id="resetYes" hidden>確定清除，無法復原</button></div></div>`);
  document.getElementById("back").onclick = () => map();
  /* 常錯的字不到 8 個時，補上範圍內還沒學會的字，讓一關至少有 10 題 */
  const go = (weak, pool, title) => {
    const cs = uniq([...weak, ...shuffle(pool.filter(c => !known(c))), ...shuffle(pool)]).slice(0, Math.max(weak.length, 8));
    start(reviewLevel(cs, title), 9999);
  };
  app.querySelectorAll("[data-review]").forEach(b => b.onclick = () => {
    const k = b.dataset.review, lv = levels(k);
    const rc = uniq(lv.flatMap(l => l.chars)).filter(c => DATA.grade === 1 && k === "m1" ? true : chars.includes(c));
    go(weakChars(rc, 12), rc.filter(c => chars.includes(c)).length ? rc.filter(c => chars.includes(c)) : chars, `${rg[k].name}考前複習`);
  });
  const ra = document.getElementById("reviewAll");
  if (ra) ra.onclick = () => go(weakChars(chars, 12), chars, "常錯字複習");
  document.getElementById("reset").onclick = () => { document.getElementById("resetYes").hidden = false; };
  document.getElementById("resetYes").onclick = () => {
    Object.assign(S, {mastery:{}, stars:{}, cards:[], at:{}, log:{}, types:{}, lastPlayed:null}); save(); report();
  };
}

/* ---------- 題庫：每次進關卡都從這一課的字、詞重新隨機抽題 ---------- */
function charDistractors(t, n){
  const r = INFO[t] ? INFO[t][1] : null, st = INFO[t] ? INFO[t][2] : 0;
  const pool = allGen.filter(c => c !== t && base(INFO[c][0]) !== base(zy(t)));
  return uniq([...shuffle(pool.filter(c => INFO[c][1] === r)), ...shuffle(pool.filter(c => Math.abs(INFO[c][2]-st) <= 2)), ...shuffle(pool)]).slice(0, n);
}
/* 錯字：同音字最常寫錯，再來是同部首、筆畫相近的字 */
function wrongChars(t){
  const pool = allGen.filter(c => c !== t);
  const b = base(zy(t)), r = INFO[t] ? INFO[t][1] : null;
  return uniq([...shuffle(pool.filter(c => base(INFO[c][0]) === b)), ...shuffle(pool.filter(c => INFO[c][1] === r)), ...shuffle(pool)]);
}
function weakFirst(chars, n){
  const w = shuffle(chars.filter(c => !known(c))), k = shuffle(chars.filter(known));
  return [...w, ...k].slice(0, n);
}
const spellQ = (c, toneOnly) => ({kind:"spell", t:c, toneOnly:!!toneOnly});
const lessonWords = lv => uniq([...lv.words]).filter(w => w.length >= 2 && w.length <= 4 && [...w].every(c => INFO[c]));
function wordQs(lv, n){
  const out = [];
  for (const c of weakFirst(lv.chars, lv.chars.length)){
    const cand = shuffle([...lessonWords(lv), ...allWords.filter(w => w.length <= 4)].filter(w => w.includes(c)));
    if (!cand.length) continue;
    const w = cand[0], pos = w.indexOf(c);
    const ds = charDistractors(c, 10).filter(d => !wordSet.has(w.slice(0,pos) + d + w.slice(pos+1))).slice(0, 2);
    if (ds.length < 2) continue;
    out.push({kind:"word", t:c, w, pos, opts:shuffle([c, ...ds])});
    if (out.length >= n) break;
  }
  return out;
}
function bossBank(lv){
  const bank = {sentence:[], radical:[], wrongword:[], hearword:[]};
  if (DATA.sentences) bank.sentence = shuffle(DATA.sentences.filter(s => lv.chars.includes(s[1]))).map(s => ({kind:"sentence", t:s[1], s:s[0], opts:shuffle([s[1], ...s[2]])}));
  const rads = uniq(allGen.map(c => INFO[c][1]));
  for (const c of shuffle(lv.chars)){
    const r = INFO[c] && INFO[c][1];
    if (!r || r === c || INFO[c][4]) continue; // 歸部無法確認的字不出題
    const ds = shuffle(rads.filter(x => x !== r && x !== INFO[c][3])).slice(0, 2); // 教育部字典的歸部不當錯誤選項
    bank.radical.push({kind:"radical", t:c, opts:shuffle([r, ...ds]), ans:r});
  }
  const lw = lessonWords(lv);
  for (const w of shuffle(lw)){
    const idx = [...w].map((c,i) => lv.chars.includes(c) ? i : -1).filter(i => i >= 0);
    if (!idx.length) continue;
    const fakes = [];
    for (const i of shuffle(idx)){
      for (const d of wrongChars(w[i])){
        const f = w.slice(0,i) + d + w.slice(i+1);
        if (!wordSet.has(f) && !fakes.includes(f)){ fakes.push(f); break; }
      }
      if (fakes.length >= 2) break;
    }
    if (fakes.length < 2){ const i = idx[0]; for (const d of wrongChars(w[i])){ const f = w.slice(0,i) + d + w.slice(i+1); if (!wordSet.has(f) && !fakes.includes(f)) fakes.push(f); if (fakes.length >= 2) break; } }
    if (fakes.length >= 2) bank.wrongword.push({kind:"wrongword", t:w[idx[0]], w, opts:shuffle([w, ...fakes.slice(0,2)]), ans:w});
  }
  if (lw.length >= 3) for (const w of shuffle(lw).slice(0, 4)){
    const others = shuffle(lw.filter(x => x !== w && x.length === w.length)).concat(shuffle(lw.filter(x => x !== w)));
    const opts = uniq([w, ...others]).slice(0, 3);
    if (opts.length === 3) bank.hearword.push({kind:"hearword", t:[...w].find(c => lv.chars.includes(c)) || w[0], w, opts:shuffle(opts), ans:w});
  }
  return bank;
}
function pickBoss(bank, n, grade){
  const plan = grade === 1 ? ["sentence","sentence","sentence","radical","hearword","wrongword"] : ["wrongword","radical","hearword","wrongword","radical","hearword"];
  const out = [], used = new Set();
  for (let round = 0; out.length < n && round < 6; round++){
    for (const k of plan){
      if (out.length >= n) break;
      const q = bank[k].find(x => !used.has(x));
      if (q){ used.add(q); out.push(q); }
    }
  }
  return out;
}
/* 閱讀：每課一篇自編短文、3 題，選項順序每次打亂 */
function readingQs(lessonId){
  const r = DATA.reading && DATA.reading[lessonId];
  if (!r) return [];
  return r.qs.map((x, i) => ({kind:"read", t:null, r, first:i === 0, q:x[0], ans:x[1], opts:shuffle(x.slice(1))}));
}
/* 閱讀加強區（五、六年級）：和一般關卡分開，每次從範圍內隨機抽幾篇 */
const hasReading = () => !!(DATA && DATA.reading);
function readingLevels(){
  const ls = lessonsOf(S.version), half = Math.ceil(ls.length/2);
  const mk = (id, title, label, from, pick) => ({id:`${DATA.grade}-${S.version}-${id}`, kind:"read", title, label, glyph:"讀",
    lessonIds:from.map(l => l.id), pick, chars:[]});
  return [
    mk("read-m1", "第一次月考範圍閱讀", `第 ${ls[0].lessonNo}～${ls[half-1].lessonNo} 課・每次 4 篇`, ls.slice(0, half), 4),
    mk("read-m2", "第二次月考範圍閱讀", `第 ${ls[half].lessonNo}～${ls[ls.length-1].lessonNo} 課・每次 4 篇`, ls.slice(half), 4),
    mk("read-all", "全冊閱讀挑戰", `全部 ${ls.length} 課・每次 5 篇`, ls, 5),
  ];
}
function buildStations(lv){
  if (lv.kind === "read")
    return [{name:"漂流瓶閱讀", game:"read", qs:shuffle(lv.lessonIds).slice(0, lv.pick).flatMap(readingQs)}];
  if (lv.kind === "zy"){
    const multi = Object.keys(INFO).filter(c => parse(INFO[c][0]).syl.length > 1);
    if (lv.game === "fish"){
      const qs = weakFirst(lv.chars, 10).map(c => spellQ(c));
      /* 一個符號的字不到 10 個，用聲調題補滿 */
      if (qs.length < 10) qs.push(...weakFirst(multi, 12 - qs.length).map(c => spellQ(c, true)));
      return [{name:"撈魚拼注音", game:"fish", qs}];
    }
    if (lv.game === "tone") return [{name:"撿聲調貝殼", game:"fish", qs:weakFirst(multi, 12).map(c => spellQ(c, true))}];
    return [{name:"注音大魔王", game:"boss", qs:weakFirst(multi, 10).map(c => spellQ(c))}];
  }
  if (lv.kind === "practice") return practiceStations(lv);
  if (lv.items && DATA.bank) return sentenceStations(lv);
  const bank = bossBank(lv);
  const st = [
    {name:"打開寶箱", game:"chest"},
    {name:"射氣球", game:"balloon", qs:weakFirst(lv.chars, 4).map(c => ({kind:"listen", t:c, opts:shuffle([c, ...charDistractors(c, 2)])}))},
    /* 描寫只有一年級；二年級以上把題數留給單元複習 */
    {name:"描一描", game:"write", qs:DATA.grade === 1 ? weakFirst(lv.chars.filter(canWrite), 2).map(c => ({kind:"write", t:c})) : []},
    {name:"撈魚拼注音", game:"fish", qs:weakFirst(lv.chars, 3).map(c => spellQ(c))},
    {name:"看注音修小橋", game:"bridge", qs:wordQs(lv, DATA.grade === 1 ? 4 : 5)},
    {name:"打魔王", game:"boss", qs:[]},
  ];
  /* 每關 10～20 題：前面幾站不夠的題數由魔王關補 */
  const pre = st.reduce((s,x) => s + (x.qs ? x.qs.length : 0), 0);
  const boss = st[st.length - 1];
  boss.qs = pickBoss(bank, Math.max(5, Math.min(20 - pre, DATA.grade === 1 ? 5 : 8)), DATA.grade);
  const total = pre + boss.qs.length;
  if (total < 10){
    const extra = weakFirst(lv.chars, 10 - total).map(c => ({kind:"listen", t:c, opts:shuffle([c, ...charDistractors(c, 2)])}));
    st[1].qs.push(...extra);
  }
  return st.filter(s => s.game === "chest" || s.qs.length);
}

/* ---------- 三年級以上的句式關卡 ----------
 * 1. 共用題庫依版本的課次順序分到每一課：課文裡的成語固定在原本那一課，其他題目輪流分到第 1～12 課。
 * 2. 同一關裡出現過的字、詞、成語、句子不會再出現；最近玩過的題目（S.recent）也會往後排。
 * 3. 題型隨機穿插，每次的題型比例也會小幅變動。 */
const lessonCharIn = (lv, w) => [...w].find(c => lv.chars.includes(c)) || null;
const RECENT_MAX = 400;
const isRecent = k => (S.recent || []).includes(k);
function markSeen(q){
  if (!q || !q.keys) return;
  S.recent = (S.recent || []).filter(k => !q.keys.includes(k)).concat(q.keys).slice(-RECENT_MAX);
}
/* 從主要題庫（這一課分到的）優先抽，沒出現過、最近沒玩過的先抽；不夠再從其他課補 */
function take(primary, secondary, n, keyOf, used){
  const fresh = a => shuffle(a.filter(x => !used.has(keyOf(x)) && !isRecent(keyOf(x))));
  const stale = a => shuffle(a.filter(x => !used.has(keyOf(x)) && isRecent(keyOf(x))));
  const out = [];
  for (const x of [...fresh(primary), ...fresh(secondary || []), ...stale(primary), ...stale(secondary || [])]){
    if (out.length >= n) break;
    const k = keyOf(x);
    if (used.has(k)) continue;
    used.add(k); out.push(x);
  }
  return out;
}
/* 依目前版本的課次，把年級共用題庫分到每一課 */
let ASSIGN = null;
function assignBank(){
  const key = `${DATA.grade}-${S.version}`;
  if (ASSIGN && ASSIGN.key === key) return ASSIGN.map;
  const ls = lessonsOf(S.version), map = {};
  ls.forEach(l => map[l.id] = {});
  for (const [cat, rows] of Object.entries(DATA.bank)){
    ls.forEach(l => map[l.id][cat] = []);
    let rest = rows;
    if (cat === "idiom"){
      const tagOf = x => (x[5] || "").split(",").map(t => t.trim()).find(id => map[id]);
      rows.filter(tagOf).forEach(x => map[tagOf(x)].idiom.push(x));
      rest = rows.filter(x => !tagOf(x));
    }
    rest.forEach((x, i) => map[ls[i % ls.length].id][cat].push(x));
  }
  ASSIGN = {key, map};
  return map;
}
function poolsFor(lessonIds){
  const map = assignBank(), out = {};
  for (const id of lessonIds) for (const [cat, rows] of Object.entries(map[id] || {})) (out[cat] = out[cat] || []).push(...rows);
  return out;
}
const otherRows = (cat, primary) => (DATA.bank[cat] || []).filter(x => !primary.includes(x));

/* --- 各題型的出題函式，都接收 used（這一關已用過的鍵） --- */
function typoQs(rows, n, used, lv){
  const out = [];
  for (const f of take(rows, [], rows.length, f => "s:" + f[0], new Set([...used]))){
    if (out.length >= n) break;
    const w = f[1];
    if (used.has("w:" + w) || used.has("s:" + f[0])) continue;
    const plain = f[0].replace(/[\[\]]/g, ""), at = f[0].indexOf("[");
    for (const i of shuffle([...w].map((c,i) => i).filter(i => INFO[w[i]]))){
      const c = w[i], fake = wrongChars(c).find(d => d !== c && !wordSet.has(w.slice(0,i) + d + w.slice(i+1)));
      if (!fake) continue;
      const others = wrongChars(c).filter(d => d !== fake && d !== c).slice(0, 2);
      if (others.length < 2) continue;
      used.add("w:" + w); used.add("s:" + f[0]);
      out.push({kind:"typo", t:c, s:plain.slice(0,at+i) + fake + plain.slice(at+i+1), pos:at+i, fake, opts:shuffle([c, ...others]), w, keys:["s:" + f[0]]});
      break;
    }
  }
  return out;
}
function fillQs(rows, n, used, lv){
  return take(rows.filter(f => !used.has("w:" + f[1])), [], n, f => "s:" + f[0], used).map(f => {
    used.add("w:" + f[1]);
    return {kind:"fill", t:lv ? lessonCharIn(lv, f[1]) : null, s:f[0], ans:f[1], opts:shuffle([f[1], f[2], f[3]]), keys:["s:" + f[0]]};
  });
}
function bridgeQs(lv, n, used){
  const out = [];
  for (const c of weakFirst(lv.chars, lv.chars.length)){
    if (out.length >= n) break;
    const cand = shuffle([...lessonWords(lv), ...allWords.filter(w => w.length <= 4)].filter(w => w.includes(c) && !used.has("w:" + w)));
    const w = cand.find(x => !isRecent("w:" + x)) || cand[0];
    if (!w || used.has("c:" + c)) continue;
    const pos = w.indexOf(c);
    const ds = charDistractors(c, 10).filter(d => !wordSet.has(w.slice(0,pos) + d + w.slice(pos+1))).slice(0, 2);
    if (ds.length < 2) continue;
    used.add("w:" + w); used.add("c:" + c);
    out.push({kind:"word", t:c, w, pos, opts:shuffle([c, ...ds]), keys:["w:" + w]});
  }
  return out;
}
function measureQs(rows, n, used){
  const out = [];
  for (let k = 0; k < n; k++){
    const pick = [], seenAns = new Set();
    for (const m of take(rows, otherRows("measure", rows), 12, m => "m:" + m[0], new Set(used))){
      const ans = m[0].match(/\[(.+?)\]/)[1];
      if (seenAns.has(ans)) continue;
      seenAns.add(ans); used.add("m:" + m[0]); pick.push({text:m[0], ans});
      if (pick.length >= 3) break;
    }
    if (pick.length === 3) out.push({kind:"measure", t:null, pairs:pick, opts:shuffle(pick.map(x => x.ans)), keys:pick.map(p => "m:" + p.text)});
  }
  return out;
}
const fillIn = x => x[2].replace(/\[[^\]]*\]/, x[0]);
/* 成語：一個成語只出一次，題型可能是拼圖、情境選用、選意思、找出用對的句子（高年級） */
function idiomQ(x, form){
  const k = ["i:" + x[0]];
  if (form === "puzzle") return {kind:"idiomPuzzle", t:null, w:x[0], meaning:x[1], tiles:shuffle([...x[0]]), answers:[[...x[0]]], keys:k};
  if (form === "meaning"){
    const wrong = shuffle(DATA.bank.idiom.filter(y => y[0] !== x[0] && y[1] !== x[1])).slice(0, 2).map(y => y[1]);
    return {kind:"idiomMeaning", t:null, p:`「${x[0]}」是什麼意思？`, ans:x[1], opts:shuffle([x[1], ...wrong]), meaning:`「${x[0]}」：${x[1]}`, keys:k};
  }
  if (form === "use" && x[6]){
    const wrong = shuffle(DATA.bank.idiom.filter(y => y[0] !== x[0] && y[6])).slice(0, 2).map(y => y[6]);
    if (wrong.length === 2) return {kind:"idiomUse", t:null, p:"哪一句的成語用得正確？", ans:fillIn(x), opts:shuffle([fillIn(x), ...wrong]), meaning:`「${x[0]}」：${x[1]}`, keys:k};
  }
  return {kind:"idiom", t:null, s:x[2], ans:x[0], opts:shuffle([x[0], x[3], x[4]]), meaning:x[1], keys:k};
}
function idiomQs(rows, n, used){
  const picked = take(rows, otherRows("idiom", rows), n, x => "i:" + x[0], used), forms = idiomForms(picked.length);
  return picked.map((x, i) => idiomQ(x, forms[i]));
}
const simpleQ = (kind, keyPre) => (rows, n, used) => take(rows, otherRows(kind === "conn" ? "conn" : kind, rows), n, x => keyPre + x[0], used).map(x => {
  if (kind === "conn") return {kind, t:null, s:x[0], ans:x[1], opts:shuffle([x[1], x[2], x[3]]), rel:x[4], keys:[keyPre + x[0]]};
  if (kind === "transform") return {kind, t:null, label:x[0], p:x[1], ans:x[2], opts:shuffle([x[2], x[3], x[4]]), keys:[keyPre + x[0]]};
  return {kind, t:null, p:x[0], ans:x[1], opts:shuffle([x[1], x[2], x[3]]), keys:[keyPre + x[0]]};
});
const connQs = simpleQ("conn", "c:"), rhetQs = simpleQ("rhet", "r:"), transformQs = (rows, n, used) =>
  take(rows, otherRows("transform", rows), n, x => "t:" + x[1], used).map(x => ({kind:"transform", t:null, label:x[0], p:x[1], ans:x[2], opts:shuffle([x[2], x[3], x[4]]), keys:["t:" + x[1]]}));
const punctQs = simpleQ("punct", "p:"), meaningQs = simpleQ("meaning", "p:"), rewriteQs = simpleQ("rewrite", "p:");
function buildQs(rows, n, used){
  return take(rows, [], n, b => "b:" + b[0].join(""), used).map(b => ({kind:"build", t:null, tiles:shuffle(b[0]), answers:b, keys:["b:" + b[0].join("")]}));
}
/* 題型隨機排：洗牌後避免同一種題型連續出現三次 */
function mixOrder(qs){
  const run3 = a => a.some((x, i) => i >= 2 && x.kind === a[i-1].kind && x.kind === a[i-2].kind);
  let a = shuffle(qs);
  for (let t = 0; t < 30 && run3(a); t++){
    a = shuffle(qs);
    for (let i = 2; i < a.length; i++){
      if (a[i].kind === a[i-1].kind && a[i].kind === a[i-2].kind){
        const j = a.findIndex((x, k) => k > i && x.kind !== a[i].kind);
        if (j > 0) [a[i], a[j]] = [a[j], a[i]];
      }
    }
  }
  return a;
}
/* 成語題型輪流分配（拼圖、選用、意思、誤用），避免某一種太多 */
const idiomForms = n => {
  const base = DATA.grade >= 5 ? ["puzzle", "choose", "meaning", "use"] : ["puzzle", "choose", "meaning"];
  return shuffle(Array.from({length:n}, (_, i) => base[i % base.length]));
};
/* 每次的題數分配：以基本比例為準，隨機挪動兩題 */
function jitter(quota){
  const q = {...quota}, ks = Object.keys(q);
  for (let t = 0; t < 2; t++){
    const from = rand(ks.filter(k => q[k] > 1)), to = rand(ks.filter(k => k !== from));
    if (from && to){ q[from]--; q[to]++; }
  }
  return q;
}
function sentenceStations(lv){
  const used = new Set(), pool = poolsFor([lv.id]), hi = DATA.grade >= 5;
  const fills = lv.items.fill, builds = lv.items.build;
  const quota = jitter(hi ? {word:2, typo:2, idiom:4, fill:2, rhet:3, conn:2, transform:2}
                          : {word:3, typo:2, measure:1, idiom:3, fill:3, conn:2, build:2});
  const qs = [
    ...typoQs(fills, Math.min(quota.typo, 2), used, lv),
    ...fillQs(fills, quota.fill, used, lv),
    ...bridgeQs(lv, quota.word, used),
    ...(quota.measure ? measureQs(pool.measure || [], quota.measure, used) : []),
    ...idiomQs(pool.idiom || [], quota.idiom, used),
    ...connQs(pool.conn || [], quota.conn, used),
    ...(quota.build ? buildQs(builds, quota.build, used) : []),
    ...(quota.rhet ? rhetQs(pool.rhet || [], quota.rhet, used) : []),
    ...(quota.transform ? transformQs(pool.transform || [], quota.transform, used) : []),
  ];
  const bossN = Math.max(3, 20 - qs.length);
  const boss = [];
  const bossMakers = [() => punctQs(pool.punct || [], 1, used), () => meaningQs(pool.meaning || [], 1, used), () => rewriteQs(pool.rewrite || [], 1, used)];
  for (let i = 0; boss.length < bossN && i < 15; i++) boss.push(...bossMakers[i % 3]());
  return [
    {name:"打開寶箱", game:"chest"},
    {name:"闖關挑戰", game:"mix", qs:mixOrder(qs)},
    {name:"句子魔王", game:"boss", qs:boss.slice(0, bossN)},
  ].filter(s => s.game === "chest" || s.qs.length);
}

/* ---------- 加強練習（三年級以上）：成語練習、句型練習，依版本課次範圍一次複習 ---------- */
function practiceLevels(){
  const ls = lessonsOf(S.version), half = Math.ceil(ls.length/2);
  const ranges = [["m1", "第一次月考範圍", ls.slice(0, half)], ["m2", "第二次月考範圍", ls.slice(half)], ["all", "全冊", ls]];
  const out = [];
  for (const [focus, name, glyph] of [["idiom", "成語練習", "成"], ["pattern", "句型練習", "句"]])
    for (const [rid, rname, from] of ranges)
      out.push({id:`${DATA.grade}-${S.version}-pr-${focus}-${rid}`, kind:"practice", focus, glyph, chars:[],
        title:`${name}・${rname}`, label:`第 ${from[0].lessonNo}～${from[from.length-1].lessonNo} 課・每次 20 題`, lessonIds:from.map(l => l.id)});
  return out;
}
function practiceStations(lv){
  const used = new Set(), pool = poolsFor(lv.lessonIds), hi = DATA.grade >= 5;
  const lessonsIn = DATA.lessons.filter(l => lv.lessonIds.includes(l.id) && l.items);
  let qs = [];
  if (lv.focus === "idiom"){
    const picked = take(pool.idiom || [], otherRows("idiom", pool.idiom || []), 20, x => "i:" + x[0], used), forms = idiomForms(picked.length);
    qs = picked.map((x, i) => idiomQ(x, forms[i]));
  } else {
    const builds = lessonsIn.flatMap(l => l.items.build);
    const makers = hi
      ? [[connQs, "conn", 4], [rhetQs, "rhet", 4], [transformQs, "transform", 4], [punctQs, "punct", 3], [meaningQs, "meaning", 2], [rewriteQs, "rewrite", 3]]
      : [[connQs, "conn", 5], [buildQs, "build", 5], [punctQs, "punct", 4], [meaningQs, "meaning", 3], [rewriteQs, "rewrite", 3]];
    const src = cat => cat === "build" ? builds : (pool[cat] || []);
    for (const [fn, cat, n] of makers) qs.push(...fn(src(cat), n + (Math.random() < .5 ? 1 : -1), used));
    /* 隨機增減後不足 20 題，就輪流從各題型補一題 */
    for (let i = 0; qs.length < 20 && i < 40; i++){ const [fn, cat] = makers[i % makers.length]; qs.push(...fn(src(cat), 1, used)); }
    qs = qs.slice(0, 20);
  }
  return [{name:lv.focus === "idiom" ? "成語練習" : "句型練習", game:"mix", qs:mixOrder(qs)}];
}

/* ---------- 關卡流程 ---------- */
let G = null;
function start(lv, idx){
  CUR_ZY = lv.zy || null;
  G = {lv, idx, st:buildStations(lv), si:0, qi:0, right:0, total:0, missed:new Set()};
  G.count = G.st.reduce((s,x) => s + (x.qs ? x.qs.length : 0), 0);
  station();
}
function header(){
  const s = G.st[G.si];
  return `<div class="top"><button class="btn small" id="back">← 地圖</button>
    <div class="steps" aria-hidden="true">${G.st.map((x,i) => `<span class="${i<G.si?"ok":i===G.si?"on":""}"></span>`).join("")}</div>
    <span class="chip ${G.lv.kind==="zy" ? "" : S.version}">${esc(G.lv.title)}</span></div>
    <div class="stname">${s.game === "mix" && s.qs[G.qi] ? `${s.name}・${KIND_NAME[s.qs[G.qi].kind] || ""}` : s.name}${s.qs && s.game !== "boss" ? `・${Math.min(G.qi+1, s.qs.length)}／${s.qs.length}` : ""}</div>`;
}
function bindBack(){ document.getElementById("back").onclick = () => { try { speechSynthesis.cancel(); } catch(e){} map(); }; }
function station(){
  const s = G.st[G.si];
  if (!s) return finish();
  if (s.game === "chest") return chest();
  if (s.game === "boss") return bossFight(s);
  if (G.qi >= s.qs.length){ G.si++; G.qi = 0; return station(); }
  const q = s.qs[G.qi];
  const GAME = {listen:balloon, spell:fishGame, word:bridge, write:writeGame, read:readGame, typo:typoGame, measure:measureGame,
    idiomPuzzle:orderGame, build:orderGame, idiom:fillGame, fill:fillGame, conn:fillGame,
    rhet:pickGame, transform:pickGame, idiomUse:pickGame, idiomMeaning:pickGame, punct:pickGame, meaning:pickGame, rewrite:pickGame};
  GAME[q.kind](q, (ok, chosen) => afterAnswer(q, ok, chosen));
}
/* 家長報表用的紀錄：每個字答對／答錯幾次、常被選成哪個字，以及每種題型的對錯 */
const KIND_NAME = {listen:"聽音找字", spell:"拼注音", "spell-tone":"注音聲調", word:"看注音寫國字", write:"筆順描寫", radical:"部首",
  wrongword:"錯字辨識", hearword:"聽語詞", sentence:"句子填空", read:"閱讀理解",
  typo:"錯字偵探", measure:"量詞", idiomPuzzle:"成語拼圖", idiom:"成語運用", fill:"選詞填空", conn:"關聯詞", build:"句子重組",
  punct:"標點符號", meaning:"句意理解", rewrite:"換句話說", rhet:"修辭", transform:"句子變身", idiomUse:"成語誤用辨別", idiomMeaning:"成語意思"};
function record(q, ok, chosen){
  S.log = S.log || {}; S.types = S.types || {};
  const kind = q.kind === "spell" && !ok && q.err === "tone" ? "spell-tone" : q.kind;
  const tk = S.types[kind] = S.types[kind] || {r:0, w:0};
  ok ? tk.r++ : tk.w++;
  if (q.t){
    const e = S.log[q.t] = S.log[q.t] || {r:0, w:0, x:{}};
    ok ? e.r++ : e.w++;
    if (!ok && chosen && [...chosen].length === 1 && chosen !== q.t) e.x[chosen] = (e.x[chosen] || 0) + 1;
    e.at = Date.now();
  }
  if (ok) S.lastPlayed = Date.now();
}
/* 共用的對錯紀錄：第一次答錯會把題目排到這一站最後再考一次 */
function afterAnswer(q, ok, chosen){
  if (ok === "skip"){ setTimeout(() => { G.qi++; station(); }, 100); return; }
  if (ok === "miss"){
    record(q, false);
    G.total++; G.missed.add(q.t); S.mastery[q.t] = Math.max(0, (S.mastery[q.t]||0) - 1); collect(q.t); save();
    setTimeout(() => { G.qi++; station(); }, 1600); return;
  }
  markSeen(q);
  /* 閱讀題不綁特定的字，只計分、不記字的熟練度 */
  const tracked = !!q.t;
  if (ok){
    /* 先答錯、後來才答對的題目，已經在答錯時計過一次，不再加分 */
    if (!q.retried && !q.counted){ record(q, true); G.right++; G.total++; if (tracked) S.mastery[q.t] = Math.min(3, (S.mastery[q.t]||0) + 1); }
    if (tracked) collect(q.t);
    save();
    setTimeout(() => { G.qi++; station(); }, q.kind === "read" ? 1500 : 1300);
  } else if (!q.counted){
    q.counted = true; if (tracked) G.missed.add(q.t);
    if (!q.retried){ record(q, false, chosen); G.total++; if (tracked) S.mastery[q.t] = Math.max(0, (S.mastery[q.t]||0) - 1); save();
      /* 一、二年級答錯的題目會在最後再考一次；三年級以上不重複出題，答錯的字詞記在家長報表 */
      if (DATA.grade <= 2) G.st[G.si].qs.push({...q, retried:true, counted:false, opts:q.opts && shuffle(q.opts)}); }
  }
}
function speakerBtn(label){ return `<button class="speak" id="play">${ICON_SPEAK}<span>${label || "再聽一次"}</span></button>`; }
function talk(msg){ return `<div class="say">${AVATAR}<div class="bubble" id="msg">${msg}</div></div>`; }
function setMsg(t){ const m = document.getElementById("msg"); if (m) m.textContent = t; const a = app.querySelector(".say .avatar"); if (a){ a.classList.remove("jump"); void a.offsetWidth; a.classList.add("jump"); } }
const cheer = () => rand(["答對了！","好厲害！","太棒了！","你好棒！"]);

/* 寶箱：點開認識新字 */
function chest(){
  const l = G.lv, cs = [...l.chars, ...l.readChars.filter(c => INFO[c])];
  render(`${header()}<div class="stage">${talk("寶箱裡藏著這一課的字，全部打開吧！")}
    <div class="detail" id="detail" hidden></div>
    <div class="chests">${cs.map(c => `<button class="chest nozy ${l.readChars.includes(c) ? "rc" : ""}" data-c="${esc(c)}" aria-label="寶箱"><b>${esc(c)}</b><small>${esc(zy(c))}</small></button>`).join("")}</div>
    <p class="muted">${l.readChars.length ? "最後幾個寶箱是只要會認的字。" : ""}</p>
    <div class="row" style="justify-content:center"><button class="btn" id="skip">直接出發</button><button class="btn primary" id="next" hidden>全部打開了，出發！</button></div></div>`);
  bindBack();
  const left = new Set(cs);
  app.querySelectorAll(".chest").forEach(b => b.onclick = () => {
    const c = b.dataset.c, i = INFO[c];
    if (!b.classList.contains("open")){ b.classList.add("open"); burst(b); sfx("pop"); collect(c); save(); }
    left.delete(c); say(c);
    const ws = lessonWords(l).filter(w => w.includes(c)).concat(allWords.filter(w => w.includes(c))), d = document.getElementById("detail");
    d.innerHTML = `<span class="bigchar nozy">${esc(c)}</span><dl><dt>注音</dt><dd>${esc(zy(c))}</dd><dt>部首</dt><dd>${esc(radLabel(i[1]))}${i[3] ? `<span class="muted">（${i[4] ? "也有字典歸在" : "教育部國語小字典歸在"}「${esc(i[3])}」部）</span>` : ""}</dd><dt>筆畫</dt><dd>${i[2]} 畫</dd>${ws.length ? `<dt>語詞</dt><dd>${uniq(ws).slice(0,3).map(w => rubyWord(w)).join("、")}</dd>` : ""}</dl>`;
    d.hidden = false;
    if (!left.size){ document.getElementById("next").hidden = false; document.getElementById("skip").hidden = true; setMsg("全部打開了！我們出發吧！"); }
  });
  const go = () => { G.si++; G.qi = 0; station(); };
  document.getElementById("next").onclick = go;
  document.getElementById("skip").onclick = go;
}

/* 射氣球：聽音找字 */
function balloon(q, done){
  const xs = [8, 38, 68];
  render(`${header()}<div class="stage">${talk("聽一聽，把對的氣球射下來！")}
    ${speakerBtn()}
    <div class="sky">${q.opts.map((o,i) => `<button class="balloon" data-o="${esc(o)}" style="left:calc(${xs[i]}% - 10px);bottom:${20 + (i%2)*40}px;animation-delay:${-i*.8}s"><span class="ball nozy" style="background:${BALLCOL[(i + G.qi) % 4]}">${esc(o)}</span><span class="str"></span></button>`).join("")}</div></div>`);
  bindBack();
  document.getElementById("play").onclick = () => say(q.t); say(q.t);
  let over = false;
  app.querySelectorAll(".balloon").forEach(b => b.onclick = () => {
    if (over) return;
    if (b.dataset.o === q.t){ over = true; b.classList.add("pop"); burst(b); sfx("ok"); setMsg(cheer() + "是「" + q.t + "」"); done(true); }
    else { b.classList.remove("no"); void b.offsetWidth; b.classList.add("no"); sfx("no"); setMsg("不是這個喔，再聽一次"); say(q.t); done(false, b.dataset.o); }
  });
}

/* 撈魚拼注音：看國字，點注音魚放進格子，最後撿聲調貝殼 */
function fishGame(q, done, inBoss){
  const p = parse(zy(q.t));
  const keys = new Set(p.syl);
  p.syl.forEach(x => [...(LOOKALIKE[x] || "")].forEach(y => keys.size < 8 && keys.add(y)));
  for (const y of shuffle([...ORDER])){ if (keys.size >= 8) break; keys.add(y); }
  const fishKeys = [...keys].sort((a,b) => ORDER.indexOf(a) - ORDER.indexOf(b));
  const filled = q.toneOnly ? p.syl.slice() : p.syl.map(() => null);
  let tone = null, tries = 0, over = false;
  const html = `
    <div class="pond">
      <div class="boat"><span class="bigchar nozy">${esc(q.t)}</span><div class="slots" id="slots"></div></div>
      ${q.toneOnly ? "" : `<div class="fishes">${fishKeys.map((k,i) => `<button class="fish" data-k="${k}" aria-label="${k}">${FISH(FISHCOL[i % FISHCOL.length])}<span>${k}</span></button>`).join("")}</div>`}
      <div class="shells">${TONES.map(t => `<button class="shell" data-t="${t.v}"><b>${t.k}</b><span>${t.n}</span></button>`).join("")}</div>
      <div class="tools"><button class="btn small" id="undo">退一格</button>${speakerBtn()}</div>
    </div>`;
  if (inBoss) inBoss(html);
  else { render(`${header()}<div class="stage">${talk(q.toneOnly ? "這個字念第幾聲？撿起對的貝殼！" : "看國字，把注音魚撈進船上的格子！")}${html}</div>`); bindBack(); }
  const slots = document.getElementById("slots");
  function draw(state){
    const nextI = filled.indexOf(null);
    slots.innerHTML = `<div class="slotcol">${filled.map((x,i) => `<span class="slot ${q.toneOnly ? "locked" : x ? "filled" : i===nextI ? "next" : ""} ${state && state.bad.includes(i) ? "wrong" : state && state.ok ? "right" : ""}">${x || ""}</span>`).join("")}</div>
      <span class="slot tone ${tone ? "filled" : nextI < 0 ? "next" : ""} ${state && state.toneBad ? "wrong" : state && state.ok ? "right" : ""}">${tone ? TONES[tone-1].k : ""}</span>`;
    app.querySelectorAll(".shell").forEach(b => b.disabled = over || filled.includes(null));
  }
  function check(){
    const bad = filled.map((x,i) => x === p.syl[i] ? -1 : i).filter(i => i >= 0), toneBad = tone !== p.tone;
    if (!bad.length && !toneBad){
      over = true; draw({ok:true, bad:[]}); burst(slots); sfx("ok"); setMsg(cheer() + zy(q.t)); say(q.t); done(true); return;
    }
    q.err = toneBad && !bad.length ? "tone" : "symbol";
    tries++; sfx("no"); draw({bad, toneBad}); done(false);
    if (tries >= 2){
      over = true; setMsg("正確的是 " + zy(q.t) + "，下次一定會！");
      p.syl.forEach((x,i) => filled[i] = x); tone = p.tone;
      setTimeout(() => { draw({ok:true, bad:[]}); say(q.t); }, 700);
      setTimeout(() => done("skip"), 2200);
      return;
    }
    setMsg(toneBad && !bad.length ? "聲調不對喔，換一個貝殼" : "紅色的魚不對，牠游走了，再試一次");
    setTimeout(() => { bad.forEach(i => filled[i] = null); if (toneBad) tone = null; draw(); }, 900);
  }
  app.querySelectorAll(".fish").forEach(b => b.onclick = () => {
    if (over) return;
    const i = filled.indexOf(null);
    if (i < 0) return;
    filled[i] = b.dataset.k; b.classList.remove("away"); void b.offsetWidth; b.classList.add("away");
    sfx("pop"); draw();
  });
  app.querySelectorAll(".shell").forEach(b => b.onclick = () => {
    if (over || filled.includes(null)) return;
    tone = +b.dataset.t; draw(); setTimeout(check, 250);
  });
  document.getElementById("undo").onclick = () => {
    if (over) return;
    if (tone){ tone = null; }
    else if (!q.toneOnly){ const i = filled.map(x => !!x).lastIndexOf(true); if (i >= 0) filled[i] = null; }
    draw();
  };
  document.getElementById("play").onclick = () => say(q.t);
  draw();
}

/* 描一描：田字格裡照筆順寫，每寫對一筆點亮一顆寶石。practice=true 是圖鑑裡的自由練習 */
let writer = null;
function padSize(){
  const w = Math.min(app.clientWidth, window.innerWidth) - 56;
  return Math.round(Math.max(220, Math.min(w, window.innerHeight * .52, 520)));
}
function writeGame(q, done, practice){
  const c = q.t, n = STROKES[c].strokes.length, size = padSize();
  render(`${practice ? `<div class="top"><button class="btn small" id="back">← 圖鑑</button><span class="spacer"></span></div>` : header()}
    <div class="stage">${talk(practice ? "想練幾次都可以！" : "跟著筆順，用手指寫寫看！")}
      <div class="writehead"><span class="zc"><span class="bigchar">${esc(c)}</span>${bpmf(zy(c))}</span><span class="muted">共 ${n} 筆</span></div>
      <div class="gems" id="gems">${Array.from({length:n}, () => "<i></i>").join("")}</div>
      <div class="pad" id="pad" style="width:${size}px;height:${size}px"></div>
      <div class="tools"><button class="btn small" id="demo">看示範</button><button class="btn small" id="redo">重寫</button>${speakerBtn()}</div></div>`);
  if (practice) document.getElementById("back").onclick = () => { try { speechSynthesis.cancel(); } catch(e){} dex(); };
  else bindBack();
  const css = getComputedStyle(document.documentElement), col = v => css.getPropertyValue(v).trim();
  writer = HanziWriter.create("pad", c, {
    width:size, height:size, padding:Math.round(size*.06),
    showCharacter:false, showOutline:true, showHintAfterMisses:2, highlightOnComplete:true,
    strokeColor:col("--ink"), outlineColor:col("--line"), highlightColor:col("--coral"), drawingColor:col("--kang"),
    drawingWidth:Math.max(18, size/16), strokeAnimationSpeed:1.2, delayBetweenStrokes:250,
    charDataLoader:(ch, onLoad) => onLoad(STROKES[ch]),
  });
  const gems = () => [...document.querySelectorAll("#gems i")];
  let mistakes = 0;
  function quiz(){
    mistakes = 0; gems().forEach(g => g.classList.remove("lit"));
    writer.quiz({
      onCorrectStroke: d => { const g = gems()[d.strokeNum]; if (g) g.classList.add("lit"); sfx("pop"); },
      onMistake: d => { mistakes++; if (d.mistakesOnStroke === 1) sfx("no"); if (d.mistakesOnStroke === 2) setMsg("看看亮起來的那一筆，從那裡開始寫"); },
      onComplete: () => {
        burst(document.getElementById("pad")); sfx("win"); say(c);
        if (practice){ setMsg(mistakes ? "寫完了！再寫一次會更漂亮" : "一筆都沒錯，太厲害了！"); return; }
        if (mistakes <= 2){ setMsg(cheer() + "「" + c + "」寫好了"); done(true); }
        else { setMsg("寫完了！這個字我們下次再多練習"); done("miss"); }
      },
    });
  }
  document.getElementById("demo").onclick = () => { setMsg("看清楚每一筆的順序喔"); writer.cancelQuiz(); writer.animateCharacter({onComplete:() => { writer.hideCharacter(); quiz(); setMsg("換你寫了！"); }}); };
  document.getElementById("redo").onclick = () => { writer.cancelQuiz(); writer.hideCharacter(); quiz(); };
  document.getElementById("play").onclick = () => say(c);
  say(c); quiz();
}

/* 看注音修小橋：語詞缺一個字，看缺字的注音選對的石頭補上 */
function bridge(q, done){
  render(`${header()}<div class="stage">${talk("橋壞了！看注音，選對的石頭補上去！")}
    <div class="river"><span class="walker" id="walker">${AVATAR}</span>
      <div class="bridge"><span class="cliffL"></span>${[...q.w].map((c,i) => i === q.pos ? `<span class="plank gap" id="gap"><span class="sentence">${zc(`<span class="blank">？</span>`, wordZy(q.w)[i])}</span></span>` : `<span class="plank"><span class="sentence">${ruby(c, wordZy(q.w)[i])}</span></span>`).join("")}<span class="cliffR"></span></div></div>
    <div class="stones nozy">${q.opts.map(o => `<button class="stone" data-o="${esc(o)}">${esc(o)}</button>`).join("")}</div></div>`);
  bindBack();
  let over = false;
  app.querySelectorAll(".stone").forEach(b => b.onclick = () => {
    if (over) return;
    if (b.dataset.o === q.t){
      over = true; const gap = document.getElementById("gap");
      gap.className = "plank fill"; gap.innerHTML = `<span class="sentence">${ruby(q.t, wordZy(q.w)[q.pos])}</span>`;
      b.style.visibility = "hidden"; sfx("ok"); setMsg(cheer() + "「" + q.w + "」"); say(q.w);
      const w = document.getElementById("walker"), river = w.parentElement;
      requestAnimationFrame(() => w.style.left = (river.clientWidth - 56) + "px");
      done(true);
    } else { b.classList.add("sink"); b.disabled = true; sfx("no"); setMsg("石頭沉下去了，換一顆試試"); done(false, b.dataset.o); }
  });
}

/* 錯字偵探：先用放大鏡點出句子裡的錯字，再選出正確的字 */
function typoGame(q, done){
  const chars = [...q.s];
  render(`${header()}<div class="stage">${talk("句子裡藏了一個錯字，用放大鏡把它找出來！")}
    <div class="case"><p class="hunt" id="hunt">${chars.map((c,i) => /[，。、！？：；「」『』（）《》…—\s]/.test(c) ? `<span class="pc">${esc(c)}</span>` : `<button class="ch" data-i="${i}">${esc(c)}</button>`).join("")}</p></div>
    <div class="fixbox" id="fix" hidden><p class="muted">「<b id="bad"></b>」應該改成哪一個字？</p>
      <div class="cards">${q.opts.map(o => `<button class="wcard" data-o="${esc(o)}">${esc(o)}</button>`).join("")}</div></div></div>`);
  bindBack();
  let found = false, over = false;
  app.querySelectorAll(".ch").forEach(b => b.onclick = () => {
    if (found) return;
    if (+b.dataset.i === q.pos){
      found = true; b.classList.add("found"); sfx("pop"); setMsg("找到了！現在把它改正");
      document.getElementById("bad").textContent = q.fake; document.getElementById("fix").hidden = false;
    } else { b.classList.remove("nope"); void b.offsetWidth; b.classList.add("nope"); sfx("no"); setMsg("這個字沒有錯喔，再找找看"); done(false); }
  });
  app.querySelectorAll("#fix .wcard").forEach(b => b.onclick = () => {
    if (over) return;
    if (b.dataset.o === q.t){
      over = true; b.classList.add("right"); const h = app.querySelector(`.ch[data-i="${q.pos}"]`);
      h.textContent = q.t; h.classList.add("fixed"); sfx("ok"); burst(h); setMsg(cheer() + "是「" + q.w + "」"); done(true);
    } else { b.classList.add("wrong"); b.disabled = true; sfx("no"); setMsg("不是這個字，再想想"); done(false, b.dataset.o); }
  });
}

/* 量詞配對：先點左邊的東西，再點右邊的量詞，三組都配對成功就過關 */
function measureGame(q, done){
  render(`${header()}<div class="stage">${talk("幫每樣東西找到對的量詞！先點左邊，再點右邊。")}
    <div class="match"><div class="mleft">${q.pairs.map((p,i) => `<button class="mitem" data-i="${i}">${esc(p.text.replace(/\[.+?\]/, "（　）"))}</button>`).join("")}</div>
      <div class="mright">${q.opts.map(o => `<button class="mword" data-o="${esc(o)}">${esc(o)}</button>`).join("")}</div></div></div>`);
  bindBack();
  let sel = null, left = q.pairs.length, missed = false;
  app.querySelectorAll(".mitem").forEach(b => b.onclick = () => {
    if (b.classList.contains("done")) return;
    app.querySelectorAll(".mitem").forEach(x => x.classList.toggle("sel", x === b)); sel = +b.dataset.i;
  });
  app.querySelectorAll(".mword").forEach(b => b.onclick = () => {
    if (sel === null || b.disabled) return;
    const p = q.pairs[sel], item = app.querySelector(`.mitem[data-i="${sel}"]`);
    if (b.dataset.o === p.ans){
      item.textContent = p.text.replace(/\[(.+?)\]/, "$1"); item.classList.remove("sel"); item.classList.add("done");
      b.disabled = true; b.classList.add("used"); sfx("pop"); sel = null; left--;
      /* 中途配錯過的話，這題已經記成答錯，配完只是往下一題走 */
      if (!left){ sfx("ok"); setMsg(missed ? "全部配對好了！" : cheer() + "全部配對正確"); done(true); }
    } else {
      b.classList.remove("nope"); void b.offsetWidth; b.classList.add("nope"); sfx("no"); setMsg(`「${p.text.replace(/\[.+?\]/, "")}」不是用「${b.dataset.o}」喔`);
      if (!missed){ missed = true; done(false); }
    }
  });
}

/* 排順序：成語拼圖（排字）和句子積木（排詞語）共用。依序點積木放進上方，點上方的積木可以退回 */
function orderGame(q, done){
  const idiom = q.kind === "idiomPuzzle";
  const pool = q.tiles.map((t,i) => ({t, i})), placed = [];
  let tries = 0, over = false;
  render(`${header()}<div class="stage">${talk(idiom ? "把字卡排成正確的成語！" : "把積木排成通順的句子！")}
    ${idiom ? `<p class="muted">提示：${esc(q.meaning)}</p>` : ""}
    <div class="tray ${idiom ? "idi" : ""}" id="tray"></div>
    <div class="pool ${idiom ? "idi" : ""}" id="pool"></div>
    <div class="tools"><button class="btn small" id="clear">全部退回</button></div></div>`);
  bindBack();
  function draw(state){
    document.getElementById("tray").innerHTML = placed.length ? placed.map((p,k) => `<button class="tile on ${state || ""}" data-k="${k}">${esc(p.t)}</button>`).join("") : `<span class="muted">點下面的${idiom ? "字卡" : "積木"}放到這裡</span>`;
    document.getElementById("pool").innerHTML = pool.map(p => `<button class="tile" data-i="${p.i}" ${placed.includes(p) ? "disabled" : ""}>${esc(p.t)}</button>`).join("");
    app.querySelectorAll("#pool .tile").forEach(b => b.onclick = () => { if (over) return; placed.push(pool.find(p => p.i === +b.dataset.i)); sfx("pop"); draw(); if (placed.length === pool.length) setTimeout(check, 250); });
    app.querySelectorAll("#tray .tile").forEach(b => b.onclick = () => { if (over) return; placed.splice(+b.dataset.k, 1); draw(); });
  }
  function check(){
    const got = placed.map(p => p.t).join("");
    if (q.answers.some(a => a.join("") === got)){
      over = true; draw("right"); sfx("ok"); burst(document.getElementById("tray"));
      setMsg(idiom ? `${cheer()}「${q.w}」：${q.meaning}` : cheer()); say(got.replace(/[，。]/g, " "));
      done(true); return;
    }
    tries++; draw("wrong"); sfx("no"); done(false);
    if (tries >= 2){
      over = true; const a = q.answers[0];
      placed.length = 0; a.forEach(t => placed.push(pool.find(p => p.t === t && !placed.includes(p))));
      setTimeout(() => { draw("right"); setMsg("正確的順序是這樣，下次一定會！"); }, 700);
      setTimeout(() => done("skip"), 2400); return;
    }
    setMsg(idiom ? "順序不太對，再排一次" : "句子不太通順，再試一次");
    setTimeout(() => { placed.length = 0; draw(); }, 900);
  }
  document.getElementById("clear").onclick = () => { if (!over){ placed.length = 0; draw(); } };
  draw();
}

/* 填空：選詞填空、成語運用、關聯詞火車共用。關聯詞的答案用「…」分成兩段，分別填進兩個空格 */
function fillGame(q, done){
  const parts = q.s.split(/\[[^\]]*\]/), nb = parts.length - 1;
  const theme = {fill:"words", idiom:"idioms", conn:"train"}[q.kind];
  const msg = {fill:"選出最適合放進句子的語詞", idiom:"哪一個成語放進句子最恰當？", conn:"選對關聯詞，把兩節車廂連起來！"}[q.kind];
  const sent = parts.map((p,i) => esc(p) + (i < nb ? `<span class="blank" data-b="${i}">？</span>` : "")).join("");
  render(`${header()}<div class="stage">${talk(msg)}
    <div class="${theme === "train" ? "trainbox" : "sentcard"}">${theme === "train" ? `<div class="train" id="train"><p class="ctext">${sent}</p></div><div class="rail"></div>` : `<p class="ctext">${sent}</p>`}</div>
    <div class="cards ${theme === "train" ? "conns" : theme}">${q.opts.map(o => `<button class="wcard" data-o="${esc(o)}">${esc(o)}</button>`).join("")}</div></div>`);
  bindBack();
  let over = false;
  app.querySelectorAll(".cards .wcard").forEach(b => b.onclick = () => {
    if (over) return;
    if (b.dataset.o === q.ans){
      over = true; b.classList.add("right"); sfx("ok");
      const seg = q.ans.split("…");
      app.querySelectorAll(".blank").forEach((x,i) => { x.textContent = nb > 1 ? (seg[i] || "") : q.ans; x.classList.add("filled"); });
      if (theme === "train"){ document.getElementById("train").classList.add("go"); setMsg(`${cheer()}這是「${q.rel}」關係的句子`); }
      else setMsg(q.kind === "idiom" ? `${cheer()}「${q.ans}」：${q.meaning}` : cheer());
      say(parts.map((p,i) => p + (i < nb ? (nb > 1 ? seg[i] : q.ans) : "")).join(""));
      done(true);
    } else { b.classList.add("wrong"); b.disabled = true; sfx("no"); setMsg(theme === "train" ? "火車開不動，換一個連結器試試" : "放進去讀讀看，好像不太對"); done(false, b.dataset.o); }
  });
}

/* 選一個答案的高年級玩法：修辭偵探（把證物卡放進對的箱子）、句子變身、成語誤用辨別 */
function pickGame(q, done){
  const cfg = {
    rhet:{msg:"這句話用了什麼修辭？把證物卡放進對的箱子！", top:`<div class="evidence"><span class="evtag">證物</span><p class="ctext">${esc(q.p)}</p></div>`, cls:"boxes"},
    transform:{msg:`句子變身：${q.label}`, top:`<div class="sentcard"><span class="evtag">${esc(q.label)}</span><p class="ctext">${esc(q.p)}</p></div>`, cls:"longs"},
    punct:{msg:"空格裡該填哪個標點符號？", top:`<div class="sentcard"><p class="ctext">${(q.p || "").split("[]").map(esc).join('<span class="blank">？</span>')}</p></div>`, cls:"boxes"},
    meaning:{msg:"想一想，選出正確的意思", top:`<div class="sentcard"><p class="ctext">${esc(q.p)}</p></div>`, cls:"longs"},
    rewrite:{msg:"哪一句的意思和它一樣？", top:`<div class="sentcard"><p class="ctext">${esc(q.p)}</p></div>`, cls:"longs"},
    idiomMeaning:{msg:"選出這個成語的意思", top:`<div class="sentcard"><p class="ctext" style="text-align:center">${esc(q.p)}</p></div>`, cls:"longs"},
    idiomUse:{msg:"三個句子裡，只有一句的成語用對了", top:`<div class="sentcard"><p class="ctext" style="text-align:center">${esc(q.p)}</p></div>`, cls:"longs"},
  }[q.kind];
  render(`${header()}<div class="stage">${talk(cfg.msg)}${cfg.top}
    <div class="${cfg.cls}">${q.opts.map(o => `<button class="pick" data-o="${esc(o)}">${esc(o)}</button>`).join("")}</div></div>`);
  bindBack();
  let over = false;
  app.querySelectorAll(".pick").forEach(b => b.onclick = () => {
    if (over) return;
    if (b.dataset.o === q.ans){
      over = true; b.classList.add("right"); sfx("ok"); burst(b);
      const ev = app.querySelector(".evidence"); if (ev) ev.classList.add("filed");
      setMsg(q.kind === "idiomUse" || q.kind === "idiomMeaning" ? `${cheer()}${q.meaning}` : q.kind === "rhet" ? `${cheer()}這是「${q.ans}」` : cheer());
      done(true);
    } else { b.classList.add("wrong"); b.disabled = true; sfx("no"); setMsg(q.kind === "rhet" ? "不是這個箱子，再看看句子的特色" : "再讀一次，想想哪裡不對"); done(false, b.dataset.o); }
  });
}

/* 漂流瓶閱讀：先點開漂流瓶拿出信，讀完回答問題；答對一題就點亮一顆寶石，三顆都亮會打開寶藏 */
function readGame(q, done){
  const r = q.r, qs = G.st[G.si].qs, n = r.qs.length;
  const lit = qs.slice(0, G.qi).filter(x => !x.retried && x.r === r).length;
  const lastOfLetter = !qs.slice(G.qi + 1).some(x => x.r === r && !x.retried);
  const letter = `<article class="letter" id="letter"><h3>${esc(r.title)}</h3><p>${showZy() ? rubyText(r.text) : esc(r.text)}</p></article>`;
  render(`${header()}<div class="stage">${talk(q.first ? "海上漂來一個瓶子，點一下打開看看！" : "回到信裡找答案吧！")}
    <div class="sea" id="sea">
      ${q.first ? `<button class="bottle" id="bottle" aria-label="打開漂流瓶"><span></span></button>` : ""}
      <div id="letterBox" ${q.first ? "hidden" : ""}>${letter}<div class="tools"><button class="speak" id="readAloud">${ICON_SPEAK}<span>念給我聽</span></button></div></div>
    </div>
    <div class="treasure" aria-label="已點亮 ${lit} 顆寶石">${Array.from({length:n}, (_,i) => `<i class="${i < lit ? "lit" : ""}"></i>`).join("")}</div>
    <div class="rq" id="rq" ${q.first ? "hidden" : ""}><p class="qtext">${esc(q.q)}</p>
      <div class="answers">${q.opts.map((o,i) => `<button class="ansbtn" data-o="${esc(o)}"><b>${"ABC"[i]}</b><span>${esc(o)}</span></button>`).join("")}</div></div></div>`);
  bindBack();
  const open = () => {
    const b = document.getElementById("bottle");
    if (b){ b.classList.add("opened"); sfx("pop"); }
    setTimeout(() => { if (b) b.remove(); document.getElementById("letterBox").hidden = false; document.getElementById("rq").hidden = false; setMsg("讀完信，再回答下面的問題"); }, b ? 450 : 0);
  };
  const bottle = document.getElementById("bottle");
  if (bottle) bottle.onclick = open;
  document.getElementById("readAloud").onclick = () => say(r.text);
  let over = false;
  app.querySelectorAll(".ansbtn").forEach(b => b.onclick = () => {
    if (over) return;
    if (b.dataset.o === q.ans){
      over = true; b.classList.add("right"); sfx("ok");
      const gem = app.querySelectorAll(".treasure i")[lit]; if (gem && !q.retried){ gem.classList.add("lit"); burst(gem); }
      setMsg(lastOfLetter && !q.retried ? "這封信的寶石全部收集到了！" : cheer()); done(true);
    } else {
      b.classList.add("wrong"); b.disabled = true; sfx("no"); setMsg("再回到信裡找一找線索"); done(false);
      document.getElementById("letter").scrollIntoView({behavior:"smooth", block:"nearest"});
    }
  });
}

/* 打魔王：答對發射星星，答錯魔王會反擊。題型混合：句子填空、錯字辨識、部首、聽語詞、拼注音 */
function bossFight(s){
  const total = s.qs.length;
  let hp = total, hearts = 3, qi = 0;
  function frame(inner, msg){
    render(`${header()}<div class="stage"><div class="arena">
      <div class="bossrow">${BOSS}<div style="display:grid;gap:6px;justify-items:start"><b>${G.lv.kind === "zy" ? "注音大魔王" : G.lv.items && DATA.bank ? "句子魔王" : "錯字魔王"}</b>
        <div class="hp">${Array.from({length:total}, (_,i) => `<i class="${i >= hp ? "gone" : ""}"></i>`).join("")}</div>
        <div class="hearts" aria-label="剩 ${hearts} 顆心">${"♥".repeat(hearts)}<span class="off">${"♥".repeat(3-hearts)}</span></div></div></div>
      ${talk(msg || (qi === 0 ? "答對就能發射星星打魔王！" : "繼續加油！"))}
      ${inner}</div></div>`);
    bindBack();
  }
  /* 每題只算一次：第一次就答對才算對，答錯過的題目之後打中魔王不加分 */
  function hit(q){
    const b = document.getElementById("boss"); hp--;
    if (!q.tot){ q.tot = true; G.right++; G.total++; }
    b.classList.add("hit"); sfx("ok");
    const seg = app.querySelectorAll(".hp i")[hp]; if (seg) seg.classList.add("gone");
    qi++;
    setTimeout(() => {
      if (hp <= 0){ b.classList.add("dead"); sfx("win"); setMsg("打敗魔王了！"); setTimeout(() => { G.si++; station(); }, 1100); }
      else ask();
    }, 1200);
  }
  function hurt(q){
    const b = document.getElementById("boss"); hearts--;
    if (!q.tot){ q.tot = true; G.total++; }
    b.classList.remove("laugh"); void b.offsetWidth; b.classList.add("laugh"); sfx("no");
    const h = app.querySelector(".hearts"); h.innerHTML = `${"♥".repeat(hearts)}<span class="off">${"♥".repeat(3-hearts)}</span>`;
    if (hearts <= 0){
      setTimeout(() => {
        frame(`<p class="bubble">魔王太強了！休息一下再挑戰吧</p><button class="btn primary" id="retry">再挑戰一次</button>`);
        document.getElementById("retry").onclick = () => { s.qs = shuffle(s.qs); bossFight(s); };
      }, 700);
      return true;
    }
    setMsg("哈哈，打不到！再想想看");
    return false;
  }
  const good = q => { markSeen(q); if (!q.badOnce) record(q, true); if (q.t){ S.mastery[q.t] = Math.min(3,(S.mastery[q.t]||0)+1); collect(q.t); } save(); };
  const bad = (q, chosen) => { if (!q.badOnce){ q.badOnce = true; record(q, false, q.kind === "sentence" ? chosen : null); } if (q.t){ G.missed.add(q.t); S.mastery[q.t] = Math.max(0,(S.mastery[q.t]||0)-1); } save(); };
  function ask(){
    const q = s.qs[qi];
    if (q.kind === "spell"){
      fishGame(q, ok => {
        if (hearts <= 0) return;
        if (ok === true){ good(q); setTimeout(() => hit(q), 600); }
        else if (ok === false){ bad(q); hurt(q); }
        else { s.qs.splice(qi, 1); s.qs.push(q); ask(); }
      }, inner => frame(inner, "看國字拼注音，拼對就攻擊！"));
      return;
    }
    let prompt = "", msg = "", answer = q.ans || q.t, wide = false;
    if (q.kind === "sentence"){
      const parts = q.s.split(/\[(.)\]/);
      prompt = `<div class="scroll"><div class="sentence">${rubyText(parts[0])}${zc(`<span class="blank">？</span>`, zy(q.t))}${rubyText(parts[2])}</div></div>`;
      msg = "把句子補完整！";
    } else if (q.kind === "radical"){
      prompt = `<div class="scroll"><span class="bigchar" style="font-size:72px">${esc(q.t)}</span></div>`;
      msg = `「${q.t}」的部首是哪一個？`; wide = true;
    } else if (q.kind === "wrongword"){
      prompt = ""; msg = "哪一個語詞的字全部寫對了？"; wide = true;
    } else if (["punct", "meaning", "rewrite"].includes(q.kind)){
      const blanks = q.p.split("[]");
      prompt = `<div class="scroll"><p class="ctext">${blanks.map(esc).join('<span class="blank">？</span>')}</p></div>`;
      msg = {punct:"空格裡該填哪個標點符號？", meaning:"想一想，選出正確的意思", rewrite:"哪一句的意思和它一樣？"}[q.kind];
      wide = true;
    } else if (q.kind === "hearword"){
      prompt = speakerBtn("聽語詞"); msg = "聽一聽，是哪一個語詞？"; wide = true;
    }
    frame(`${prompt}<div class="magic ${q.kind === "radical" ? "" : "nozy"}">${q.opts.map(o => `<button class="${wide ? "gem" : "star"}" data-o="${esc(o)}">${esc(q.kind === "radical" ? radLabel(o) : o)}</button>`).join("")}</div>`, msg);
    const play = document.getElementById("play");
    if (play){ play.onclick = () => say(q.w); say(q.w); }
    let over = false;
    app.querySelectorAll(".magic button").forEach(b => b.onclick = () => {
      if (over) return;
      if (b.dataset.o === answer){
        over = true; b.classList.add("fly"); good(q);
        say(q.kind === "sentence" ? q.s.replace(/[\[\]]/g, "") : q.w || q.t); setMsg(cheer()); setTimeout(() => hit(q), 400);
      } else {
        b.classList.add("dud"); b.disabled = true; bad(q, b.dataset.o);
        if (hurt(q)) over = true;
      }
    });
  }
  ask();
}

function finish(){
  const lv = G.lv, pct = G.total ? G.right / G.total : 1;
  const st = pct >= .9 ? 3 : pct >= .7 ? 2 : 1;
  S.stars[lv.id] = Math.max(S.stars[lv.id] || 0, st);
  const lvs = levels(S.range), nextLv = lvs[G.idx + 1];
  if (nextLv) S.at[`${DATA.grade}-${S.version}-${S.range}`] = G.idx + 1;
  save(); sfx("win");
  const shown = lv.kind === "lesson" ? lv.chars : uniq(G.st.flatMap(s => (s.qs || []).map(q => q.t))).filter(Boolean);
  render(`<div class="stage result">
    <h2>${esc(lv.title)} 過關！</h2>
    <div class="bigstars" aria-label="${st} 顆星">${"★".repeat(st)}<span class="off">${"★".repeat(3-st)}</span></div>
    <p>這一關共 ${G.count} 題，答對 ${G.right}／${G.total}</p>
    <div class="learned">${shown.map(c => `<span class="${G.missed.has(c) ? "weak" : ""}">${esc(c)}</span>`).join("")}</div>
    <p class="muted">${G.missed.size ? "紅色的字下次會再出現，多練幾次就會了。" : "每一個都答對了！"}</p>
    <div class="row" style="justify-content:center"><button class="btn" id="again">再玩一次</button>
      ${nextLv ? `<button class="btn primary" id="nextl">下一座島</button>` : `<button class="btn primary" id="tomap">回地圖</button>`}</div></div>`);
  burst(app.querySelector(".bigstars"));
  document.getElementById("again").onclick = () => start(lv, G.idx);
  const n = document.getElementById("nextl"), m = document.getElementById("tomap");
  if (n) n.onclick = () => start(nextLv, G.idx + 1);
  if (m) m.onclick = () => map();
}

async function boot(){
  if (S.grade && S.version){ if (await loadGrade(S.grade)) map(); }
  else setup();
}
boot();
