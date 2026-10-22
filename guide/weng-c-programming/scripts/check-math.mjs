// 公式自检：课堂脚本里每一条行内 $...$ 的 LaTeX 都必须能被 KaTeX 渲染。
// 不能渲染的公式在界面上会变成红字，读者以为是书错了——所以放进 build。
// 跑法：node scripts/check-math.mjs
import * as esbuild from "esbuild";
import katex from "katex";
import { mkdtempSync, readFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(mkdtempSync(join(tmpdir(), "macros-")), "macros.mjs");
await esbuild.build({ absWorkingDir: root, entryPoints: ["src/macros.ts"], bundle: true, format: "esm", outfile: out, logLevel: "error" });
const { MACROS } = await import(pathToFileURL(out).href);
const out2 = join(mkdtempSync(join(tmpdir(), "inline-")), "inline.mjs");
await esbuild.build({ absWorkingDir: root, entryPoints: ["src/splitInline.ts"], bundle: true, format: "esm", outfile: out2, logLevel: "error" });
const { splitInline } = await import(pathToFileURL(out2).href);

const dir = join(root, "content", "lessons");
let bad = 0;
let total = 0;
const seen = new Map();
const tryRender = (tex, where, display) => {
  total++;
  try {
    katex.renderToString(tex, { macros: { ...MACROS }, throwOnError: true, displayMode: display, strict: "ignore" });
  } catch (e) {
    const key = String(e.message).split("\n")[0];
    if (!seen.has(key)) seen.set(key, []);
    seen.get(key).push(`${where}: ${tex.slice(0, 70).replace(/\s+/g, " ")}`);
    bad++;
  }
};
const walkText = (s, where) => {
  for (const seg of splitInline(s)) if (seg.k === "math") tryRender(seg.v, where, false);
};
// 课堂脚本里所有字符串（目标、题面、选项、解析、要点）里的行内公式都要能渲染
const walkEx = (node, where) => {
  if (typeof node === "string") return walkText(node, where);
  if (Array.isArray(node)) return node.forEach((n) => walkEx(n, where));
  if (node && typeof node === "object") for (const v of Object.values(node)) walkEx(v, where);
};
for (const f of readdirSync(dir).filter((x) => x.endsWith(".json"))) {
  walkEx(JSON.parse(readFileSync(join(dir, f), "utf8")), f.replace(".json", ""));
}
for (const [k, v] of seen) console.error(`✗ ${k}  ×${v.length}\n    例：${v.slice(0, 2).join("\n        ")}`);
if (bad) {
  console.error(`公式：${bad} / ${total} 条不能渲染`);
  process.exit(1);
}
console.log(`公式：${total} 条全部可渲染`);
