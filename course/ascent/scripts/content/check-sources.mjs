// Check that every word and sentence under content/ names a source registered in content/sources.json (ADR 0019).
// 自用软件不按授权限制存放位置（ADR 0026）：只查出处登记过、关系认得，不再拦「只能本机用」。
// 考研英语二（english2/，ADR 0025）的题目按题目查：出处写在 source 数组里，带关系与定位。
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

const KNOWN_RELATIONS = new Set(["verbatim", "quoted", "adapted", "authored", "selection_basis", "exam_alignment", "see_also"]);

/** 一道英语二题目连同它的变式：自己没写出处就用文件级的。 */
function checkEnglish2Item(item, fileRefs, at) {
  const refs = item.source?.length ? item.source : fileRefs;
  if (!refs.length) errors.push(`${at} 没有出处`);
  for (const ref of [...refs, ...(item.variants ?? []).flatMap((v) => v.source ?? [])]) {
    if (!sources.has(ref.source_id)) errors.push(`${at} 的出处没有登记（${ref.source_id ?? "空"}）`);
    if (!KNOWN_RELATIONS.has(ref.relation)) errors.push(`${at} 的出处关系「${ref.relation ?? "空"}」不认识`);
  }
}

for (const file of jsonFiles(CONTENT)) {
  const rel = relative(CONTENT, file).split("\\").join("/");
  if (rel.startsWith("english2/")) {
    const data = readJson(file);
    if (!Array.isArray(data.items)) continue; // 课表
    for (const item of data.items) {
      items++;
      checkEnglish2Item(item, data.source ?? [], `${rel}: ${item.id}`);
    }
    continue;
  }
  const data = readJson(file);
  const list = data.sentences ?? (rel.includes("vocab/") && rel.endsWith("words.json") ? data.words : null);
  if (!Array.isArray(list)) continue;
  for (const item of list) {
    items++;
    const id = item.source ?? data.source;
    if (!sources.has(id)) errors.push(`${rel}: ${item.id ?? item.word} 的出处没有登记（${id ?? "空"}）`);
  }
}

if (errors.length) {
  console.error(errors.slice(0, 50).join("\n"));
  console.error(`共 ${errors.length} 处问题`);
  process.exit(1);
}
console.log(`出处检查通过：${items} 条都有登记的来源`);
