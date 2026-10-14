// 函数库的数值自检（ADR 0028）：白名单里每个函数的解析导数、原函数必须和数值
// 结果对得上——画面上的割线斜率、黎曼和读数都靠它们，错一个就会教错。
// 跑法：node scripts/test-calculus.mjs（已挂进 pnpm run build）
import * as esbuild from "esbuild";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(mkdtempSync(join(tmpdir(), "calc-")), "calculus.mjs");
await esbuild.build({
  absWorkingDir: root,
  entryPoints: ["src/calculus.ts"],
  bundle: true,
  format: "esm",
  outfile: out,
  logLevel: "error",
});
const { FUNCTIONS, fnById, secantSlope, riemannSum, exactIntegral } = await import(pathToFileURL(out).href);

let bad = 0;
const fail = (m) => {
  console.error("✗ " + m);
  bad++;
};
const near = (a, b, tol) => Math.abs(a - b) <= tol;

// 每个函数在若干采样点上：解析 df 与中心差分一致；有 F 的话 F' 与 f 一致。
const SAMPLES = [-2.3, -0.7, 0.4, 1.6, 2.9];
for (const fn of FUNCTIONS) {
  for (const x of SAMPLES) {
    const y = fn.f(x);
    if (!Number.isFinite(y)) continue;
    const e = 1e-5;
    const num = (fn.f(x + e) - fn.f(x - e)) / (2 * e);
    const d = fn.df(x);
    if (Number.isFinite(num) && Number.isFinite(d) && !near(num, d, 1e-3 * Math.max(1, Math.abs(d)))) {
      fail(`${fn.id}: x=${x} 处 df=${d} 与数值导数 ${num} 不一致`);
    }
    if (fn.F) {
      const fnum = (fn.F(x + e) - fn.F(x - e)) / (2 * e);
      if (Number.isFinite(fnum) && !near(fnum, y, 1e-3 * Math.max(1, Math.abs(y)))) {
        fail(`${fn.id}: x=${x} 处 F'=${fnum} 与 f=${y} 不一致`);
      }
    }
  }
}

// 割线斜率随 h→0 逼近导数
const sq = fnById("x2");
if (!near(secantSlope(sq, 1, 1), 3, 1e-9)) fail("x² 在 1 处 h=1 的割线斜率应为 3");
if (!near(secantSlope(sq, 1, 0.001), 2.001, 1e-6)) fail("x² 在 1 处 h=0.001 的割线斜率应为 2.001");
if (!Number.isNaN(secantSlope(fnById("inv"), 0, 0.5))) fail("1/x 在 0 处没有定义，割线斜率应为 NaN");

// 黎曼和：x² 在 [0,1] 上，左和 < 精确值 1/3 < 右和，n 增大两者夹拢
const l4 = riemannSum(sq, 0, 1, 4, "left");
const r4 = riemannSum(sq, 0, 1, 4, "right");
if (!near(l4, 0.21875, 1e-12) || !near(r4, 0.46875, 1e-12)) fail(`x² 4 等份左右和应为 0.21875 / 0.46875，得 ${l4} / ${r4}`);
const l400 = riemannSum(sq, 0, 1, 400, "left");
if (!(l4 < l400 && l400 < 1 / 3)) fail("左和应随 n 增大单调逼近 1/3");
if (!near(exactIntegral(sq, 0, 1), 1 / 3, 1e-12)) fail("x² 在 [0,1] 的精确积分应为 1/3");
if (!near(riemannSum(sq, 0, 1, 4, "mid"), 0.328125, 1e-12)) fail("x² 4 等份中点和应为 0.328125");

// 不可导点必须报 NaN，而不是静默给一个数
if (!Number.isNaN(fnById("abs").df(0))) fail("|x| 在 0 处不可导，df 应为 NaN");

if (bad) {
  console.error(`calculus：${bad} 项不通过`);
  process.exit(1);
}
console.log(`calculus：${FUNCTIONS.length} 个函数的导数/原函数/黎曼和自检通过`);
