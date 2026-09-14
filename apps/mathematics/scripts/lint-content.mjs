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
/** 练习题位置分布的统计文字，最后随通过信息一起打印 */
let drillStat = "";
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

// ── 练习题：正确答案位置不得过于集中（同诊断题那条教训）──
// 检查的是**渲染之后**的顺序：drills.ts 按题目 id 做确定性打乱，
// 所以源文件里怎么排不重要，用户看到的那个顺序才重要。这里复刻同一个算法。
function orderOptions(options, seed, idx) {
  const right = options.find((o) => o.ok);
  if (!right || options.length < 2) return options;
  const rest = options.filter((o) => o !== right);
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  const pos = (Math.abs(h) + idx) % options.length;
  return [...rest.slice(0, pos), right, ...rest.slice(pos)];
}

for (const pass of [1, 2]) {
  const slots = new Map();
  let total = 0;
  const sets = [];
  for (const ch of cur.chapters) {
    for (const t of ch.topics) if (t.drills) sets.push([t.drills, t.id]);
    if (ch.checkpoint) sets.push([ch.checkpoint, ch.id]);
  }
  for (const [set, ns] of sets) {
    // 序号要按「这一遍实际显示出来的次序」算，与 renderDrills 里一致
    const shown = set.items.filter((x) => (x.pass ?? 2) <= pass);
    for (const [idx, it] of shown.entries()) {
      if (!it.options) continue;
      const k = orderOptions(it.options, ns, idx).findIndex((o) => o.ok);
      if (k < 0) {
        if (pass === 2) {
          console.error(`练习题：${it.id} 没有标出正确选项`);
          hits++;
        }
        continue;
      }
      slots.set(k, (slots.get(k) ?? 0) + 1);
      total++;
    }
  }
  for (const [k, n] of slots) {
    if (total >= 6 && n > total * 0.5) {
      console.error(
        `练习题：第 ${pass} 遍可见的 ${total} 道里有 ${n} 道正确答案落在第 ${k + 1} 位` +
          `（超过一半），会让人能按位置蒙`,
      );
      hits++;
    }
  }
  const line = `第${pass}遍 ${total} 题 ${[...slots.entries()]
    .sort()
    .map(([k, n]) => `第${k + 1}位×${n}`)
    .join(" ")}`;
  drillStat = drillStat ? `${drillStat}；${line}` : `练习 ${line}`;
}

// ── 标题：术语作主标题，直觉说法作副标题（ADR 0021）──────────────
// 一次改完还不够，下次新增又会滑回口语标题——这条必须机械兜住。
// 判据：主标题是**名词短语**，不是句子。误报时改标题，不放宽规则:
// 真的需要一个句子当标题，说明那句话属于 plain_title。
const TITLE_SPOKEN = [
  /[？?]/, /吗|呢|啦|吧/, /怎么|为什么|哪些|哪个|哪一|什么|多少|几倍|几维/,
  /能不能|是不是|有没有|会不会/, /了$/, /的$/,
];

for (const [kind, list] of [
  ["章", cur.chapters],
  ["节", topics],
]) {
  for (const n of list) {
    if (!n.plain_title) {
      console.error(
        `标题：${kind}「${n.title}」缺 plain_title——只有术语会把人挡在门外（ADR 0021 第 4 节）`,
      );
      hits++;
    }
    for (const re of TITLE_SPOKEN) {
      const m = n.title.match(re);
      if (m) {
        console.error(
          `标题：${kind}「${n.title}」里的「${m[0]}」是口语/疑问说法——` +
            `主标题要用规范术语的名词短语，这句话应该放进 plain_title`,
        );
        hits++;
        break;
      }
    }
    // 术语是名词短语，长到一句话的程度就不是术语了
    if (n.title.length > 14) {
      console.error(`标题：${kind}「${n.title}」有 ${n.title.length} 字，术语标题不该这么长`);
      hits++;
    }
  }
}

// ── 题目出处（ADR 0019）──────────────────────────────────────────
// 自造题没有难度校准，做对了说明不了什么——检验器本身不可信，反而加固
// 流畅性错觉。所以每道判分的题都要指得到一个真实出处。
//
// **这份名单只能变短，不能变长。** 它是 ADR 0019 落地时已经存在的 35 道
// 无出处存量题；改动其中任何一道，就要顺手给它补出处并从这里划掉。
// 新增的题一律不得进这份名单——加进来 lint 就白做了。
const LEGACY_UNSOURCED = new Set([
  "math.linalg.transform2d::t1",
  "math.linalg.transform2d::t2",
  "math.linalg.transform2d::t3",
  "math.linalg.compose::c1",
  "math.linalg.compose::c2",
  "math.linalg.compose::c3",
  "math.linalg.determinant::d1",
  "math.linalg.determinant::d2",
  "math.linalg.determinant::d3",
  "math.linalg.determinant::d4",
  "math.linalg.determinant::d5",
  "math.linalg.inverse::i1",
  "math.linalg.inverse::i2",
  "math.linalg.inverse::i3",
  "compose_and_undo::c1",
  "compose_and_undo::c2",
  "compose_and_undo::c3",
  "compose_and_undo::c4",
  "math.linalg.solve::s1",
  "math.linalg.solve::s2",
  "math.linalg.solve::s3",
  "math.linalg.solve::s4",
  "math.linalg.rank::r1",
  "math.linalg.rank::r2",
  "math.linalg.rank::r3",
  "math.linalg.rank::r4",
  "math.linalg.span::p1",
  "math.linalg.span::p2",
  "math.linalg.span::p3",
  "math.linalg.kernel::k1",
  "math.linalg.kernel::k2",
  "math.linalg.kernel::k3",
  "math.linalg.eigen::e1",
  "math.linalg.eigen::e2",
  "math.linalg.eigen::e3",
]);

const SOURCE_KINDS = new Set(["verbatim", "adapted", "authored"]);

/** 一处出处的合法性；`where` 用于报错定位 */
function checkSource(src, where, required) {
  if (!src) {
    if (required) {
      console.error(`出处：${where} 没有 source——ADR 0019 第 1 节要求每道判分的题都能指到出处`);
      hits++;
    }
    return null;
  }
  if (!SOURCE_KINDS.has(src.kind)) {
    console.error(`出处：${where} 的 kind「${src.kind}」不是 verbatim / adapted / authored`);
    hits++;
    return null;
  }
  if (src.kind === "authored") {
    // 自造是例外不是默认，要说得出为什么外部题库覆盖不到
    if (!src.why) {
      console.error(`出处：${where} 标了 authored 却没写 why——自造是例外，要说明为什么没有现成的可用`);
      hits++;
    }
  } else {
    if (!src.site && !src.ref) {
      console.error(`出处：${where} 是 ${src.kind}，但没说改编自哪里`);
      hits++;
    }
    // 假出处比自造更糟：使用者按图索骥扑一次空，从此不再信任何一条出处
    if (src.url && !/^https?:\/\//.test(src.url)) {
      console.error(`出处：${where} 的 url「${src.url}」不是可点开的链接`);
      hits++;
    }
    if (src.kind === "adapted" && !src.note) {
      console.error(`出处：${where} 是 adapted，要在 note 里写清改了什么`);
      hits++;
    }
  }
  return src.kind;
}

let sourced = 0;
let authored = 0;
let legacyLeft = 0;
for (const ch of cur.chapters) {
  const sets = [];
  for (const t of ch.topics) if (t.drills) sets.push([t.drills, t.id]);
  if (ch.checkpoint) sets.push([ch.checkpoint, ch.id]);

  for (const [set, ns] of sets) {
    let localAuthored = 0;
    let localTotal = 0;
    for (const it of set.items) {
      const tag = `${ns}::${it.id}`;
      // 答对那一刻是最该讲清楚的时刻。解释可以写在题级 why，也可以写在正确选项的
      // why 上（现有内容全用后者）；两处都没有，答对后就只剩一个「对。」
      // 这一条与出处无关，存量题同样要查，所以放在 legacy 豁免之前。
      const rightOpt = (it.options ?? []).find((o) => o.ok);
      if (!it.why && !rightOpt?.why) {
        console.error(`练习题：${tag} 答对后没有解释——题级 why 与正确选项的 why 都是空的`);
        hits++;
      }
      if (!it.source && LEGACY_UNSOURCED.has(tag)) {
        legacyLeft++;
        continue;
      }
      if (it.source && LEGACY_UNSOURCED.has(tag)) {
        console.error(`出处：${tag} 已经补上出处，请把它从 lint 的 LEGACY_UNSOURCED 名单里删掉`);
        hits++;
      }
      const kind = checkSource(it.source, tag, true);
      if (!kind) continue;
      localTotal++;
      sourced++;
      if (kind === "authored") {
        localAuthored++;
        authored++;
      }
    }
    // 配额：自造过半，这一节的练习就整体失去校准（ADR 0019 第 3 节）
    if (localTotal >= 2 && localAuthored * 2 > localTotal) {
      console.error(
        `出处：${ns} 的 ${localTotal} 道题里有 ${localAuthored} 道是自造的（过半）——` +
          `ADR 0019 第 3 节要求自造不超过半数`,
      );
      hits++;
    }
  }
}

// ── 两个视图必须对得上（ADR 0020）────────────────────────────────
// 「不要割裂两种关系」不能靠写作时自觉：每条严谨陈述都要指得回直觉侧讲同一件事
// 的那一段，指到不存在的段落说明两侧内容脱节了。
const FORMAL_KINDS = new Set(["definition", "theorem", "property", "method", "term"]);

/** 这一节的直觉侧实际有哪些锚点——pairs 只能指向真的存在的那些 */
function intuitiveAnchors(t) {
  const a = new Set();
  if (t.hook) a.add("s-hook");
  if (t.overview?.asks) a.add("ov-asks");
  if (t.overview?.says) a.add("ov-says");
  if (t.overview?.steps?.length) a.add("ov-steps");
  if (t.overview?.aha) a.add("ov-aha");
  if (t.walkthrough) a.add("s-walk");
  if (t.widget) a.add("s-widget");
  if ((t.experiments ?? []).some((e) => e.options?.length)) a.add("s-ask");
  return a;
}

let formalTopics = 0;
let formalEntries = 0;
for (const ch of cur.chapters) {
  for (const t of ch.topics) {
    if (!t.formal) continue;
    formalTopics++;
    const anchors = intuitiveAnchors(t);
    const seen = new Set();
    for (const e of t.formal.entries ?? []) {
      formalEntries++;
      const where = `${t.id}::严谨 ${e.id}`;
      if (seen.has(e.id)) {
        console.error(`严谨表述：${where} 的 id 重复`);
        hits++;
      }
      seen.add(e.id);
      if (!FORMAL_KINDS.has(e.kind)) {
        console.error(`严谨表述：${where} 的 kind「${e.kind}」不在定义/定理/性质/计算方法/术语之内`);
        hits++;
      }
      if (!e.title || !e.statement) {
        console.error(`严谨表述：${where} 缺标题或陈述`);
        hits++;
      }
      // 配对：这是「不割裂」的机械保证，缺一不可
      if (!e.pairs) {
        console.error(`严谨表述：${where} 没有 pairs——每条都要指回直觉侧讲同一件事的那一段`);
        hits++;
      } else if (!anchors.has(e.pairs)) {
        console.error(
          `严谨表述：${where} 的 pairs「${e.pairs}」在这一节的直觉侧不存在` +
            `（本节可用的是 ${[...anchors].join("、") || "无"}）——两侧脱节了`,
        );
        hits++;
      }
      if (!e.plain) {
        console.error(
          `严谨表述：${where} 没有 plain——写不出「换成图上的话怎么说」，` +
            `说明这条在直觉侧没有对应`,
        );
        hits++;
      } else if (e.plain.length > 80) {
        // plain 是一句话的接缝，写长了就是在严谨视图里再讲一遍直觉（ADR 0020 第 3 节）
        console.error(`严谨表述：${where} 的 plain 有 ${e.plain.length} 字，太长了——它是一句话的接缝，不是第二份讲解`);
        hits++;
      }
      checkSource(e.source, where, true);
    }
    if (!(t.formal.entries ?? []).length) {
      console.error(`严谨表述：${t.id} 有 formal 但没有条目`);
      hits++;
    }
  }
}

const formalStat = `严谨视图 ${formalTopics}/${topics.length} 节（${formalEntries} 条）`;

// ── 标准例题（ADR 0019 第 4 节）──
let exCount = 0;
for (const ch of cur.chapters) {
  for (const t of ch.topics) {
    for (const e of t.examples ?? []) {
      exCount++;
      const where = `${t.id}::例题 ${e.id}`;
      checkSource(e.source, where, true);
      if (!e.given || !e.answer) {
        console.error(`例题：${where} 缺题干或结论`);
        hits++;
      }
      if (!(e.steps ?? []).length) {
        console.error(`例题：${where} 没有解题步骤——例题的价值就在完整解答`);
        hits++;
      }
      for (const [i, st] of (e.steps ?? []).entries()) {
        // 只给「怎么算」不给「为什么可以这么算」，例题就退化成了答案
        if (!st.do || !st.why) {
          console.error(`例题：${where} 第 ${i + 1} 步缺 do 或 why（ADR 0019 第 4 节要求 why 必填）`);
          hits++;
        }
      }
    }
  }
}

const sourceStat =
  `出处 ${sourced} 题（自造 ${authored}）` +
  (legacyLeft ? `，另有 ${legacyLeft} 道存量待补` : "，存量已补完") +
  `；例题 ${exCount} 道`;

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
      // 否定式一律不算断言：「只要面积不是零」「先看没压扁的情形」都在描述反面。
      // 这一条已经误报过三次，宁可漏报也不要让人整个忽略这项检查。
      const negated =
        /不是零|不为零|非零|不等于零|不是 0|不为 0|[没未不]压扁|[没未不]会压扁/.test(ln.say);
      const saysFlat =
        !negated && (/压扁|塌成|什么都不剩|读数是零|面积.{0,4}零/.test(ln.say));
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
    `诊断 ${total} 题，位置分布 ${[...slots.entries()].sort().map(([k, n]) => `第${k + 1}位×${n}`).join(" ")}；` +
    drillStat + "；" + sourceStat + "；" + formalStat + "。",
);
