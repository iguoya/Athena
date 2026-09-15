// 朗读文本转换的用例（ADR 0018）。speakable 是纯函数，最容易在改别的规则时
// 被顺手改坏，而坏了只有戴着耳机听才发现——所以拿测试钉住。
// 跑法：node scripts/test-speech.mjs（已挂进 npm run build）
//
// 用 esbuild 的 JS API 而不是 spawn `npx esbuild`：Windows 上 npx 实际是
// npx.cmd，execFileSync 不经 shell，CreateProcess 只替没有扩展名的程序补 .exe，
// 于是这里在 Windows 上必然 ENOENT（主仓库 ADR 0047）。不起子进程就没有这个
// 问题，顺带还省掉一次进程启动。
import * as esbuild from "esbuild";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { pathToFileURL } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dir = mkdtempSync(join(tmpdir(), "speech-"));
const out = join(dir, "speak.mjs");
await esbuild.build({
  absWorkingDir: root,
  entryPoints: ["src/speak.ts"],
  bundle: true,
  format: "esm",
  outfile: out,
  logLevel: "error",
});
// Windows 上 import() 不接受 C:\ 开头的裸路径，要转成 file:// URL 才认。
const { speakable } = await import(pathToFileURL(out).href);

const CASES = [
  // 下标上标要摊平，否则 TTS 直接跳过，念出来缺主语
  ["`a₁₁a₂₂ − a₁₂a₂₁`", "a 1 1 a 2 2 减 a 1 2 a 2 1"],
  ["`T: Rⁿ → Rᵐ`", "T: R n 变成 R m"],
  ["`T(eᵢ)`", "T(e i )"],
  // 减号两种读法
  ["`det A = −10`", "det A 等于 负 10"],
  ["`1×1 − k×0 = 1`", "1 乘 1 减 k 乘 0 等于 1"],
  // 矩阵：逗号后有空格也要认出来
  ["`[[1, k], [0, 1]]`", "矩阵 1 k 0 1"],
  // 反引号必须清干净，一个都不许漏
  ["为 `A` 的**行列式**", "为 A 的行列式"],
  // 绝对值竖线
  ["`|det A|` 等于面积", "det A 的绝对值 等于面积"],
  ["`x²` 与 `x³`", "x 平方 与 x 立方"],
];

let bad = 0;
for (const [src, want] of CASES) {
  const got = speakable(src);
  if (got !== want) {
    console.error(`朗读转换不对：\n  原文 ${src}\n  期望 ${want}\n  实得 ${got}`);
    bad++;
  }
}
// 转换后不该再有这些：念出来全是噪音
for (const [src] of CASES) {
  const got = speakable(src);
  for (const ch of ["`", "**", "==", "₁", "ⁿ", "−"]) {
    if (got.includes(ch)) {
      console.error(`朗读转换残留「${ch}」：${src} → ${got}`);
      bad++;
    }
  }
}
rmSync(dir, { recursive: true, force: true });
if (bad) {
  console.error(`\n共 ${bad} 处。见 ADR 0018 与 src/speak.ts。`);
  process.exit(1);
}
console.log(`朗读转换检查通过：${CASES.length} 条用例。`);
