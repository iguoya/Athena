// 答案解析的用例（核对点）。解析器是纯函数，改一处容易把另一处改坏，所以拿测试钉住。
// 跑法：node scripts/test-answer.mjs（已挂进 pnpm run build）
import * as esbuild from "esbuild";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(mkdtempSync(join(tmpdir(), "ans-")), "answer.mjs");
await esbuild.build({ absWorkingDir: root, entryPoints: ["src/answer.ts"], bundle: true, format: "esm", outfile: out, logLevel: "error" });
const { answerMatches, evalExpr } = await import(pathToFileURL(out).href);

const YES = [
  ["3", [3]], ["-2.5", [-2.5]], ["1/2", [0.5]], ["−3/4", [-0.75]], ["0.5", [0.5]],
  ["1, 2, 3", [1, 2, 3]], ["(1, -2, 3)", [1, -2, 3]], ["1 2 3", [1, 2, 3]], ["1 -2 3", [1, -2, 3]],
  ["1，2，3", [1, 2, 3]], ["[1, 2; 3, 4]", [1, 2, 3, 4]], ["(1,2),(3,4)", [1, 2, 3, 4]],
  ["sqrt(2)", [Math.SQRT2]], ["√2", [Math.SQRT2]], ["2√3", [2 * Math.sqrt(3)]], ["1/sqrt(2)", [Math.SQRT1_2]],
  ["pi/2", [Math.PI / 2]], ["π", [Math.PI]], ["2^3", [8]], ["(1+2)*3", [9]], ["(1+2)", [3]], ["1/2, 1/3", [0.5, 1 / 3]],
  ["1 / 2   3 / 4", [0.5, 0.75]], ["x"] && ["0", [0]],
];
const NO = [["", [1]], ["abc", [1]], ["1/0", [1]], ["1,2", [1, 2, 3]], ["2", [3]], ["1/3", [0.33]], ["(1,2", [1, 2]], ["sqrt2", [Math.SQRT2]]];
let bad = 0;
for (const [s, w] of YES) if (!answerMatches(s, w)) { console.error(`✗ 应当通过：${JSON.stringify(s)} → ${JSON.stringify(w)}`); bad++; }
for (const [s, w] of NO) if (answerMatches(s, w)) { console.error(`✗ 应当拒绝：${JSON.stringify(s)} vs ${JSON.stringify(w)}`); bad++; }
if (evalExpr("2+") !== null || evalExpr("sqrt") !== null) { console.error("✗ 残缺表达式应返回 null"); bad++; }
if (bad) process.exit(1);
console.log(`答案解析：${YES.length + NO.length + 1} 条用例通过`);
