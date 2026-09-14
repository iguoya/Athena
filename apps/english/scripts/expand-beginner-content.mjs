import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// 作者工具：从仓库内已经保存的词表、双语例句和 VOA 原文生成初级扩容批次。
// 输出仍是 content/ 下可审阅、可版本化的普通 JSON；应用运行时不执行本脚本。

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const contentRoot = path.join(appRoot, "content");

function readJson(relative) {
  return JSON.parse(fs.readFileSync(path.join(contentRoot, relative), "utf8"));
}

function writeJson(relative, value) {
  const target = path.join(contentRoot, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`);
}

function slug(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

function normalizeText(text) {
  return String(text).replace(/\s+([,.;:!?])/g, "$1").replace(/\s+/g, " ").trim();
}

function wordPattern(word) {
  return new RegExp(`\\b${word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}[a-z’']*\\b`, "i");
}

function glossParts(text) {
  return String(text)
    .replace(/\[[^\]]+\]/g, "")
    .split(/[；;，,]/)
    .map((part) => part
      .replace(/^\([^)]*\)\s*/, "")
      .replace(/^(aux|prep|pron|conj|art|num|int)\.?\s*/i, "")
      .replace(/[：:]$/, "")
      .trim())
    .filter((part) => part.length > 0 && part.length <= 8);
}

function cleanGloss(text) {
  return glossParts(text)[0] ?? "";
}

function uniqueBy(items, keyOf) {
  const seen = new Set();
  return items.filter((item) => {
    const key = keyOf(item);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function itemRefs(entry, sentenceIndexes) {
  const sourceIds = new Set(sentenceIndexes.map((index) => entry.sentences[index]?.source_id).filter(Boolean));
  return [...sourceIds].map((sourceId) => ({
    source_id: sourceId,
    relation: "quoted",
    locator: `word “${entry.word}” · examples ${sentenceIndexes.map((index) => index + 1).join(" / ")}`,
    note: "英文例句和对应中文释义取自仓库内双语句库；题干、干扰项和反馈由本项目转换。",
  }));
}

function loadSentenceSource(sourceId, relative, merged) {
  const lines = fs.readFileSync(path.join(contentRoot, relative), "utf8").trim().split(/\r?\n/);
  for (const line of lines) {
    const raw = JSON.parse(line);
    const word = String(raw.word ?? "").toLowerCase();
    if (!word) continue;
    const entry = merged.get(word) ?? { word, translations: [], sentences: [] };
    entry.translations.push(...(raw.translations ?? []));
    entry.sentences.push(...(raw.sentences ?? []).map((sentence) => ({
      ...sentence,
      sentence: normalizeText(sentence.sentence),
      translation: normalizeText(sentence.translation),
      source_id: sourceId,
    })));
    merged.set(word, entry);
  }
}

const merged = new Map();
loadSentenceSource("kylebing-kaoyan", "sources/reference/github/kylebing/kaoyan-sentences.jsonl", merged);
loadSentenceSource("kylebing-cet4", "sources/reference/github/kylebing/cet4-sentences.jsonl", merged);
loadSentenceSource("kylebing-cet6", "sources/reference/github/kylebing/cet6-sentences.jsonl", merged);

const ngslRaw = readJson("sources/reference/raw/NGSL.json");
const ngslOrder = Object.keys(ngslRaw["1000"]);
const ngslRank = new Map(ngslOrder.map((word, index) => [word, index + 1]));
const entries = [];
for (const word of ngslOrder) {
  if (!/^[a-z]+$/.test(word)) continue;
  const raw = merged.get(word);
  if (!raw) continue;
  const pattern = wordPattern(word);
  const allSentencesForWord = uniqueBy(
    raw.sentences.filter((entry) =>
      entry.sentence &&
      entry.translation &&
      pattern.test(entry.sentence) &&
      entry.sentence.trim().split(/\s+/).length >= 5 &&
      !entry.sentence.includes("(="),
    ),
    (entry) => entry.sentence.toLowerCase(),
  );
  let selected;
  for (const sense of raw.translations.filter((entry) => ["v", "n", "adj", "adv"].includes(entry.type))) {
    // 助动词用法属于句法轨，不把“已经”等完成体标记冒充词汇核心义。
    if (/^\s*(?:\([^)]*\)\s*)?aux/i.test(sense.translation)) continue;
    const alternatives = uniqueBy(glossParts(sense.translation), (part) => part);
    for (const gloss of alternatives) {
      const matching = allSentencesForWord.filter((entry) => entry.translation.includes(gloss));
      if (matching.length >= 1 && allSentencesForWord.length >= 2) {
        const sentences = [matching[0], ...allSentencesForWord.filter((entry) => entry !== matching[0])];
        selected = { word, pos: sense.type, gloss, alternatives: alternatives.filter((part) => part !== gloss), sentences };
        break;
      }
    }
    if (selected) break;
  }
  if (selected) entries.push(selected);
}

const originalVocab = readJson("vocab/beginner/core.json");
const originalWords = new Set(originalVocab.items.map((item) => item.word));
const generatedWords = entries.filter((entry) => !originalWords.has(entry.word)).slice(0, 300 - originalWords.size);
if (generatedWords.length !== 300 - originalWords.size) {
  throw new Error(`初级词汇候选不足：需要 ${300 - originalWords.size}，实际 ${generatedWords.length}`);
}
const allWordEntries = [
  ...originalVocab.items.map((item) => ({
    word: item.word,
    pos: item.senses[0].pos,
    gloss: cleanGloss(item.senses[0].gloss),
  })),
  ...generatedWords,
];

function distractorsFor(entry, index, pool = allWordEntries) {
  const ownAlternatives = (entry.alternatives ?? []).filter((gloss) => gloss !== entry.gloss).slice(0, 2)
    .map((gloss) => ({ word: entry.word, pos: entry.pos, gloss }));
  const samePos = pool.filter((other) => other.word !== entry.word && other.pos === entry.pos && other.gloss !== entry.gloss);
  const source = samePos.length >= 2 ? samePos : pool.filter((other) => other.word !== entry.word && other.gloss !== entry.gloss);
  const fallback = [source[(index * 7 + 11) % source.length], source[(index * 13 + 29) % source.length]];
  return uniqueBy([...ownAlternatives, ...fallback], (item) => item.gloss).slice(0, 2);
}

const generatedVocabItems = generatedWords.map((entry, index) => {
  const distractors = distractorsFor(entry, index);
  const choice = (candidate, sentence, correct) => ({
    label: candidate.gloss,
    ok: correct,
    why: correct
      ? `${entry.word} 在本句中取“${entry.gloss}”这个核心义。整句可理解为：${sentence.translation}`
      : `${candidate.word} 常表示“${candidate.gloss}”；放回本句不符合语境。`,
  });
  return {
    id: `en.beginner.vocab.${slug(entry.word)}`,
    word: entry.word,
    senses: [{ pos: entry.pos, gloss: entry.gloss }],
    sentence: entry.sentences[0].sentence,
    prompt: "先看语境：标记词在本句中最接近哪个核心义？",
    error_tag: "高频词义",
    choices: [choice(entry, entry.sentences[0], true), ...distractors.map((item) => choice(item, entry.sentences[0], false))],
    variants: [{
      sentence: entry.sentences[1].sentence,
      prompt: "换一个语境，这个词仍最接近哪个核心义？",
      choices: [choice(entry, entry.sentences[1], true), ...distractors.map((item) => choice(item, entry.sentences[1], false))],
    }],
    source_refs: itemRefs(entry, [0, 1]),
  };
});

const vocabChunkSize = 48;
const generatedVocabPaths = [];
for (let offset = 0; offset < generatedVocabItems.length; offset += vocabChunkSize) {
  const part = Math.floor(offset / vocabChunkSize) + 1;
  const relative = `vocab/beginner/generated-${String(part).padStart(2, "0")}.json`;
  generatedVocabPaths.push(relative);
  writeJson(relative, {
    topic_id: "en.beginner.vocab.core",
    kind: "vocab",
    source_refs: [
      { source_id: "ngsl-1.2", relation: "selection_basis", note: "按 NGSL 前 1000 词的频率顺序补足初级核心词。" },
      { source_id: "kylebing-kaoyan", relation: "quoted", note: "双语例句用于建立词在语境中的核心义。" },
    ],
    items: generatedVocabItems.slice(offset, offset + vocabChunkSize),
  });
}
const legacyVocabPath = path.join(contentRoot, "vocab/beginner/generated-core.json");
if (fs.existsSync(legacyVocabPath)) fs.rmSync(legacyVocabPath);

const selectedWords = new Set([...originalWords, ...generatedWords.map((entry) => entry.word)]);
const translationEntries = entries.filter((entry) => !selectedWords.has(entry.word)).slice(0, 58);
if (translationEntries.length !== 58) throw new Error("初级英译汉候选不足 58 组");

function translationChoices(entry, sentence, index, pool) {
  const sameWordOther = entry.sentences.find((candidate) => candidate.sentence !== sentence.sentence);
  const other = pool[(index + 17) % pool.length];
  return [
    { label: sentence.translation, ok: true, why: `时间、对象、动作和语气均与原句对应；${entry.word} 在这里是“${entry.gloss}”。` },
    { label: sameWordOther.translation, ok: false, why: `这项也包含 ${entry.word} 的意思，但人物、动作或限定信息来自另一句。` },
    { label: other.sentences[0].translation, ok: false, why: "这项来自另一条真实句子，主语、动作或条件与题面不对应。" },
  ];
}

const translationItems = translationEntries.map((entry, index) => ({
  id: `en.beginner.sentence.translation_${slug(entry.word)}`,
  kind: "translation",
  text: entry.sentences[0].sentence,
  prompt: "哪项翻译准确、完整地保留了原句信息？",
  error_tag: "英译汉信息完整",
  choices: translationChoices(entry, entry.sentences[0], index, translationEntries),
  variants: [{
    text: entry.sentences[1].sentence,
    prompt: "换一句再译：哪项表达准确、完整、自然？",
    choices: translationChoices(entry, entry.sentences[1], index + 3, translationEntries),
  }],
  source_refs: itemRefs(entry, [0, 1]),
}));

writeJson("sentences/beginner/translation.json", {
  topic_id: "en.beginner.sentence.basic_logic",
  kind: "sentence",
  source_refs: [
    { source_id: "kylebing-kaoyan", relation: "quoted", note: "双语例句提供可核对的英译汉原句和参考译文。" },
    { source_id: "yz-english-2-outline", relation: "exam_alignment", note: "从短句信息完整性逐步衔接英语二英译汉。" },
  ],
  items: translationItems,
});

const logicKinds = [
  { key: "because", limit: 4, pattern: /\bbecause\s+(?:i|you|he|she|we|they|it|the|a|an|there)\b/i, reject: /\bnot\s+because\b/i, kind: "cause", prompt: "because 后面的信息在句中承担什么作用？", answer: "说明前面情况的原因", wrong: ["说明前面情况的结果", "引出与前文无关的话题"] },
  { key: "but", limit: 4, pattern: /\bbut\s+(?:i|you|he|she|we|they|it|the|a|an)\b/i, reject: /^(?:[“\"']\s*)?(?:but\b|(?:no|yes),\s*but\b)|\bnot only\b.*\bbut\b|\b(?:nothing|anything)\b.*\bbut\b/i, kind: "contrast", prompt: "but 前后两部分是什么关系？", answer: "后半句转折或修正前半句", wrong: ["后半句只重复前半句", "两部分构成时间先后"] },
  { key: "if", limit: 4, pattern: /^(?:[“\"']\s*)?if\s+(?:i|you|he|she|we|they|it|the|a|an)\b/i, reject: /\bas if\b|\bif not\b/i, kind: "condition", prompt: "if 从句在这里给出了什么？", answer: "行动或结果成立的条件", wrong: ["已经发生的结果", "说话人的身份"] },
  { key: "so", limit: 4, pattern: /[,;]\s+so\s+(?:i|you|he|she|we|they|it|the|a|an|don['’]t|do|can|could|would|should|had|was|were)\b/i, reject: /^(?:[“\"']\s*)?but\b/i, kind: "cause", prompt: "so 后面的信息在句中承担什么作用？", answer: "说明前面情况带来的结果", wrong: ["说明前面情况的原因", "只补充动作发生地点"] },
  { key: "although", limit: 3, pattern: /^(?:[“\"']\s*)?(?:although|even though|though)\b/i, reject: /\b(?:shorn|skeptical|qualms|sanity|admiring)\b/i, kind: "contrast", prompt: "although / though 引出的内容有什么作用？", answer: "先承认一种情况，再给出不同结论", wrong: ["列出完全相同的两件事", "只交代动作发生地点"] },
  { key: "time", limit: 3, pattern: /\b(?:before|after)\s+(?:i|you|he|she|we|they|it)\b/i, reject: /\b(?:look|looks|looked|looking)\s+after\b/i, kind: "clause_split", prompt: "before / after 在这里帮助读者判断什么？", answer: "两个动作或情况发生的先后", wrong: ["两个动作之间的因果方向", "说话人的身份"] },
  { key: "when", limit: 3, pattern: /\bwhen\s+(?:i|you|he|she|we|they|it|the)\b/i, reject: /^\.\.\./, kind: "clause_split", prompt: "when 引出的部分帮助读者判断什么？", answer: "动作或情况发生的时间背景", wrong: ["前后内容互相否定", "说话人的身份"] },
];

const allSentences = uniqueBy(
  [...merged.entries()].flatMap(([word, entry]) => entry.sentences
    .filter((sentence) => sentence.sentence && sentence.translation && sentence.sentence.trim().split(/\s+/).length >= 5 && !sentence.sentence.includes("(="))
    .map((sentence) => ({ ...sentence, word }))),
  (entry) => entry.sentence.toLowerCase(),
);
const logicItems = [];
for (const template of logicKinds) {
  const matches = allSentences
    .filter((entry) => {
      const words = entry.sentence.trim().split(/\s+/).length;
      return words >= 6 && words <= 32 && template.pattern.test(entry.sentence) && !template.reject?.test(entry.sentence);
    })
    .sort((left, right) => left.sentence.split(/\s+/).length - right.sentence.split(/\s+/).length);
  for (let pair = 0; pair < template.limit && pair * 2 + 1 < matches.length; pair += 1) {
    const base = matches[pair * 2];
    const variant = matches[pair * 2 + 1];
    logicItems.push({
      id: `en.beginner.sentence.logic_${template.key}_${pair + 1}`,
      kind: template.kind,
      text: base.sentence,
      prompt: template.prompt,
      error_tag: template.kind === "cause" ? "因果关系" : template.kind === "contrast" ? "转折关系" : template.kind === "condition" ? "条件关系" : "句子切分",
      choices: [
        { label: template.answer, ok: true, why: `连接词在这句话中确实承担这一作用。整句可理解为：${base.translation}` },
        ...template.wrong.map((label) => ({ label, ok: false, why: "这种关系与原句连接词和上下文不符。" })),
      ],
      variants: [{
        text: variant.sentence,
        prompt: template.prompt,
        choices: [
          { label: template.answer, ok: true, why: `换句后连接关系不变。整句可理解为：${variant.translation}` },
          ...template.wrong.map((label) => ({ label, ok: false, why: "这种关系与变式句不符。" })),
        ],
      }],
      source_refs: [{
        source_id: base.source_id,
        relation: "quoted",
        locator: `word “${base.word}” · connector ${template.key}`,
        note: "句子取自仓库内双语句库；题目只把真实句子转换为连接关系判断。",
      }],
    });
  }
}
logicItems.length = Math.min(logicItems.length, 23);
if (logicItems.length !== 23) throw new Error(`初级连接关系候选不足 23 组：${logicItems.length}`);

writeJson("sentences/beginner/logic.json", {
  topic_id: "en.beginner.sentence.basic_logic",
  kind: "sentence",
  source_refs: [{ source_id: "kylebing-kaoyan", relation: "quoted", note: "真实双语例句用于因果、转折、条件和切分练习。" }],
  items: logicItems,
});

function sourceParagraphs(relative, sourceId) {
  const raw = fs.readFileSync(path.join(contentRoot, relative), "utf8")
    .replace(/^#.*$/gm, "")
    .replace(/^来源：.*$/gm, "")
    .replace(/^授权：.*$/gm, "")
    .replace(/^音频：.*$/gm, "")
    .replace(/<https?:[^>]+>/g, "")
    .replace(/^[-*] /gm, "");
  return raw.split(/\n\s*\n/)
    .map((text) => text.replace(/\n+/g, " ").trim())
    .filter((text) => {
      const words = text.split(/\s+/).length;
      return words >= 3 && words <= 90 &&
        !/[:：]\s*$/.test(text) &&
        !text.startsWith("From VOA") &&
        !/^(?:Today we answer|She writes:?|Dear\b|Thank you for asking|I hope this helps|I['’]m\b|And that)/i.test(text) &&
        !/ wrote this| was the editor|Ask a Teacher/.test(text);
    })
    .map((text) => ({ text, sourceId }));
}

const articleParagraphs = [
  ...sourceParagraphs("sources/reference/voa/walking-wonder-drug.md", "voa-walking-wonder-drug"),
  ...sourceParagraphs("sources/reference/voa/job-and-career.md", "voa-job-and-career"),
];
const passageChunks = articleParagraphs.map((paragraph, index) => {
  const parts = [paragraph.text];
  let nextIndex = index + 1;
  const sentenceCount = () => (parts.join(" ").match(/[.!?](?:["”'])?(?=\s|$)/g) ?? []).length;
  while (sentenceCount() < 2 && articleParagraphs[nextIndex]?.sourceId === paragraph.sourceId) {
    parts.push(articleParagraphs[nextIndex].text);
    nextIndex += 1;
  }
  if (sentenceCount() < 2 && articleParagraphs[index - 1]?.sourceId === paragraph.sourceId) {
    parts.unshift(articleParagraphs[index - 1].text);
  }
  return { text: parts.join(" "), sourceId: paragraph.sourceId };
}).filter((chunk) => {
  const words = chunk.text.split(/\s+/).length;
  const sentences = (chunk.text.match(/[.!?](?:["”'])?(?=\s|$)/g) ?? []).length;
  return words >= 18 && words <= 120 && sentences >= 2;
});
if (passageChunks.length < 30) throw new Error(`短文候选不足 30 段：${passageChunks.length}`);
function firstStatement(text) {
  return text.match(/^.*?[.!?](?:["”'])?(?=\s|$)/)?.[0] ?? text;
}
for (const chunk of passageChunks) chunk.evidence = firstStatement(chunk.text);
function unrelatedEvidence(chunk, start) {
  for (let step = 0; step < passageChunks.length; step += 1) {
    const candidate = passageChunks[(start + step) % passageChunks.length].evidence;
    if (candidate !== chunk.evidence && !chunk.text.includes(candidate)) return candidate;
  }
  throw new Error("无法为初级短文找到不重叠的干扰项");
}
const passageItems = passageChunks.slice(0, 30).map((chunk, index) => {
  const wrongA = unrelatedEvidence(chunk, index + 7);
  const wrongB = unrelatedEvidence(chunk, index + 19);
  const variant = passageChunks[(index + 13) % passageChunks.length];
  return {
    id: `en.beginner.sentence.passage_${String(index + 1).padStart(2, "0")}`,
    kind: "passage_detail",
    text: chunk.text,
    prompt: "先定位证据：哪一句确实出现在这段短文中？",
    error_tag: "短文证据定位",
    choices: [
      { label: chunk.evidence, ok: true, why: "这项信息可以直接在短文中找到。" },
      { label: wrongA, ok: false, why: "这是另一段材料的信息，本段没有这样说。" },
      { label: wrongB, ok: false, why: "这项内容没有出现在当前短文中。" },
    ],
    variants: [{
      text: variant.text,
      prompt: "换一段短文，哪项信息有明确原文依据？",
      choices: [
        { label: variant.evidence, ok: true, why: "这项信息可以直接由变式短文核对。" },
        { label: wrongB, ok: false, why: "这项内容属于其他段落。" },
      ],
    }],
    source_refs: [{
      source_id: chunk.sourceId,
      relation: "quoted",
      locator: `beginner excerpt ${index + 1}`,
      note: "短文由同一篇 VOA 原文中的相邻句组成；题目训练先定位明确证据。",
    }],
  };
});

writeJson("passages/beginner/core.json", {
  topic_id: "en.beginner.sentence.basic_logic",
  kind: "sentence",
  source_refs: [
    { source_id: "voa-walking-wonder-drug", relation: "quoted", note: "选取相邻句组成初级健康主题短文。" },
    { source_id: "voa-job-and-career", relation: "quoted", note: "选取相邻句组成初级工作主题短文。" },
  ],
  items: passageItems,
});

const originalWriting = readJson("writing/beginner/core.json");
originalWriting.items = originalWriting.items.filter((item) => [
  "en.beginner.writing.reason",
  "en.beginner.writing.contrast",
  "en.beginner.writing.practical_note",
].includes(item.id));
const originalPracticalNote = originalWriting.items.find((item) => item.id === "en.beginner.writing.practical_note");
if (originalPracticalNote && !originalPracticalNote.reference.endsWith("Thank you.")) {
  originalPracticalNote.reference += " Thank you.";
}
const reasonSeeds = [
  ["提前列好第二天的计划", "I make a short plan before I go to bed.", "because it helps me start the next morning calmly"],
  ["晚饭后散步", "I take a short walk after dinner.", "because it helps me relax and sleep better"],
  ["在家做早餐", "I often make breakfast at home.", "because it saves money and lets me choose fresh food"],
  ["每天复习新词", "I review new words every day.", "because short daily practice is easier to remember"],
  ["上课时记笔记", "I take notes during class.", "because writing down key ideas helps me review them later"],
  ["把手机调成静音", "I keep my phone silent while I study.", "because messages can easily break my attention"],
  ["遇到问题及时提问", "I ask questions when I do not understand.", "because a clear answer prevents the same mistake later"],
  ["尽量按时睡觉", "I try to go to bed at the same time.", "because a regular schedule gives me more energy"],
  ["周末去图书馆", "I visit the library on weekends.", "because it gives me a quiet place and useful books"],
];
const contrastSeeds = [
  ["线上课程", "Online classes are convenient", "they require me to manage my time carefully"],
  ["乘公交上班", "The bus is sometimes crowded", "it is cheaper than driving"],
  ["独自学习", "Studying alone is quiet", "I sometimes miss the ideas other people can share"],
  ["早起锻炼", "Getting up early is difficult", "a morning walk makes me feel active"],
  ["住在市中心", "The city centre is noisy", "shops and public transport are close"],
  ["自己做饭", "Cooking takes time", "it gives me more control over what I eat"],
  ["学习新软件", "The new program looks complicated", "its basic tools are easy to learn"],
  ["参加小组活动", "Group work can be slow", "it helps us see different solutions"],
  ["阅读英文新闻", "Some news articles contain difficult words", "their main ideas are often clear from context"],
];
const noteSeeds = [
  ["同学", "说明今天会晚到，并请对方先开始讨论", "Hi Lin, I will arrive about fifteen minutes late because my bus is moving slowly. Please start the discussion without me."],
  ["老师", "说明身体不舒服，并询问今天的作业", "Hello Ms Chen, I cannot attend class today because I am not feeling well. Could you please tell me what homework I should complete?"],
  ["室友", "说明晚上有客人来，并询问是否方便", "Hi Mei, a friend will visit me this evening. Is seven o'clock convenient for you? Please let me know."],
  ["图书馆", "询问遗失的卡是否已经找到", "Hello, I lost my library card yesterday. Could you please tell me whether anyone has returned it?"],
  ["同事", "说明文件已经完成，并请对方检查", "Hi David, I have finished the report. Please check the final page and tell me if anything needs to change."],
  ["朋友", "拒绝周五邀请、说明原因并建议另一个时间", "Hi Sara, I am sorry I cannot come on Friday because I have a class. Could we meet on Saturday afternoon instead?"],
  ["课程管理员", "询问上课地点和开始时间", "Hello, I have joined the Saturday course. Could you please confirm where the class meets and what time it starts?"],
  ["邻居", "提醒包裹暂存在自己家，并说明领取时间", "Hi Alex, your package is at my apartment. You can collect it after six this evening. Please call before you come."],
  ["店家", "说明收到的商品有问题，并提出简单解决办法", "Hello, the lamp I received does not work. Could you please replace it or tell me how to return it?"],
];

const generatedWriting = [
  ...reasonSeeds.map(([topic, starter, reason], index) => ({
    id: `en.beginner.writing.reason_${index + 2}`,
    kind: "guided_writing",
    prompt: `围绕“${topic}”补写 2—3 句，至少使用 because。`,
    starter,
    min_words: 25,
    required_any: ["because"],
    reference: `${starter} I do this ${reason}. This small habit makes my day easier, and it is easy to continue.`,
    error_tag: "理由没有展开",
    checklist: ["是否写清具体做法", "because 后是否给出真正原因", "是否用一句结果收束"],
    source_refs: [{ source_id: "voa-writing-speaking-guide", relation: "adapted", locator: "Beginners: personal experience", note: "按初级个人经验活动改成短段落练习；参考写法不是唯一答案。" }],
  })),
  ...contrastSeeds.map(([topic, first, second], index) => ({
    id: `en.beginner.writing.contrast_${index + 2}`,
    kind: "guided_writing",
    prompt: `围绕“${topic}”写 3 句：先承认一个情况，再用 but 写出另一面。`,
    starter: `${first}, but`,
    min_words: 28,
    required_any: ["but"],
    reference: `${first}, but ${second}. I decide what to do by thinking about both sides. For me, the second point matters more in daily life.`,
    error_tag: "转折表达不完整",
    checklist: ["but 前后是否真的形成对照", "两个分句是否都有完整谓语", "结尾是否回到自己的判断"],
    source_refs: [{ source_id: "voa-writing-speaking-guide", relation: "adapted", locator: "Beginners: compare experiences", note: "按初级对比活动改成短段落练习；参考写法用于自查结构。" }],
  })),
  ...noteSeeds.map(([reader, task, reference], index) => ({
    id: `en.beginner.writing.note_${index + 2}`,
    kind: "guided_writing",
    prompt: `给${reader}写一条短消息：${task}。`,
    starter: "Hello,",
    min_words: 28,
    required_any: ["please", "could"],
    reference: `${reference} Thank you for your help and understanding. I look forward to your reply.`,
    error_tag: "任务回应不完整",
    checklist: ["是否回应了题目中的每项任务", "请求是否清楚且礼貌", "时间、人物和动作是否明确"],
    source_refs: [{ source_id: "voa-writing-speaking-guide", relation: "adapted", locator: "Beginners: practical messages", note: "按初级真实交流活动改成短消息任务；参考写法只示范任务回应。" }],
  })),
];
writeJson("writing/beginner/core.json", { ...originalWriting, items: [...originalWriting.items, ...generatedWriting] });

const practiceMaterialText = new Set([
  ...originalVocab.items.flatMap((item) => [item.sentence, ...(item.variants ?? []).map((variant) => variant.sentence)]),
  ...generatedVocabItems.flatMap((item) => [item.sentence, ...(item.variants ?? []).map((variant) => variant.sentence)]),
  ...readJson("sentences/beginner/core.json").items.flatMap((item) => [item.text, ...(item.variants ?? []).map((variant) => variant.text)]),
  ...translationItems.flatMap((item) => [item.text, ...(item.variants ?? []).map((variant) => variant.text)]),
  ...logicItems.flatMap((item) => [item.text, ...(item.variants ?? []).map((variant) => variant.text)]),
  ...passageItems.flatMap((item) => [item.text, ...(item.variants ?? []).map((variant) => variant.text)]),
].filter(Boolean).map((text) => text.toLowerCase()));

const originalVocabAssessment = readJson("assessments/beginner/vocab.json");
originalVocabAssessment.items = originalVocabAssessment.items.filter((item) => [
  "en.assessment.beginner.vocab.provide",
  "en.assessment.beginner.vocab.affect",
  "en.assessment.beginner.vocab.result",
  "en.assessment.beginner.vocab.opportunity",
  "en.assessment.beginner.vocab.support",
].includes(item.id));
const assessmentWordEntries = generatedWords.flatMap((entry) => {
  const sentenceIndex = entry.sentences.findIndex((sentence, index) =>
    index >= 2 && sentence.translation.includes(entry.gloss) && !practiceMaterialText.has(sentence.sentence.toLowerCase()),
  );
  return sentenceIndex >= 0 ? [{ entry, sentenceIndex }] : [];
}).slice(0, 25);
if (assessmentWordEntries.length !== 25) throw new Error(`独立词汇考核候选不足：${assessmentWordEntries.length}`);
const vocabAssessmentItems = assessmentWordEntries.map(({ entry, sentenceIndex }, index) => {
  const distractors = distractorsFor(entry, index + 71);
  const sentence = entry.sentences[sentenceIndex];
  practiceMaterialText.add(sentence.sentence.toLowerCase());
  return {
    id: `en.assessment.beginner.vocab.${slug(entry.word)}`,
    word: entry.word,
    senses: [{ pos: entry.pos, gloss: entry.gloss }],
    sentence: sentence.sentence,
    prompt: "在这个新语境中，标记词最接近哪个意思？",
    error_tag: "高频词义迁移",
    choices: [
      { label: entry.gloss, ok: true, why: `本句取“${entry.gloss}”这一核心义。整句可理解为：${sentence.translation}` },
      ...distractors.map((item) => ({ label: item.gloss, ok: false, why: `“${item.gloss}”不符合本句语境。` })),
    ],
    source_refs: itemRefs(entry, [sentenceIndex]),
  };
});
writeJson("assessments/beginner/vocab.json", {
  ...originalVocabAssessment,
  assessment_id: "en.assessment.beginner.vocab.v2",
  items: [...originalVocabAssessment.items, ...vocabAssessmentItems],
});

const originalSentenceAssessment = readJson("assessments/beginner/sentence.json");
originalSentenceAssessment.items = originalSentenceAssessment.items.filter((item) => [
  "en.assessment.beginner.sentence.cause",
  "en.assessment.beginner.sentence.contrast",
  "en.assessment.beginner.sentence.reference",
  "en.assessment.beginner.sentence.translation",
  "en.assessment.beginner.sentence.short_text",
].includes(item.id));
const assessmentTranslations = translationEntries.filter((entry) => entry.sentences.length >= 3).slice(0, 10).map((entry, index) => {
  const sentence = entry.sentences[2];
  return {
    id: `en.assessment.beginner.sentence.translation_${slug(entry.word)}`,
    kind: "translation",
    text: sentence.sentence,
    prompt: "哪项翻译准确、完整、自然？",
    error_tag: "英译汉信息完整",
    choices: translationChoices(entry, sentence, index + 80, translationEntries),
    source_refs: itemRefs(entry, [2]),
  };
});
const assessmentLogic = [];
for (const template of logicKinds) {
  for (const source of allSentences.filter((entry) => template.pattern.test(entry.sentence))) {
    if (practiceMaterialText.has(source.sentence.toLowerCase())) continue;
    practiceMaterialText.add(source.sentence.toLowerCase());
    assessmentLogic.push({
      id: `en.assessment.beginner.sentence.logic_${assessmentLogic.length + 1}`,
      kind: template.kind,
      text: source.sentence,
      prompt: template.prompt,
      error_tag: "句间逻辑",
      choices: [
        { label: template.answer, ok: true, why: `连接词与上下文支持这一判断。整句可理解为：${source.translation}` },
        ...template.wrong.map((label) => ({ label, ok: false, why: "这种关系不符合题面。" })),
      ],
      source_refs: [{ source_id: source.source_id, relation: "quoted", locator: `word “${source.word}”`, note: "使用未出现在练习题面的双语例句做独立关系判断。" }],
    });
    if (assessmentLogic.length === 10) break;
  }
  if (assessmentLogic.length === 10) break;
}
if (assessmentLogic.length !== 10) throw new Error(`独立句子逻辑考核候选不足：${assessmentLogic.length}`);
const assessmentReading = allSentences.filter((entry) => !practiceMaterialText.has(entry.sentence.toLowerCase())).slice(0, 5).map((entry, index, pool) => ({
  id: `en.assessment.beginner.sentence.reading_${index + 1}`,
  kind: "detail",
  text: entry.sentence,
  prompt: "哪项中文信息与原句一致？",
  error_tag: "细节定位",
  choices: [
    { label: entry.translation, ok: true, why: "人物、动作和限定信息均与原句对应。" },
    { label: pool[(index + 2) % pool.length].translation, ok: false, why: "这项来自另一句，信息与题面不符。" },
  ],
  source_refs: [{ source_id: entry.source_id, relation: "quoted", locator: `word “${entry.word}”`, note: "使用未在练习中出现的真实双语例句检查细节理解。" }],
}));
writeJson("assessments/beginner/sentence.json", {
  ...originalSentenceAssessment,
  assessment_id: "en.assessment.beginner.sentence.v2",
  items: [...originalSentenceAssessment.items, ...assessmentTranslations, ...assessmentLogic, ...assessmentReading],
});

const originalWritingAssessment = readJson("assessments/beginner/writing.json");
originalWritingAssessment.items = originalWritingAssessment.items.filter((item) => [
  "en.assessment.beginner.writing.complete_sentence",
  "en.assessment.beginner.writing.reason",
  "en.assessment.beginner.writing.contrast",
  "en.assessment.beginner.writing.order",
  "en.assessment.beginner.writing.task",
].includes(item.id));
const writingAssessmentSeeds = [
  ["说明不能参加活动、给出原因并道歉", "I am sorry that I cannot join the activity because I have to work.", "I like many different activities."],
  ["询问课程地点和开始时间", "Could you please tell me where the class meets and when it starts?", "The class is very interesting."],
  ["说明会迟到并请对方先开始", "I will be late because my train has stopped. Please start without me.", "Trains are a useful form of transport."],
  ["感谢帮助并说明帮助带来的结果", "Thank you for helping me. Your advice made the task much easier.", "The task was on the table."],
  ["报告物品损坏并提出解决请求", "The lamp I received is broken. Could you please replace it?", "The lamp is blue and the shop is large."],
  ["邀请朋友并交代时间地点", "Would you like to meet at the library at three on Saturday?", "Libraries have many books."],
  ["拒绝邀请并建议另一个时间", "I cannot come on Friday, but I am free on Saturday afternoon.", "Friday comes before Saturday."],
  ["请假并询问需要补做什么", "I cannot attend class today. Could you tell me what work I should complete?", "Today is a busy day."],
  ["提醒对方带证件并说明原因", "Please bring your card because you need it to enter the building.", "The building has several windows."],
  ["说明计划发生变化并给出新安排", "Our meeting has moved to Tuesday. Please come to Room 4 at ten.", "Tuesday is one day of the week."],
  ["介绍一个习惯及其好处", "I prepare my bag at night because this saves time in the morning.", "My bag is black and quite new."],
  ["先承认困难再说明好处", "The course is demanding, but it gives me useful practice.", "The course is demanding because practice is useless."],
  ["提出礼貌请求并说明截止时间", "Could you please send the file before five this afternoon?", "The file was created on a computer."],
  ["说明遗失物品并询问是否找到", "I lost my card yesterday. Has anyone found it?", "I bought a new card yesterday."],
  ["向邻居说明包裹存放地点和领取办法", "Your package is at my apartment. Please call me before you collect it.", "Packages can come in different sizes."],
];
const extraWritingAssessment = writingAssessmentSeeds.map(([task, correct, wrong], index) => ({
  id: `en.assessment.beginner.writing.task_${index + 2}`,
  kind: "writing_choice",
  prompt: `任务要求“${task}”。哪项回应完整？`,
  error_tag: "任务回应",
  choices: [
    { label: correct, ok: true, why: "题目要求的关键信息均已明确回应。" },
    { label: wrong, ok: false, why: "句子虽然相关，但遗漏了任务要求的关键动作。" },
    { label: "Thank you. Everything is fine.", ok: false, why: "这句没有回应当前任务。" },
  ],
  source_refs: [{ source_id: "voa-writing-speaking-guide", relation: "adapted", locator: "Beginners: practical writing", note: "按初级真实交流活动改成独立任务回应判断，不复用练习题干。" }],
}));
writeJson("assessments/beginner/writing.json", {
  ...originalWritingAssessment,
  assessment_id: "en.assessment.beginner.writing.v2",
  items: [...originalWritingAssessment.items, ...extraWritingAssessment],
});

const oldAudit = readJson("sources/ngsl-1.2-used-words.json");
const oldAuditByWord = new Map(oldAudit.words.map((entry) => [entry.lemma, entry]));
const auditWords = [...selectedWords].map((lemma) => ({
  lemma,
  rank: ngslRank.get(lemma) ?? oldAuditByWord.get(lemma)?.rank ?? 9999,
  ...(oldAuditByWord.get(lemma)?.frequency_per_million
    ? { frequency_per_million: oldAuditByWord.get(lemma).frequency_per_million }
    : {}),
})).sort((a, b) => a.rank - b.rank || a.lemma.localeCompare(b.lemma));
writeJson("sources/ngsl-1.2-used-words.json", {
  ...oldAudit,
  fields: "NGSL 1.2 frequency order; frequency_per_million is preserved where separately audited",
  words: auditWords,
});

console.log(`初级内容已生成：词汇 ${originalVocab.items.length + generatedVocabItems.length}，句子 ${10 + translationItems.length + logicItems.length + passageItems.length}，写作 ${originalWriting.items.length + generatedWriting.length}。`);
