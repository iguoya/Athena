// Word splitting shared by the sentence importers.

const CONTRACTIONS = { "won't": ["will", "not"], "can't": ["can", "not"], "shan't": ["shall", "not"] };
const SUFFIXES = { "n't": "not", "'re": "are", "'ll": "will", "'ve": "have", "'d": "would", "'m": "am", "'s": null };
export const ALWAYS_KNOWN = new Set(["mr", "mrs", "ms", "ok", "okay"]);

/** Lower-case words, with contractions split ("don't" -> do, not; "Tom's" -> tom). */
export function tokenize(en) {
  const out = [];
  for (const raw of en
    .toLowerCase()
    .replace(/’/g, "'")
    .match(/[a-z]+(?:'[a-z]+)?/g) ?? []) {
    if (CONTRACTIONS[raw]) {
      out.push(...CONTRACTIONS[raw]);
      continue;
    }
    const suffix = Object.keys(SUFFIXES).find((s) => raw.endsWith(s) && raw.length > s.length);
    if (!suffix) out.push(raw);
    else out.push(raw.slice(0, -suffix.length), ...(SUFFIXES[suffix] ? [SUFFIXES[suffix]] : []));
  }
  return out;
}
