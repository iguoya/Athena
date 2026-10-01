// Check that every word and sentence under content/ names a source registered in content/sources.json (ADR 0019),
// and that nothing from a local-only source sits outside content/private/.
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

for (const file of jsonFiles(CONTENT)) {
  const rel = relative(CONTENT, file).replaceAll("\\", "/");
  const isPrivate = rel.startsWith("private/");
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
