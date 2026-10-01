import { describe, expect, it } from "vitest";
import { grammarChapter, grammarUnits, sentenceSets, sources } from "./index";
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
