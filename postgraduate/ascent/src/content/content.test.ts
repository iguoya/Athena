import { describe, expect, it } from "vitest";
import { grammarChapter, grammarUnits, sentenceSets, sources } from "./index";
import { bankStages, loadWords, VOCAB_BANKS } from "./vocab";
import { validateSet } from "./validate";

describe("content packs", () => {
  it("has at least one set", () => {
    expect(sentenceSets.length).toBeGreaterThan(0);
  });

  it.each(sentenceSets.map((s) => [s.id, s] as const))("%s passes the content check", (_id, set) => {
    expect(validateSet(set, sources)).toEqual([]);
  });

  it("rejects a sentence without a registered source", () => {
    const bad = structuredClone(sentenceSets[0]);
    bad.sentences[0].source = "nowhere";
    expect(validateSet(bad, sources)).toHaveLength(1);
  });

  it("chapter-1 grammar map has the ten high-school units", () => {
    expect(grammarChapter.chapter).toBe(1);
    expect(grammarUnits.map((u) => u.id)).toEqual([
      "tense",
      "passive",
      "nonfinite",
      "relative",
      "noun-clause",
      "adverbial",
      "modal",
      "subjunctive",
      "inversion",
      "emphasis",
    ]);
    for (const u of grammarUnits) {
      expect(u.patterns.length).toBeGreaterThan(0);
      expect(new Set(u.patterns.map((p) => p.id)).size).toBe(u.patterns.length);
    }
  });

  it("registers the jobs speech source for attribution", () => {
    expect(sources["jobs-stanford-2005"]?.title).toContain("Jobs");
  });
});

describe("vocab stages (ADR 0022)", () => {
  it.each(VOCAB_BANKS.map((b) => [b.id] as const))("%s stages cover the bank without overlaps", async (exam) => {
    const file = bankStages(exam);
    expect(file).toBeDefined();
    expect(file!.stages.length).toBeGreaterThan(0);

    const bank = await loadWords(exam);
    const seen = new Set<string>();
    for (const stage of file!.stages) {
      expect(stage.words.length).toBeGreaterThan(0);
      for (const w of stage.words) {
        expect(bank[w]).toBeDefined();
        expect(seen.has(w)).toBe(false);
        seen.add(w);
      }
    }
  });

  it("orders the high-school ladder from most common words to rarest", () => {
    const stages = bankStages("hs")!.stages;
    // the/be 是语料里最高频的词，必须出现在第一阶的开头。
    expect(stages[0].words.slice(0, 2)).toEqual(["the", "be"]);
    // 冷门词不该跑到第一阶。
    expect(stages[0].words).not.toContain("brochure");
  });

  it("keeps each stage close to one month of new words (15/day)", () => {
    for (const bank of VOCAB_BANKS) {
      for (const stage of bankStages(bank.id)!.stages) {
        expect(stage.words.length).toBeLessThanOrEqual(500);
      }
    }
  });
});
