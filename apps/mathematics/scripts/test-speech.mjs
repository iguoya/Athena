// 朗读文本转换的用例（ADR 0018）。speakable 是纯函数，最容易在改别的规则时
// 被顺手改坏，而坏了只有戴着耳机听才发现——所以拿测试钉住。
// 跑法：node scripts/test-speech.mjs（已挂进 npm run build）
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dir = mkdtempSync(join(tmpdir(), "speech-"));
const out = join(dir, "speak.mjs");
execFileSync("npx", ["esbuild", "src/speak.ts", "--bundle", "--format=esm", `--outfile=${out}`,
  "--log-level=error"], { cwd: root, stdio: "inherit" });
const { speakable } = await import(out);

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
