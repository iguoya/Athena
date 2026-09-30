import type { SentenceSet, Source } from "./types";

// Content is plain JSON in the repo and bundled at build time (ADR 0010).
const setModules = import.meta.glob<SentenceSet>("../../content/sets/*.json", { eager: true, import: "default" });
const sourceModule = import.meta.glob<Record<string, Source>>("../../content/sources.json", {
  eager: true,
  import: "default",
});

export const sources: Record<string, Source> = Object.values(sourceModule)[0] ?? {};
export const sentenceSets: SentenceSet[] = Object.values(setModules);

// Until scheduling by mastery exists, today's set is the first one.
export function todaySet(): SentenceSet {
  return sentenceSets[0];
}
