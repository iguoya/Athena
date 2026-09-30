import type { GrammarChapter, SentenceSet, Source } from "./types";

// Content is plain JSON in the repo and bundled at build time (ADR 0010).
const setModules = import.meta.glob<SentenceSet>("../../content/sets/*.json", { eager: true, import: "default" });
const sourceModule = import.meta.glob<{
  sources?: Array<{
    id: string;
    name: string;
    url: string;
    license: string;
    use?: string;
    notes?: string;
  }>;
}>("../../content/sources.json", { eager: true, import: "default" });
const grammarModule = import.meta.glob<GrammarChapter>("../../content/grammar.json", {
  eager: true,
  import: "default",
});

function yearFromText(text: string | undefined): number {
  const m = text?.match(/\b(19|20)\d{2}\b/);
  return m ? Number(m[0]) : 0;
}

/** Registry keyed by source id, shaped for sentence attribution in the UI. */
export const sources: Record<string, Source> = (() => {
  const raw = Object.values(sourceModule)[0];
  const list = raw?.sources ?? [];
  const out: Record<string, Source> = {};
  for (const s of list) {
    out[s.id] = {
      title: s.name,
      year: yearFromText(s.name) || yearFromText(s.notes),
      url: s.url,
      kind: s.use ?? "quote",
      license: s.license,
    };
  }
  return out;
})();

export const sentenceSets: SentenceSet[] = Object.values(setModules);

export const grammarChapter: GrammarChapter = Object.values(grammarModule)[0] ?? {
  chapter: 1,
  title: "夯实高中",
  subtitle: "高中英语知识地图",
  blurb: "",
  units: [],
};

export const grammarUnits = [...grammarChapter.units].sort((a, b) => a.order - b.order);

export function grammarUnit(id: string) {
  return grammarUnits.find((u) => u.id === id);
}

/** Sentences whose grammar tags belong to this unit (by pattern id prefix or set.unit). */
export function sentencesForUnit(unitId: string) {
  const unit = grammarUnit(unitId);
  if (!unit) return [];
  const patternIds = new Set(unit.patterns.map((p) => p.id));
  const primary: SentenceSet["sentences"] = [];
  const fallback: SentenceSet["sentences"] = [];
  for (const set of sentenceSets) {
    for (const s of set.sentences) {
      const tagged = s.grammar.some((g) => patternIds.has(g) || g.startsWith(`${unitId}-`));
      if (tagged) primary.push(s);
      else if (set.unit === unitId) fallback.push(s);
    }
  }
  const seen = new Set<string>();
  return [...primary, ...fallback].filter((s) => (seen.has(s.id) ? false : (seen.add(s.id), true)));
}

// Until scheduling by mastery exists, today's set is the first one.
export function todaySet(): SentenceSet {
  return sentenceSets[0];
}
