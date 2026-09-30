import { describe, expect, it } from "vitest";
import { sentenceSets, sources } from "./index";
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
});
