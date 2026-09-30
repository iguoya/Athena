// Real CET-4 exam sentences for LOCAL use only (ADR 0019): exam papers are copyrighted, so the sentences go to
// the git-ignored content/private/exam/ and never into the public repo or the installer.
//
//   pnpm content:cet4
//
// Source: https://github.com/123xzw999/cet4-exam-quiz, 46 CET-4 papers (2020-2026) with reading passages and
// the listening lines each answer is located in. The script clones it into .cache/content/ and writes:
//   content/private/exam/cet4.json          reading and listening sentences, each with paper and part
//   content/vocab/hs/exam-frequency.json    how often each high-school word appears in those papers
// The frequency file holds counts only, no exam text, so it is committed: chapter 1 uses it to put the words
// CET-4 actually tests first. Writing and translation "model" answers in the source are not exam text and are skipped.

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import vm from "node:vm";
import { CACHE, CONTENT, readJson, today, writeJsonLines } from "./lib.mjs";
import { tokenize } from "./tokenize.mjs";

const REPO = "https://github.com/123xzw999/cet4-exam-quiz.git";
const dir = join(CACHE, "cet4-exam-quiz");
if (existsSync(dir)) execFileSync("git", ["-C", dir, "pull", "--ff-only", "-q"], { stdio: "inherit" });
else execFileSync("git", ["clone", "-q", "--depth", "1", REPO, dir], { stdio: "inherit" });

const sandbox = { window: {} };
vm.createContext(sandbox);
const paperDir = join(dir, "data/papers");
for (const f of readdirSync(paperDir).filter((f) => f.endsWith(".js"))) {
  vm.runInContext(readFileSync(join(paperDir, f), "utf8"), sandbox);
}
const papers = Object.values(sandbox.window.__CET4_PAPERS ?? {});
if (!papers.length) throw new Error(`在 ${paperDir} 没读到试卷，源仓库的格式可能变了。`);

const PART_NAMES = { cloze: "选词填空", matching: "长篇阅读", reading: "仔细阅读", listening: "听力" };
const ABBREVIATIONS = /\b(Mr|Mrs|Ms|Dr|Prof|St|U\.S|U\.K|e\.g|i\.e|etc|vs)\.$/;

/** Split a passage into sentences, keeping abbreviations like "Dr." inside their sentence. */
function sentencesOf(text) {
  const out = [];
  let current = "";
  for (const piece of text.split(/(?<=[.!?]["”’)]?)\s+(?=["“(]?[A-Z])/)) {
    current = current ? `${current} ${piece}` : piece;
    if (!ABBREVIATIONS.test(current)) {
      out.push(current.trim());
      current = "";
    }
  }
  if (current) out.push(current.trim());
  return out;
}

function cleanPassage(passage, answers) {
  return (
    passage
      // Put the right word back into each cloze blank: "(26)______" -> "detailed".
      .replace(/,?\s*\((\d+)\)_+/g, (_, no) => ` ${answers.get(Number(no)) ?? "______"}`)
      // Paragraph labels: "P1 " in careful reading, "A) " in long reading.
      .replace(/(^|\n)\s*(P\d+|[A-P]\))\s+/g, "$1")
      .replace(/\s+/g, " ")
  );
}

const sentences = [];
const seen = new Set();
function add(paper, part, en, cn) {
  const words = en.split(" ").length;
  if (words < 4 || words > 45 || en.includes("___") || seen.has(en)) return;
  seen.add(en);
  const n = sentences.filter((s) => s.paperId === paper.id).length + 1;
  sentences.push({
    id: `cet4-${paper.id}-${n}`,
    en,
    ...(cn ? { cn } : {}),
    exam: "cet4",
    paperId: paper.id,
    paper: `${paper.label} ${paper.set}`,
    part: PART_NAMES[part] ?? part,
    grammar: [],
  });
}

for (const paper of papers.sort((a, b) => a.id.localeCompare(b.id))) {
  const answers = new Map(paper.questions.filter((q) => q.answerText).map((q) => [q.no, q.answerText]));
  const passages = new Map();
  for (const q of paper.questions) if (q.passage && !passages.has(q.passage)) passages.set(q.passage, q.part);
  for (const [passage, part] of passages) {
    for (const s of sentencesOf(cleanPassage(passage, answers))) add(paper, part, s);
  }
  // Listening has no full transcript, but each answer's "定位" quotes the recording, then a Chinese translation.
  for (const q of paper.questions.filter((q) => q.part === "listening")) {
    const locate = q.explain?.["定位"] ?? "";
    const cjk = locate.search(/[一-鿿]/);
    if (cjk <= 0) continue;
    const en = locate.slice(0, cjk).trim();
    if (!/[.!?]["”’]?$/.test(en)) continue;
    add(paper, "listening", en, locate.slice(cjk).trim());
  }
}

writeJsonLines(
  join(CONTENT, "private/exam/cet4.json"),
  {
    about: "四级真题句子，只在本机用，不进仓库（ADR 0019）。由 scripts/content/import-cet4-local.mjs 生成。",
    source: "exam",
    upstream: "https://github.com/123xzw999/cet4-exam-quiz",
    generated: today(),
  },
  "sentences",
  sentences,
);

// Count how often each high-school headword (any form) appears across the papers.
const words = readJson(join(CONTENT, "vocab/hs/words.json")).words;
const formToWord = new Map();
for (const w of words) for (const f of [w.word, ...w.forms]) formToWord.set(f.toLowerCase(), w.word);
const hits = new Map();
const inSentences = new Map();
for (const s of sentences) {
  const heads = new Set();
  for (const t of tokenize(s.en)) {
    const head = formToWord.get(t);
    if (!head) continue;
    hits.set(head, (hits.get(head) ?? 0) + 1);
    heads.add(head);
  }
  for (const h of heads) inSentences.set(h, (inSentences.get(h) ?? 0) + 1);
}
writeJsonLines(
  join(CONTENT, "vocab/hs/exam-frequency.json"),
  {
    about:
      "高中词在 2020-2026 年 46 套四级真题（阅读和听力）里出现的次数，只有统计数字，不含真题原文。" +
      "hits 是出现总次数，sentences 是出现在多少个句子里。第一章按它把四级真正考的词排在前面。",
    exam: "cet4",
    papers: papers.length,
    sentences: sentences.length,
    generated: today(),
  },
  "words",
  words
    .map((w) => ({ word: w.word, hits: hits.get(w.word) ?? 0, sentences: inSentences.get(w.word) ?? 0 }))
    .sort((a, b) => b.hits - a.hits || a.word.localeCompare(b.word)),
);
