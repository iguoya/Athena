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

// ── 脚本动画：讲稿与关键帧必须对得上 ──
// 念「面积变成零」而矩阵行列式不是 0，是很隐蔽的内容 bug：
// 动画演的和语音念的不是一回事，而两边单看都正常。
for (const ch of cur.chapters) {
  for (const t of ch.topics) {
    for (const [i, ln] of (t.walkthrough?.lines ?? []).entries()) {
      const m = ln.m;
      if (!Array.isArray(m) || m.length !== 4) {
        console.error(`动画 ${t.id} 第 ${i + 1} 帧：m 必须是四个数`);
        hits++;
        continue;
      }
      const det = m[0] * m[3] - m[1] * m[2];
      // 「只要面积不是零」是条件句，不是在说这一帧压扁了——否定式要排除，
      // 否则误报会让人整个忽略这项检查（同 ADR 0014 第 5b 节的教训）。
      const negated = /不是零|不为零|非零|不等于零|不是 0|不为 0/.test(ln.say);
      const saysFlat =
        /压扁|塌成|什么都不剩/.test(ln.say) ||
        (/读数是零|面积.{0,4}零/.test(ln.say) && !negated);
      if (saysFlat && Math.abs(det) > 1e-9) {
        console.error(
          `动画 ${t.id} 第 ${i + 1} 帧：讲稿说压扁/归零，但 det=${det}——演的和念的对不上`,
        );
        hits++;
      }
      if (/回到原样/.test(ln.say) && m.join() !== "1,0,0,1") {
        console.error(`动画 ${t.id} 第 ${i + 1} 帧：讲稿说回到原样，但 m=[${m}]`);
        hits++;
      }
    }
  }
}


// ── 正文重点：标的应是语义关键，不是形式强调 ──
// 判据：把标出来的片段单独抽出来读，能不能拿到这一节的核心？
// 以指代词或连词开头的片段（「是同一件事」「这三种情况」）离开上下文就没有内容。
// 只查高亮（==...==）：着色多用于术语，「行列式」「特征值」本来就短，查了全是误报。
// 开头词也只取真正会丢主语的系动词与连词；「这/那/它」在紧邻上下文里通常成立。
const BAD_HEAD = /^(是|和|与|也|就|而|但|所以|因此|其实|正是|同样)/;
let weak = 0;
for (const ch of cur.chapters) {
  for (const t of ch.topics) {
    const fields = [
      t.overview?.asks,
      t.overview?.says,
      t.overview?.aha,
      ...(t.overview?.steps ?? []),
      t.hook?.text,
      ...(t.walkthrough?.lines ?? []).map((l) => l.say),
    ];
    for (const v of fields) {
      if (!v) continue;
      for (const m of v.matchAll(/==(.+?)==/g)) {
        const frag = m[1].trim();
        if (BAD_HEAD.test(frag) || frag.length < 6) {
          console.warn(`提示 ${t.id}：重点「${frag}」像是形式强调，单独读拿不到内容`);
          weak++;
        }
      }
    }
  }
}
if (weak) console.warn(`  ——共 ${weak} 处，见 ADR 0013 第 1 节；这是提示，不阻断构建。\n`);

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
  // 严格表述必须可核对：每节都要指到具体的外部出处（ADR 0017 第 3 节）
  const sr = t.sources;
  if (!sr || (!sr.intuition && !sr.rigorous && !sr.textbook_only)) {
    console.error(
      `课表：${t.id} 缺 sources——每节的严格表述都要能指到出处（ADR 0017 第 3 节）；` +
        `在线来源确实没有的，标 textbook_only 并写明依据哪本教材`,
    );
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
