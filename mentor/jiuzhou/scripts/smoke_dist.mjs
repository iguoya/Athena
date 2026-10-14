#!/usr/bin/env node
/**
 * 构建产物冒烟（T-018）：不启浏览器。
 * - dist/ 存在且含主 chunk / 晕渲 webp
 * - PAPER_STYLE 源码无外网 URL
 * - 打包后的 JS 不含 demotiles / naciscdn 等运行时外网字形/底图地址
 */
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DIST = join(ROOT, "dist");
const PAPER = join(ROOT, "../../packages/maps/src/paper-style.ts");
const problems = [];

function fail(msg) {
  problems.push(msg);
}

if (!existsSync(DIST)) fail("dist/ 不存在，请先 pnpm run build");

const indexHtml = join(DIST, "index.html");
if (!existsSync(indexHtml)) fail("dist/index.html 缺失");
else {
  const html = readFileSync(indexHtml, "utf8");
  if (!html.includes("assets/")) fail("index.html 未引用 assets/");
}

const assetsDir = join(DIST, "assets");
if (!existsSync(assetsDir)) fail("dist/assets/ 缺失");
else {
  const files = readdirSync(assetsDir);
  if (!files.some((f) => f.endsWith(".js"))) fail("dist/assets 无 js");
  if (!files.some((f) => f.includes("relief") && f.endsWith(".webp"))) {
    fail("dist/assets 无 relief-*.webp（晕渲未打进包）");
  }
  // 关键 content JSON 由打包进 JS，不要求独立文件；检查体积合理
  const total = files.reduce((n, f) => n + statSync(join(assetsDir, f)).size, 0);
  if (total < 100_000) fail(`dist/assets 总大小异常偏小：${total}`);
}

const paperSrc = readFileSync(PAPER, "utf8");
const paperUrls = paperSrc.match(/https?:\/\/[^\s"'`]+/g) ?? [];
if (paperUrls.length) {
  fail(`PAPER_STYLE 含外网 URL：${paperUrls.join(", ")}`);
}
if (/glyphs\s*:/.test(paperSrc)) {
  fail("PAPER_STYLE 仍声明 glyphs（应离线、地名走 DOM）");
}

const banned = [
  "demotiles.maplibre.org",
  "api.maptiler.com",
  "tile.openstreetmap.org",
  "naciscdn.org/naturalearth",
];
if (existsSync(assetsDir)) {
  for (const f of readdirSync(assetsDir)) {
    if (!f.endsWith(".js")) continue;
    const body = readFileSync(join(assetsDir, f), "utf8");
    for (const b of banned) {
      if (body.includes(b)) fail(`${f} 含运行时外网串：${b}`);
    }
  }
}

if (problems.length) {
  console.error("smoke_dist FAILED:");
  for (const p of problems) console.error(" -", p);
  process.exit(1);
}
console.log("smoke_dist OK");
