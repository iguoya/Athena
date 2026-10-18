// 核对讲解内容里的每一张魔方回放图：记号写得对不对、走完是不是真的到了声明的状态。
// 图里写 "expect": "solved" 就是在向读者保证「这串转法走完魔方复原」，这里替它兜底。
import { readdirSync, readFileSync } from "node:fs";
import { isSolved, layerDone, parse, run, solved, topOriented } from "../src/cube.ts";

const dir = new URL("../content/chapters/", import.meta.url);
let figures = 0;
let failed = 0;

for (const name of readdirSync(dir).filter((f) => f.endsWith(".json")).sort()) {
  const lesson = JSON.parse(readFileSync(new URL(name, dir), "utf-8"));
  for (const section of lesson.sections ?? []) {
    const fig = section.figure;
    if (!fig || fig.kind !== "cube") continue;
    figures += 1;
    const where = `${name} · ${section.heading}`;
    try {
      const start: number[] = fig.state
        ? fig.state.split("").map(Number)
        : fig.setup
          ? run(solved(), parse(fig.setup))
          : solved();
      if (start.length !== 24 || start.some((v) => !(v >= 0 && v <= 5))) throw new Error("state 必须是 24 位 0..5 的数字");
      const end = fig.moves ? run(start, parse(fig.moves)) : start;
      const ok = {
        solved: isSolved,
        layer: layerDone,
        oriented: (s: number[]) => layerDone(s) && topOriented(s),
      };
      if (fig.expect && !ok[fig.expect as keyof typeof ok](end)) {
        console.error(`${where}：走完没有到达 ${fig.expect}`);
        failed += 1;
      }
      for (const slot of fig.marks ?? []) {
        if (!Number.isInteger(slot) || slot < 0 || slot > 23) {
          console.error(`${where}：圈出的贴纸编号 ${slot} 不在 0..23`);
          failed += 1;
        }
      }
    } catch (error) {
      console.error(`${where}：${(error as Error).message}`);
      failed += 1;
    }
  }
}
if (failed > 0) process.exit(1);
console.log(`讲解里的 ${figures} 张魔方回放图都核对过`);
