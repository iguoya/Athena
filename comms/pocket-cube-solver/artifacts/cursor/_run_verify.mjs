// 实算全部预测题，核对草稿里的 answer
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  isSolved,
  layerDone,
  parse,
  run,
  solved,
  topOriented,
} from "../../../../programming/pocket-cube-solver/src/cube.ts";

const COLOR = ["黄色", "橙色", "绿色", "白色", "红色", "蓝色"];
const COLOR1 = ["黄", "橙", "绿", "白", "红", "蓝"]; // 拼序列用
const here = dirname(fileURLToPath(import.meta.url));
const qdir = join(here, "questions");

const checks = [
  {
    id: "cube.net.predict-ruprime",
    file: "01-net.json",
    run: () => {
      const end = run(solved(), parse("R U' R'"));
      return { got: COLOR[end[0]], expectChoice: "绿色", detail: `U[0]=${COLOR[end[0]]}` };
    },
  },
  {
    id: "cube.turns.predict-ru",
    file: "02-turns.json",
    run: () => {
      const end = run(solved(), parse("R U"));
      return { got: COLOR[end[9]], expectChoice: "橙色", detail: `F右上 slot9=${COLOR[end[9]]}` };
    },
  },
  {
    id: "cube.layer.predict-rprime",
    file: "03-layer.json",
    run: () => {
      const end = run(solved(), parse("R'"));
      const bothFalse = !layerDone(end) && !isSolved(end);
      return {
        got: bothFalse ? "layer_done 为假，is_solved 也为假" : "其他",
        expectChoice: "layer_done 为假，is_solved 也为假",
        detail: `layerDone=${layerDone(end)} isSolved=${isSolved(end)}`,
      };
    },
  },
  {
    id: "cube.orient.predict-sune",
    file: "04-orient.json",
    run: () => {
      const end = run(solved(), parse("R U R' U R U2 R'"));
      const y = end.slice(0, 4).filter((c) => c === 0).length;
      const ok = y === 1 && layerDone(end);
      return {
        got: ok ? "1 格黄，且 layer_done 为真" : `黄=${y} layer=${layerDone(end)}`,
        expectChoice: "1 格黄，且 layer_done 为真",
        detail: `U黄格=${y} layerDone=${layerDone(end)} topOriented=${topOriented(end)}`,
      };
    },
  },
  {
    id: "cube.permute.predict-r2",
    file: "05-permute.json",
    run: () => {
      const end = run(solved(), parse("R2"));
      const bothFalse = !topOriented(end) && !layerDone(end);
      return {
        got: bothFalse ? "top_oriented 为假，layer_done 也为假" : "其他",
        expectChoice: "top_oriented 为假，layer_done 也为假",
        detail: `topOriented=${topOriented(end)} layerDone=${layerDone(end)}`,
      };
    },
  },
  {
    id: "cube.solver.predict-f",
    file: "06-solver.json",
    run: () => {
      const end = run(solved(), parse("F"));
      const seq = end.slice(4, 8).map((c) => COLOR1[c]).join("、");
      return { got: seq, expectChoice: "黄、橙、黄、橙", detail: `R面=${seq}` };
    },
  },
  {
    id: "cube.optimal.predict-ur",
    file: "07-optimal.json",
    run: () => {
      const end = run(solved(), parse("U R"));
      return { got: COLOR[end[8]], expectChoice: "橙色", detail: `F左上 slot8=${COLOR[end[8]]}` };
    },
  },
];

const lines = [];
lines.push("# 预测题实算记录（T-001）");
lines.push("");
lines.push("命令：`node --experimental-strip-types comms/pocket-cube-solver/artifacts/cursor/_run_verify.mjs`");
lines.push("模型：`programming/pocket-cube-solver/src/cube.ts`（`run` / `parse` / `solved` / `layerDone` / `topOriented` / `isSolved`）");
lines.push("");

let failed = 0;
for (const c of checks) {
  const qs = JSON.parse(readFileSync(join(qdir, c.file), "utf-8"));
  const question = qs.find((x) => x.id === c.id);
  if (!question) {
    lines.push(`## ${c.id}`);
    lines.push(`- FAIL：草稿里找不到该题`);
    failed += 1;
    continue;
  }
  const result = c.run();
  const choice = question.choices[question.answer];
  const matchExpect = choice === result.expectChoice || choice.startsWith(result.expectChoice);
  const matchGot = choice === result.got || choice.startsWith(result.got) || result.got === result.expectChoice;
  const ok = matchExpect && (result.got === result.expectChoice || choice.includes(result.got) || result.got.includes(result.expectChoice.split("，")[0]));
  // 更严：实算 got 必须等于 expectChoice，且草稿选中项以 expectChoice 开头（允许后面有补长）
  const strict =
    result.got === result.expectChoice &&
    (choice === result.expectChoice || choice.startsWith(result.expectChoice));
  lines.push(`## ${c.id}`);
  lines.push(`- 文件：\`questions/${c.file}\``);
  lines.push(`- 实算：${result.detail}`);
  lines.push(`- 期望正确项：${result.expectChoice}`);
  lines.push(`- 草稿 answer=${question.answer} →「${choice}」`);
  lines.push(`- 结果：${strict ? "OK" : "FAIL"}`);
  lines.push("");
  if (!strict) failed += 1;
  void matchGot;
  void ok;
}

const summary = failed === 0 ? "全部预测题实算与草稿 answer 一致。" : `失败 ${failed} 题。`;
lines.push(`## 汇总`);
lines.push(summary);

const out = join(here, "verify-questions.md");
writeFileSync(out, lines.join("\n") + "\n", "utf-8");
console.log(lines.join("\n"));
if (failed) process.exit(1);
