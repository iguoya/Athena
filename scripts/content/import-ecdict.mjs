// Build the word banks from ECDICT (MIT, ADR 0019): the high-school vocabulary gate (ADR 0012), then the words
// CET-4 and CET-6 add on top of it.
//
//   pnpm content:ecdict            download ecdict.csv (about 65 MB) and write content/vocab/{hs,cet4,cet6}/words.json
//   pnpm content:ecdict <file>     use a local copy of ecdict.csv
//
// ECDICT tags words by exam: zk 中考, gk 高考, cet4, cet6, ky 考研, toefl, ielts, gre.
// The gate takes every word tagged gk. Each entry is a draft, not a finished word card:
// - cnDraft is ECDICT's Chinese gloss with web-sourced lines removed; tiger trims it to one or two senses.
// - enRef holds WordNet definitions, only as reference for drafting the simple English definition.
// - forms (from ECDICT's exchange field) lets the sentence importers find inflected forms.
// Example sentences never come from here: they come from the sentence library (content/sentences/).

import { join } from "node:path";
import { CONTENT, download, readText, today, writeJsonLines } from "./lib.mjs";

const URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv";
const EXAM_TAGS = { zk: "zk", gk: "hs", cet4: "cet4", cet6: "cet6", ky: "ky" };
// Gaps in ECDICT's gk tag and exchange field, found by checking the commonest function words.
const EXTRA_WORDS = new Set(["must"]);
const EXTRA_FORMS = { be: ["am", "are", "were"], a: ["an"], we: ["us"] };

/** Minimal RFC 4180 CSV parser (ECDICT quotes fields that contain commas or newlines). */
function* parseCsv(text) {
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else quoted = false;
      } else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") {
      row.push(field);
      field = "";
    } else if (c === "\n") {
      row.push(field.replace(/\r$/, ""));
      yield row;
      row = [];
      field = "";
    } else field += c;
  }
  if (field || row.length) yield [...row, field];
}

function cleanChinese(translation) {
  return (
    translation
      .split("\\n")
      .map((line) => line.trim())
      // Drop web-sourced lines ([网络]) and domain jargon ([计] computing, [医] medicine, ...).
      .filter((line) => line && !line.startsWith("["))
      .join("\n")
  );
}

function forms(exchange, word) {
  const out = new Set();
  for (const part of exchange.split("/")) {
    const [kind, value] = part.split(":");
    // p past, d past participle, i -ing, 3 third person, r comparative, t superlative, s plural.
    if ("pdi3rts".includes(kind) && value && value !== word) out.add(value);
  }
  return [...out];
}

const file = process.argv[2] ?? (await download(URL));
const rows = parseCsv(readText(file));
const header = rows.next().value;
const col = Object.fromEntries(header.map((name, i) => [name, i]));

// Each word goes to the lowest level it belongs to: high school, then CET-4, then CET-6.
const LEVELS = [
  {
    dir: "hs",
    about:
      "单词关词表草稿（ADR 0012、0019），高考词。由 scripts/content/import-ecdict.mjs 生成，按常用程度排序。" +
      "cnDraft 待 tiger 精简，simpleEn 待 AI 起草、tiger 审核，enRef 只作起草参考。例句见 content/sentences/。",
    has: (tags, word) => tags.includes("gk") || EXTRA_WORDS.has(word),
  },
  {
    dir: "cet4",
    about:
      "四级比高中多出来的词（ECDICT cet4 标签，去掉高中词），第二章用。按 ADR 0012 不单独背，在真题句子和听力里遇到时学。" +
      "字段含义同 vocab/hs/words.json。",
    has: (tags) => tags.includes("cet4"),
  },
  {
    dir: "cet6",
    about:
      "六级比高中和四级多出来的词（ECDICT cet6 标签，去掉高中和四级词），第三章用。按 ADR 0012 不单独背，在句子和听力里学。" +
      "字段含义同 vocab/hs/words.json。",
    has: (tags) => tags.includes("cet6"),
  },
];
const byLevel = Object.fromEntries(LEVELS.map((l) => [l.dir, []]));

for (const r of rows) {
  const tags = (r[col.tag] ?? "").split(" ");
  const word = r[col.word];
  const level = LEVELS.find((l) => l.has(tags, word));
  if (!level) continue;
  if (level.dir === "hs" && !tags.includes("gk")) tags.push("gk");
  byLevel[level.dir].push({
    word,
    phonetic: r[col.phonetic] || undefined,
    forms: [...forms(r[col.exchange] ?? "", word), ...(EXTRA_FORMS[word] ?? [])],
    exams: tags.filter((t) => t in EXAM_TAGS).map((t) => EXAM_TAGS[t]),
    oxford3000: r[col.oxford] === "1" || undefined,
    collins: Number(r[col.collins]) || undefined,
    frq: Number(r[col.frq]) || undefined,
    cnDraft: cleanChinese(r[col.translation] ?? ""),
    // WordNet glosses look like "n. where you live"; ECDICT mixes in wrapped Webster 1913 text, which is skipped.
    enRef: (r[col.definition] ?? "").split("\\n").filter((d) => /^[nvasr]\. \S/.test(d) && !/^v\. [it]\. /.test(d)),
    simpleEn: null,
    status: "draft",
  });
}

for (const level of LEVELS) {
  const words = byLevel[level.dir];
  words.sort((a, b) => (a.frq || 1e9) - (b.frq || 1e9) || a.word.localeCompare(b.word));
  writeJsonLines(
    join(CONTENT, `vocab/${level.dir}/words.json`),
    { about: level.about, source: "ecdict", generated: today() },
    "words",
    words,
  );
}
