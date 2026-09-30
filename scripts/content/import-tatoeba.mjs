// Pick real example sentences with Chinese translations from Tatoeba (CC BY 2.0 FR, ADR 0019)
// for every word in content/vocab/hs/words.json (run import-ecdict.mjs first).
//
//   pnpm content:tatoeba                 download the Tatoeba exports (about 60 MB) and write the files below
//   pnpm content:tatoeba --dir <folder>  use exports you downloaded yourself (same file names)
//
// Writes:
//   content/sentences/tatoeba.json      the chosen sentences, each with author, licence and link
//   content/vocab/hs/sentence-index.json  word -> sentence ids, before any sense is assigned
//   content/vocab/hs/todo.json          words with fewer than 3 sentences (ADR 0005: they wait for more sources)
//
// Choosing favours comprehensible sentences (i+1, ADR 0014): 4 to 20 words, most other words already in the
// high-school list, and a simplified-Chinese translation. Sense assignment, grammar tags and structure
// annotation come later and are reviewed by tiger.

import { existsSync } from "node:fs";
import { join } from "node:path";
import { CACHE, CONTENT, download, readJson, readText, today, tsvRows, writeJsonLines } from "./lib.mjs";

const BASE = "https://downloads.tatoeba.org/exports/per_language";
const FILES = {
  eng: `${BASE}/eng/eng_sentences_detailed.tsv.bz2`,
  cmn: `${BASE}/cmn/cmn_sentences_detailed.tsv.bz2`,
  links: `${BASE}/eng/eng-cmn_links.tsv.bz2`,
};
const PER_WORD = 8;
const MIN_REAL = 3;

// Characters that only appear in traditional Chinese; a translation containing them is skipped.
const TRADITIONAL =
  /[們這個說會來時為國學過對還裡麼讓樣點電話買賣開關長門問間聽見車東書愛飯誰認識語請謝歡氣發現後從動經應該覺幫幾兒嗎錢頭媽歲場]/;

const dirArg = process.argv.indexOf("--dir");
const localDir = dirArg > 0 ? process.argv[dirArg + 1] : null;

async function load(name) {
  const url = FILES[name];
  const file = url.split("/").pop();
  const local = localDir ? join(localDir, file) : join(CACHE, file);
  return tsvRows(readText(existsSync(local) ? local : await download(url)));
}

const wordsFile = join(CONTENT, "vocab/hs/words.json");
if (!existsSync(wordsFile)) throw new Error("先运行 pnpm content:ecdict 生成 content/vocab/hs/words.json");
const words = readJson(wordsFile).words;

// Every surface form maps to the headwords it can belong to ("left" -> leave, left).
const formToWords = new Map();
for (const w of words) {
  for (const f of [w.word, ...w.forms]) {
    const key = f.toLowerCase();
    if (!formToWords.has(key)) formToWords.set(key, new Set());
    formToWords.get(key).add(w.word);
  }
}

const CONTRACTIONS = { "won't": ["will", "not"], "can't": ["can", "not"], "shan't": ["shall", "not"] };
const SUFFIXES = { "n't": "not", "'re": "are", "'ll": "will", "'ve": "have", "'d": "would", "'m": "am", "'s": null };
const ALWAYS_KNOWN = new Set(["mr", "mrs", "ms", "ok", "okay"]);

/** Lower-case words, with contractions split ("don't" -> do, not; "Tom's" -> tom). */
function tokenize(en) {
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

console.log("读取 Tatoeba 导出文件……");
const [engRows, cmnRows, linkRows] = [await load("eng"), await load("cmn"), await load("links")];

// Detailed export columns: id, lang, text, username, date added, date modified.
const cmn = new Map();
for (const [id, , text, user] of cmnRows) if (!TRADITIONAL.test(text)) cmn.set(id, { text, user });
const translation = new Map();
for (const [engId, cmnId] of linkRows) if (cmn.has(cmnId) && !translation.has(engId)) translation.set(engId, cmnId);

const candidates = new Map(); // headword -> [{ id, score }]
const sentences = new Map();
for (const [id, , en, user] of engRows) {
  const cmnId = translation.get(id);
  if (!cmnId || !user || user === "\\N") continue;
  const tokens = tokenize(en);
  if (tokens.length < 4 || tokens.length > 20) continue;
  // Capitalised words are mostly names ("Tom", "Paris") and do not count as unknown.
  const names = new Set((en.match(/\b[A-Z][a-z]+/g) ?? []).map((n) => n.toLowerCase()));
  const known = tokens.filter((t) => formToWords.has(t) || names.has(t) || ALWAYS_KNOWN.has(t)).length / tokens.length;
  if (known < 0.8) continue;
  // Shorter, fully comprehensible sentences first; long ones still qualify.
  const score = known * 10 - Math.abs(tokens.length - 9) * 0.2;
  const heads = new Set(tokens.flatMap((t) => [...(formToWords.get(t) ?? [])]));
  sentences.set(id, { en, user, cmnId, heads });
  for (const h of heads) {
    if (!candidates.has(h)) candidates.set(h, []);
    candidates.get(h).push({ id, score });
  }
}

const chosen = new Set();
const index = {};
const todo = [];
for (const w of words) {
  const picks = (candidates.get(w.word) ?? []).sort((a, b) => b.score - a.score).slice(0, PER_WORD);
  index[w.word] = picks.map((p) => `tatoeba-${p.id}`);
  picks.forEach((p) => chosen.add(p.id));
  if (picks.length < MIN_REAL) todo.push({ word: w.word, found: picks.length });
}

const out = [...chosen]
  .sort((a, b) => Number(a) - Number(b))
  .map((id) => {
    const s = sentences.get(id);
    const c = cmn.get(s.cmnId);
    return {
      id: `tatoeba-${id}`,
      en: s.en,
      cn: c.text,
      source: "tatoeba",
      url: `https://tatoeba.org/sentences/show/${id}`,
      author: s.user,
      cnUrl: `https://tatoeba.org/sentences/show/${s.cmnId}`,
      cnAuthor: c.user,
      grammar: [],
    };
  });

const generated = today();
writeJsonLines(
  join(CONTENT, "sentences/tatoeba.json"),
  {
    about:
      "来自 Tatoeba 的真实句子和中文译文，CC BY 2.0 FR，署名见每条的 author。由 scripts/content/import-tatoeba.mjs 生成。",
    source: "tatoeba",
    license: "CC BY 2.0 FR",
    generated,
  },
  "sentences",
  out,
);
writeJsonLines(
  join(CONTENT, "vocab/hs/sentence-index.json"),
  { about: "单词关每个词的候选真实例句（还没分义项）。", generated },
  "index",
  Object.entries(index).map(([word, ids]) => ({ word, ids })),
);
writeJsonLines(
  join(CONTENT, "vocab/hs/todo.json"),
  { about: "真实例句不足 3 条的词，先不入库，等其他来源补齐（ADR 0005）。", generated },
  "words",
  todo,
);
