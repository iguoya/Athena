import type { SentenceSet, Source } from "./types";

// Rejects content that breaks the ADR 0005 / 0007 / 0010 rules; run by the tests and usable from a build script.
export function validateSet(set: SentenceSet, sources: Record<string, Source>): string[] {
  const errors: string[] = [];
  const seen = new Set<string>();
  for (const s of set.sentences) {
    const at = `${set.id}/${s.id}`;
    if (seen.has(s.id)) errors.push(`${at}: 句子编号重复`);
    seen.add(s.id);
    if (!s.source || !sources[s.source]) errors.push(`${at}: 没有登记的出处（${s.source || "空"}）`);
    if (!s.cn.trim()) errors.push(`${at}: 缺少译文`);
    if (s.segments.map((g) => g.text).join("") !== s.en) errors.push(`${at}: 结构标注拼起来和原句不一致`);
    const words = new Set(s.en.toLowerCase().match(/[a-z]+(?:['’][a-z]+)*/g) ?? []);
    for (const g of s.glosses) {
      if (!g.simpleEn.trim() || !g.cn.trim()) errors.push(`${at}: 词 ${g.lemma} 缺少释义`);
      if (g.words.some((w) => !words.has(w))) errors.push(`${at}: 词 ${g.lemma} 不在句子里`);
    }
  }
  return errors;
}
