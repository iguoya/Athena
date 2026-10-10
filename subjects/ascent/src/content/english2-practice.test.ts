import { describe, expect, it } from "vitest";
import type { DeckItem } from "./english2";
import { curriculum, english2From, trackItems } from "./english2";
import {
  addDays,
  buildRound,
  checkWriting,
  clozeFor,
  INTERVALS,
  PASS_RATE,
  ROUND_SIZE,
  schedule,
  scoreAssessment,
  updateMistake,
  type ItemRecord,
} from "./english2-practice";

const item = (id: string, extra: Partial<DeckItem> = {}): DeckItem => ({ id, prompt: id, ...extra });
const choice = (ok: boolean) => ({ label: ok ? "对" : "错", ok });

describe("英语二练习规则", () => {
  it("连对按阶梯拉长间隔，答错归零、明天再来", () => {
    let rec: ItemRecord | undefined;
    const days: number[] = [];
    for (let i = 0; i < INTERVALS.length + 1; i++) {
      rec = schedule(rec, true, "2026-10-10");
      days.push((new Date(rec.due).getTime() - new Date("2026-10-10").getTime()) / 86_400_000);
    }
    expect(days).toEqual([...INTERVALS, INTERVALS.at(-1)]);
    rec = schedule(rec, false, "2026-10-10");
    expect(rec.streak).toBe(0);
    expect(rec.due).toBe("2026-10-11");
    expect(rec.wrong).toBe(1);
  });

  it("一轮先到期的复习、再补新题，且不超过上限", () => {
    const items = Array.from({ length: 30 }, (_, i) => item(`i${i}`));
    const records: Record<string, ItemRecord> = {
      i5: { streak: 1, due: "2026-10-09", seen: 1, wrong: 0, last: "2026-10-08" },
      i3: { streak: 1, due: "2026-10-08", seen: 1, wrong: 0, last: "2026-10-07" },
      i7: { streak: 2, due: "2026-10-20", seen: 2, wrong: 0, last: "2026-10-10" }, // 未到期
    };
    const round = buildRound(items, records, "2026-10-10");
    expect(round).toHaveLength(ROUND_SIZE);
    expect(round.slice(0, 2).map((i) => i.id)).toEqual(["i3", "i5"]);
    expect(round.some((i) => i.id === "i7")).toBe(false);
  });

  it("真实课表里任何一条轨的一轮都不超过上限", () => {
    const content = english2From({ decks: {}, passages: {} });
    for (const stage of curriculum.stages)
      for (const track of stage.tracks)
        expect(buildRound(trackItems(content, track), {}, "2026-10-10").length).toBeLessThanOrEqual(ROUND_SIZE);
  });

  it("错题出库要隔天答对且做对变式，缺一不出", () => {
    const target = { item: item("m", { variants: [{ prompt: "v", choices: [] }] }), trackId: "t" };
    let m = updateMistake(undefined, target, "item", false, "2026-10-10");
    expect(m).toMatchObject({ laterDayOk: false, variantOk: false });
    m = updateMistake(m, target, "item", true, "2026-10-10"); // 同一天答对不算
    expect(m?.laterDayOk).toBe(false);
    m = updateMistake(m, target, "variant", true, "2026-10-10");
    expect(m).toMatchObject({ laterDayOk: false, variantOk: true });
    expect(updateMistake(m, target, "item", true, "2026-10-11")).toBeUndefined();
  });

  it("错题再错就两个条件清零；没有变式的题只看隔天答对", () => {
    const withVariant = { item: item("m", { variants: [{ prompt: "v", choices: [] }] }), trackId: "t" };
    const half = { itemId: "m", trackId: "t", opened: "2026-10-01", laterDayOk: true, variantOk: false };
    expect(updateMistake(half, withVariant, "variant", false, "2026-10-10")).toMatchObject({
      laterDayOk: false,
      variantOk: false,
      opened: "2026-10-10",
    });
    const plain = { item: item("p"), trackId: "t" };
    const m = updateMistake(undefined, plain, "item", false, "2026-10-10");
    expect(m?.variantOk).toBe(true);
    expect(updateMistake(m, plain, "item", true, addDays("2026-10-10", 1))).toBeUndefined();
  });

  it("考核按正确率计分，没答的算错，达到 80% 通过", () => {
    const items = Array.from({ length: 10 }, (_, i) => item(`a${i}`, { choices: [choice(false), choice(true)] }));
    const answers = Object.fromEntries(items.slice(0, 8).map((i) => [i.id, 1]));
    expect(scoreAssessment(items, answers)).toEqual({ correct: 8, total: 10, rate: 0.8, passed: true });
    expect(PASS_RATE).toBe(0.8);
    expect(scoreAssessment(items, { a0: 1 }).passed).toBe(false);
  });

  it("作文只机检字数与衔接词", () => {
    const task = item("w", { min_words: 8, required_any: ["because", "so that"] });
    expect(checkWriting("I study here because it is quiet and calm.", task)).toMatchObject({
      words: 9,
      enoughWords: true,
      connector: "because",
      connectorOk: true,
    });
    const miss = checkWriting("I study here. It is quiet.", task);
    expect(miss.enoughWords).toBe(false);
    expect(miss.connectorOk).toBe(false);
    expect(checkWriting("Becauseless words", task).connectorOk).toBe(false); // 不认半个词
  });

  it("单词题答对后从变式句挖出词形，含屈折形式", () => {
    const vocab = item("v", {
      word: "provide",
      variants: [{ sentence: "The course provides beginners with examples.", prompt: "p", choices: [] }],
    });
    expect(clozeFor(vocab)).toEqual({ before: "The course ", after: " beginners with examples.", answer: "provides" });
    expect(clozeFor(item("x", { word: "provide" }))).toBeNull();
  });
});
