// 把磨砚（subjects/english）的考研英语二内容迁进摘星（主仓库 ADR 0117、本应用 ADR 0025）。
//
//   pnpm content:english2 <磨砚的 content 目录>
//
// 磨砚退役后目录就没了，所以源目录从参数传入：迁移时指向 ../english/content；以后要重跑，
// 先 `git worktree add <dir> pre-english-merge` 取出基线，再指向 <dir>/subjects/english/content。
//
// 分流规则（ADR 0025 第 3 节补充）：一条题目只要有一条「内容来源」类引用（verbatim / quoted /
// adapted）指向 local-only 来源，整题进 content/private/english2/（git 忽略，不进安装包）；
// 其余进 content/english2/。selection_basis、exam_alignment 这类只说明「为什么选、对应哪条
// 考纲」，不是内容出处，不参与分流。同一个相对路径两边各写一份，加载时按路径合并。
//
// 脚本可重跑：每次先清空两个输出目录再整体重写，sources.json 只追加缺的来源。

import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync, writeFileSync, readFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { CONTENT, ROOT, readJson } from "./lib.mjs";

const OUT_PUBLIC = join(CONTENT, "english2");
const OUT_PRIVATE = join(CONTENT, "private/english2");
const CONTENT_RELATIONS = new Set(["verbatim", "quoted", "adapted"]);

// 磨砚与摘星登记的是同一个来源：沿用摘星已有的 id。
const SAME_AS = {
  "tatoeba-sentences": "tatoeba",
  "ngsl-1.2": "ngsl",
};

// 磨砚其余来源在摘星里的 use 分级。每条都写明，新来源没登记就报错，而不是悄悄猜。
// 判据：许可明确允许再分发 → bundle / bundle-sa；只作链接引用的公开说明 → quote；
// 未声明内容许可、非商用许可或第三方转存 → local-only。
const USE = {
  "voa-writing-speaking-guide": "bundle",
  "voa-lle1-course": "bundle",
  "voa-lle1-lesson2": "bundle",
  "voa-lle2-guide": "bundle",
  "voa-worksheet-nutcracker": "bundle",
  "voa-worksheet-computer-history": "bundle",
  "voa-worksheet-education-intelligence": "bundle",
  "voa-learning-english": "bundle",
  "voa-lle1-welcome": "bundle",
  "voa-job-and-career": "bundle",
  "voa-walking-wonder-drug": "bundle",
  "nawl-1.2": "bundle-sa",
  "cefr-companion": "quote",
  "yz-english-2-outline": "quote",
  awl: "local-only",
  "academic-phrasebank": "local-only",
  "netem-vocabulary": "local-only",
  "kylebing-kaoyan": "local-only",
  "kylebing-cet4": "local-only",
  "kylebing-cet6": "local-only",
  avl: "local-only",
  "bnc-coca": "local-only",
  "oxford-3000": "local-only",
  "oxford-5000": "local-only",
  "zhenghaoyang-kaoyan-english-2": "local-only",
};

const src = process.argv[2] && resolve(process.argv[2]);
if (!src || !existsSync(join(src, "curriculum.json"))) {
  console.error("用法：pnpm content:english2 <磨砚的 content 目录>（里面要有 curriculum.json）");
  process.exit(1);
}

// ── 1. 来源登记 ──
const sourcesPath = join(CONTENT, "sources.json");
const registry = readJson(sourcesPath);
const known = new Map(registry.sources.map((s) => [s.id, s]));
const catalog = readJson(join(src, "sources/catalog.json"));
const english = Array.isArray(catalog) ? catalog : catalog.sources;
let added = 0;
for (const s of english) {
  if (SAME_AS[s.id]) {
    if (!known.has(SAME_AS[s.id])) throw new Error(`摘星缺少来源 ${SAME_AS[s.id]}（${s.id} 应并到它）`);
    continue;
  }
  const use = USE[s.id];
  if (!use) throw new Error(`磨砚来源 ${s.id} 还没有 use 分级，先在 USE 表里写明`);
  if (known.has(s.id)) continue;
  const entry = {
    id: s.id,
    name: s.title,
    url: s.url,
    license: s.license,
    ...(s.license_url ? { licenseUrl: s.license_url } : {}),
    use,
    attribution: "按条目的 locator 署名并链接原文",
    notes: `迁自磨砚来源目录（主仓库 ADR 0117），核对于 ${s.checked_on ?? "未记录"}。${s.usage_note ?? ""}`.trim(),
  };
  registry.sources.push(entry);
  known.set(s.id, entry);
  added++;
}
writeFileSync(sourcesPath, JSON.stringify(registry, null, 2) + "\n");
console.log(`来源登记：新增 ${added} 条`);

const idOf = (id) => SAME_AS[id] ?? id;

/** 深拷贝并把 source_refs 改成摘星的 source，来源 id 换成摘星登记的。 */
function convert(node) {
  if (Array.isArray(node)) return node.map(convert);
  if (!node || typeof node !== "object") return node;
  const out = {};
  for (const [key, value] of Object.entries(node)) {
    if (key === "source_refs") out.source = value.map((r) => ({ ...r, source_id: idOf(r.source_id) }));
    else out[key] = convert(value);
  }
  return out;
}

/** 一条题目里所有引用（含变式里自带的）；题目自己一条都没写时用文件级的。 */
function refsOf(item, fileRefs) {
  const refs = [];
  (function walk(node) {
    if (Array.isArray(node)) return node.forEach(walk);
    if (!node || typeof node !== "object") return;
    for (const r of node.source_refs ?? []) refs.push(r);
    Object.values(node).forEach(walk);
  })(item);
  return item.source_refs?.length ? refs : [...refs, ...fileRefs];
}

const isPrivate = (refs) =>
  refs.some((r) => CONTENT_RELATIONS.has(r.relation) && known.get(idOf(r.source_id))?.use === "local-only");

// ── 2. 题目文件按条分流 ──
rmSync(OUT_PUBLIC, { recursive: true, force: true });
rmSync(OUT_PRIVATE, { recursive: true, force: true });

function* files(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* files(path);
    else yield path;
  }
}

const write = (root, rel, data) => {
  const path = join(root, rel);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(data, null, 2) + "\n");
};

const privateIndex = {};
const wentPublic = new Set();
let totals = { public: 0, private: 0 };
for (const path of files(src)) {
  const rel = relative(src, path).replaceAll("\\", "/");
  if (rel.startsWith("sources/") || !rel.endsWith(".json") || rel === "curriculum.json") continue;
  const data = readJson(path);
  if (!Array.isArray(data.items)) throw new Error(`${rel} 没有 items 数组，迁移脚本不认识这种文件`);
  const fileRefs = data.source_refs ?? [];
  const pub = [];
  const priv = [];
  for (const item of data.items) (isPrivate(refsOf(item, fileRefs)) ? priv : pub).push(item);
  const header = convert({ ...data, items: undefined });
  delete header.items;
  if (pub.length) {
    write(OUT_PUBLIC, rel, { ...header, items: pub.map(convert) });
    wentPublic.add(rel);
  }
  if (priv.length) {
    write(OUT_PRIVATE, rel, { ...header, items: priv.map(convert) });
    privateIndex[rel] = priv.map((item) => item.id);
  }
  totals.public += pub.length;
  totals.private += priv.length;
}

// ── 3. 课表、说明、短文正文、参考资料 ──
cpSync(join(src, "curriculum.json"), join(OUT_PUBLIC, "curriculum.json"));
const readme = readFileSync(join(src, "README.md"), "utf8");
writeFileSync(
  join(OUT_PUBLIC, "README.md"),
  "> 迁自磨砚（主仓库 ADR 0117、本应用 ADR 0025），由 `pnpm content:english2` 生成，不手改。\n" +
    "> 引用了只能本机用的来源的题目在 `content/private/english2/` 的同一路径下，清单见 `private-index.json`；\n" +
    "> 下文中的 `source_refs`、`sources/catalog.json` 在这里分别对应 `source` 与 `content/sources.json`。\n\n" +
    readme,
);
for (const path of files(src)) {
  const rel = relative(src, path).replaceAll("\\", "/");
  if (!rel.endsWith(".md") || rel === "README.md" || rel.startsWith("sources/")) continue;
  // 短文正文跟着同名 JSON 走：JSON 里有公开题就放公开那边，否则放本机。
  const sibling = rel.replace(/\.md$/, ".json");
  const root = wentPublic.has(sibling) || !existsSync(join(src, sibling)) ? OUT_PUBLIC : OUT_PRIVATE;
  mkdirSync(dirname(join(root, rel)), { recursive: true });
  cpSync(path, join(root, rel));
}
// 磨砚的参考资料（词表、句库、VOA、教辅摘录）是写题时的作者侧对照，许可多半没声明，整体进本机。
cpSync(join(src, "sources"), join(OUT_PRIVATE, "sources"), { recursive: true });

write(OUT_PUBLIC, "private-index.json", {
  about:
    "只在本机 content/private/english2/ 的题目清单（ADR 0025 第 3 节补充）：本机没有这些文件时界面据此提示缺了多少，而不是当它们不存在。",
  files: privateIndex,
});

console.log(
  `题目：公开 ${totals.public} 条 → ${relative(ROOT, OUT_PUBLIC)}，本机 ${totals.private} 条 → ${relative(ROOT, OUT_PRIVATE)}`,
);
