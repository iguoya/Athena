// 内容 lint：扫描 ADR 0013 第 1 节与 ADR 0015 第 5 节的禁用表达。
// 两类都可机械检查，不靠人工自觉。
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

// ADR 0013：数学写作里让读者归因于「我笨」的措辞
const WRITING = ["显然", "容易看出", "不难证明", "只需注意到", "简单的计算", "众所周知", "读者自证", "易知", "不难发现"];
// ADR 0015 第 5 节：针对学习者本人的贬低与施压。
// 用正则而非裸串：「只剩下平方项」是在描述数学，「只剩 30 天」才是稀缺焦虑。
const PUA = [
  /这都不会/, /这么简单还/, /别人都(会|做对)/, /百分之[零一二三四五六七八九十]+的人都/,
  /就别想考/, /再不抓紧/, /还不会就晚了/, /考不上/,
  /只剩\s*[0-9〇一二三四五六七八九十百]+\s*(天|周|个?月)/,
  /来不及了/, /你怎么(还|连)/,
];

const files = ["content/curriculum.json", "content/diagnostics.json"];
for (const d of ["content"]) {
  for (const f of readdirSync(join(root, d))) {
    const p = `${d}/${f}`;
    if (f.endsWith(".json") && !files.includes(p)) files.push(p);
  }
}

let hits = 0;
for (const f of files) {
  const text = readFileSync(join(root, f), "utf8");
  const lines = text.split("\n");
  lines.forEach((line, i) => {
    for (const w of WRITING) {
      if (line.includes(w)) {
        console.error(`${f}:${i + 1}  [写作禁用词] 「${w}」\n    ${line.trim().slice(0, 100)}`);
        hits++;
      }
    }
    for (const re of PUA) {
      const m = line.match(re);
      if (m) {
        console.error(`${f}:${i + 1}  [PUA 式表达] 「${m[0]}」\n    ${line.trim().slice(0, 100)}`);
        hits++;
      }
    }
  });
}

// ── 诊断题：正确答案的位置不得过于集中 ──
// 全部落在同一位置时，人会按位置选，诊断就分不清真懂还是蒙对。
const diag = JSON.parse(readFileSync(join(root, "content/diagnostics.json"), "utf8"));
const slots = new Map();
let total = 0;
for (const g of diag.groups) {
  for (const it of g.items) {
    const k = it.options.findIndex((o) => o.ok);
    if (k < 0) {
      console.error(`诊断题：${g.id}/${it.id} 没有标出正确选项`);
      hits++;
      continue;
    }
    slots.set(k, (slots.get(k) ?? 0) + 1);
    total++;
  }
}
for (const [k, n] of slots) {
  if (n > total * 0.5) {
    console.error(
      `诊断题：${n}/${total} 道题的正确答案都在第 ${k + 1} 个位置（超过一半）。` +
        `固定位置会让人按位置选，诊断分不清真懂还是蒙对。`,
    );
    hits++;
  }
}

// ── 课表结构校验（ADR 0008 后果一节要求的构建期检查）──
const cur = JSON.parse(readFileSync(join(root, "content/curriculum.json"), "utf8"));
const topics = cur.chapters.flatMap((c) => c.topics);
const ids = new Set(topics.map((t) => t.id));

for (const t of topics) {
  for (const r of t.requires ?? []) {
    if (!ids.has(r)) {
      console.error(`课表：${t.id} 的先修 ${r} 不存在`);
      hits++;
    }
  }
  if (!t.textbook_ref || !t.syllabus_ref) {
    console.error(`课表：${t.id} 缺教材或大纲坐标（ADR 0009 第 1 节要求必填）`);
    hits++;
  }
  if (!t.overview) {
    console.error(`课表：${t.id} 缺 overview 层（ADR 0012 第 1 节）`);
    hits++;
  }
}

// 拓扑排序：先修图不能有环，否则路径不可解
let done = new Set();
let todo = [...topics];
let layers = 0;
while (todo.length) {
  const ready = todo.filter((t) => (t.requires ?? []).every((r) => done.has(r)));
  if (!ready.length) {
    console.error(`课表：先修图存在环，这些节点排不进去 → ${todo.map((t) => t.id).join(", ")}`);
    hits++;
    break;
  }
  ready.forEach((t) => done.add(t.id));
  todo = todo.filter((t) => !done.has(t.id));
  layers++;
}

if (hits) {
  console.error(`\n共 ${hits} 处。见 ADR 0013 第 1 节、ADR 0015 第 5 节、ADR 0008。`);
  process.exit(1);
}
console.log(
  `内容检查通过：${files.length} 个文件无禁用表达；` +
    `课表 ${cur.chapters.length} 章 ${topics.length} 节，先修图拓扑可解（${layers} 层）；` +
    `诊断 ${total} 题，正确答案位置分布 ${[...slots.entries()].sort().map(([k, n]) => `第${k + 1}位×${n}`).join(" ")}。`,
);
