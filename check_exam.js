// 照月考測驗卷規格檢查 game/exam/g*.json：node check_exam.js <kg-exam.js 路徑>
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const el = () => ({ style: {}, appendChild() {}, setAttribute() {}, classList: { add() {}, remove() {}, toggle() {} } });
global.window = global; global.document = { createElement: el, head: el(), body: el(), getElementById: () => null, documentElement: el() };
global.localStorage = { getItem: () => null, setItem() {} }; global.location = { pathname: '/guoyu-island/game/' };
eval(src);
let errs = [], n = 0;
for (let g = 1; g <= 6; g++) {
  const all = JSON.parse(fs.readFileSync(`game/exam/g${g}.json`, 'utf8'));
  for (const [pub, B] of Object.entries(all)) {
    const tag = `${g}-${pub}`, units = new Set(B.papers.flatMap(p => p.units || [])), per = {};
    const titles = B.papers.map(p => p.title); if (new Set(titles).size !== titles.length) errs.push(tag + ' 試卷標題重複');
    for (const q of B.bank) {
      n++;
      if (!['tf', 'choice', 'fill'].includes(q.type)) errs.push(tag + ' type ' + q.type);
      if (!units.has(q.unit)) errs.push(tag + ' unit 不在試卷：' + q.unit);
      if (!q.explain) errs.push(tag + ' 沒有解說');
      (per[q.unit] = per[q.unit] || { tf: 0, choice: 0, fill: 0 })[q.type]++;
      if (q.type === 'choice') {
        if (q.choices.length !== 4) errs.push(tag + ' 選項不是 4 個：' + q.q);
        if (new Set(q.choices).size !== q.choices.length) errs.push(tag + ' 選項重複：' + q.q);
        if (!q.choices.includes(q.answer)) errs.push(tag + ' 答案不在選項：' + q.q);
      }
      if (q.type === 'tf' && typeof q.answer !== 'boolean') errs.push(tag + ' tf 答案不是布林');
      if (q.type === 'fill') {
        if (!String(q.answer).trim()) errs.push(tag + ' 填充答案空白');
        if (!KGExam._same(q.answer, q.answer)) errs.push(tag + ' _same 失敗：' + q.q);
        if (q.chips && (!q.chips.includes(q.answer) || new Set(q.chips).size !== q.chips.length)) errs.push(tag + ' 字卡有誤：' + q.q);
        if (q.chips && q.chips.filter(c => KGExam._same(c, q.answer)).length !== 1) errs.push(tag + ' 字卡有兩個對的：' + q.q);
      }
    }
    for (const u of units) {
      const s = per[u] || { tf: 0, choice: 0, fill: 0 };
      if (s.tf + s.choice + s.fill < 25 || !s.tf || !s.choice || !s.fill) errs.push(`${tag} 單元題數不足：${u} ${JSON.stringify(s)}`);
    }
    const tfs = B.bank.filter(q => q.type === 'tf'), tr = tfs.filter(q => q.answer).length / tfs.length;
    if (tr < .35 || tr > .65) errs.push(`${tag} 是非題對錯比例 ${tr.toFixed(2)}`);
    for (const p of B.papers) {
      const bank = B.bank.filter(q => !p.units || p.units.includes(q.unit));
      for (let k = 0; k < 30; k++) {
        const s = KGExam._build(bank, p.count);
        const c = { tf: s.tf.length, choice: s.choice.length, fill: s.fill.length };
        if (!c.tf || !c.choice || !c.fill || c.tf + c.choice + c.fill !== p.count) { errs.push(`${tag} ${p.title} 抽題 ${JSON.stringify(c)}`); break; }
      }
    }
  }
}
console.log('題目', n, '錯誤', errs.length); console.log(errs.slice(0, 30).join('\n'));
