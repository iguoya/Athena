// 核对网页小模型（src/cube.ts）和黄金向量（scripts/cube_golden.json）。
// 黄金向量由 C++ 模型生成，并逐字写进 exercise/02-turns/cube_test.cc 里断言；
// 这里让 TypeScript 这一份也得出同样的结果。Node 22.6+ 直接跑 .ts，不需要构建。
import { readFileSync } from "node:fs";
import { parse, run, solved } from "../src/cube.ts";

const here = new URL("./cube_golden.json", import.meta.url);
const golden: { alg: string; state: string }[] = JSON.parse(readFileSync(here, "utf-8"));

let failed = 0;
for (const { alg, state } of golden) {
  const got = run(solved(), parse(alg)).join("");
  if (got !== state) {
    console.error(`不一致：${alg}\n  期望 ${state}\n  实际 ${got}`);
    failed += 1;
  }
}
if (failed > 0) process.exit(1);
console.log(`网页小模型与 ${golden.length} 条黄金向量一致`);
