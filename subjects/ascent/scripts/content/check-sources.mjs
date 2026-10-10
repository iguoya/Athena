// Check that every word and sentence under content/ names a source registered in content/sources.json (ADR 0019),
// and that nothing from a local-only source sits outside content/private/.
// 考研英语二（english2/，ADR 0025）的题目另按题目查：出处写在 source 数组里，带关系与定位。
//
//   pnpm content:check

import { readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { CONTENT, readJson } from "./lib.mjs";

const sources = new Map(readJson(join(CONTENT, "sources.json")).sources.map((s) => [s.id, s]));
const errors = [];
let items = 0;

function* jsonFiles(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) yield* jsonFiles(path);
    else if (name.endsWith(".json") && name !== "sources.json") yield path;
  }
}

// 英语二题目：内容来源类引用（照录/摘录/改写）决定能不能公开；选材依据、考纲对应只是说明。
const CONTENT_RELATIONS = new Set(["verbatim", "quoted", "adapted"]);
const KNOWN_RELATIONS = new Set([...CONTENT_RELATIONS, "authored", "selection_basis", "exam_alignment", "see_also"]);

/** 一道英语二题目连同它的变式：自己没写出处就用文件级的。 */
function checkEnglish2Item(item, fileRefs, at, isPrivate) {
  const refs = item.source?.length ? item.source : fileRefs;
  if (!refs.length) errors.push(`${at} 没有出处`);
  for (const ref of refs) {
    const source = sources.get(ref.source_id);
    if (!source) errors.push(`${at} 的出处没有登记（${ref.source_id ?? "空"}）`);
    if (!KNOWN_RELATIONS.has(ref.relation)) errors.push(`${at} 的出处关系「${ref.relation ?? "空"}」不认识`);
    if (source?.use === "local-only" && CONTENT_RELATIONS.has(ref.relation) && !isPrivate)
      errors.push(`${at} 的内容来自只能本机用的 ${ref.source_id}，不能放在 private/ 外面`);
  }
  for (const variant of item.variants ?? []) {
    for (const ref of variant.source ?? []) {
      if (!sources.has(ref.source_id)) errors.push(`${at} 的变式出处没有登记（${ref.source_id}）`);
      if (sources.get(ref.source_id)?.use === "local-only" && CONTENT_RELATIONS.has(ref.relation) && !isPrivate)
        errors.push(`${at} 的变式内容来自只能本机用的 ${ref.source_id}，不能放在 private/ 外面`);
    }
  }
}

for (const file of jsonFiles(CONTENT)) {
  const rel = relative(CONTENT, file).replaceAll("\\", "/");
  const isPrivate = rel.startsWith("private/");
  // 磨砚带过来的作者侧参考资料（词表、句库原样转存），不是题目也不是句库。
  if (rel.startsWith("private/english2/sources/")) continue;
  if (/^(private\/)?english2\//.test(rel)) {
    const data = readJson(file);
    if (!Array.isArray(data.items)) continue; // 课表、private-index
    for (const item of data.items) {
      items++;
      checkEnglish2Item(item, data.source ?? [], `${rel}: ${item.id}`, isPrivate);
    }
    continue;
  }
  const data = readJson(file);
  const list = data.sentences ?? (rel.includes("vocab/") && rel.endsWith("words.json") ? data.words : null);
  if (!Array.isArray(list)) continue;
  for (const item of list) {
    items++;
    const id = item.source ?? data.source;
    const source = sources.get(id);
    const at = `${rel}: ${item.id ?? item.word}`;
    if (!source) errors.push(`${at} 的出处没有登记（${id ?? "空"}）`);
    else if (source.use === "local-only" && !isPrivate)
      errors.push(`${at} 来自只能本机用的 ${id}，不能放在 private/ 外面`);
  }
}

if (errors.length) {
  console.error(errors.slice(0, 50).join("\n"));
  console.error(`共 ${errors.length} 处问题`);
  process.exit(1);
}
console.log(`出处检查通过：${items} 条都有登记的来源`);
