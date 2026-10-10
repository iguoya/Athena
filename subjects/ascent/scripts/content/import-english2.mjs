// 把磨砚（subjects/english）的考研英语二内容迁进摘星（主仓库 ADR 0117、本应用 ADR 0025、0026）。
//
//   pnpm content:english2 <磨砚的 content 目录>
//
// 磨砚已退役，源目录从基线标签取：
//   git archive pre-english-merge subjects/english/content | tar -x -C <dir>
// 再指向 <dir>/subjects/english/content。
//
// 自用软件不分流（ADR 0026）：全部题目进 content/english2/，构建时打包；作者侧参考资料
// （词表、句库、教辅摘录）进 reference/english2/——进仓库，但不在 content/ 下，不打包也不被
// 当作题目扫描。来源仍逐个登记进 sources.json，出处原样保留。
//
// 脚本可重跑：每次先清空输出目录再整体重写，sources.json 只追加缺的来源。

import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { CONTENT, ROOT, readJson } from "./lib.mjs";

const OUT = join(CONTENT, "english2");
const REFERENCE = join(ROOT, "reference/english2");

// 磨砚与摘星登记的是同一个来源：沿用摘星已有的 id。
const SAME_AS = {
  "tatoeba-sentences": "tatoeba",
  "ngsl-1.2": "ngsl",
};

// 磨砚其余来源在摘星里的 use 分级：只记录授权情况（ADR 0026 起不再据此限制存放位置）。
// 每条都写明，新来源没登记就报错——登记是为了出处能核对。
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

// ── 2. 题目文件 ──
rmSync(OUT, { recursive: true, force: true });
rmSync(REFERENCE, { recursive: true, force: true });

function* files(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* files(path);
    else yield path;
  }
}

const relOf = (path) => relative(src, path).split("\\").join("/");

let total = 0;
for (const path of files(src)) {
  const rel = relOf(path);
  if (rel.startsWith("sources/") || !rel.endsWith(".json") || rel === "curriculum.json") continue;
  const data = readJson(path);
  if (!Array.isArray(data.items)) throw new Error(`${rel} 没有 items 数组，迁移脚本不认识这种文件`);
  const out = join(OUT, rel);
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, JSON.stringify(convert(data), null, 2) + "\n");
  total += data.items.length;
}

// ── 3. 课表、说明、短文正文、参考资料 ──
cpSync(join(src, "curriculum.json"), join(OUT, "curriculum.json"));
const readme = readFileSync(join(src, "README.md"), "utf8");
writeFileSync(
  join(OUT, "README.md"),
  "> 迁自磨砚（主仓库 ADR 0117、本应用 ADR 0025、0026），由 `pnpm content:english2` 生成，不手改。\n" +
    "> 下文中的 `source_refs`、`sources/catalog.json`、`sources/reference/` 在这里分别对应 `source`、\n" +
    "> `content/sources.json` 与 `reference/english2/reference/`。\n\n" +
    readme,
);
for (const path of files(src)) {
  const rel = relOf(path);
  if (!rel.endsWith(".md") || rel === "README.md" || rel.startsWith("sources/")) continue;
  mkdirSync(dirname(join(OUT, rel)), { recursive: true });
  cpSync(path, join(OUT, rel));
}
cpSync(join(src, "sources"), REFERENCE, { recursive: true });

console.log(`题目 ${total} 条 → ${relative(ROOT, OUT)}，参考资料 → ${relative(ROOT, REFERENCE)}`);
