import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const contentRoot = path.join(appRoot, "content");
const curriculum = readJson("curriculum.json");
const catalog = readJson("sources/catalog.json");
const ngslAudit = readJson("sources/ngsl-1.2-used-words.json");
const lemmasBundle = readJson("sources/reference/lemmas.json");
const errors = [];
const ids = new Map();
const assessmentIds = new Set();
const practiceMaterial = new Set();
const assessmentMaterial = [];
const sourceIds = new Set();
const allowedLemmas = new Set();
for (const key of ["ngsl", "nawl", "awl"]) {
  const list = lemmasBundle[key]?.lemmas ?? [];
  if (list.length === 0) {
    errors.push(`sources/reference/lemmas.json: ${key} 为空（ADR 0008）`);
  }
  for (const entry of list) {
    if (entry.lemma) allowedLemmas.add(String(entry.lemma).toLowerCase());
  }
}
const outlineFile = path.join(contentRoot, "sources/reference/exam-outline-lemmas.txt");
if (fs.existsSync(outlineFile)) {
  for (const line of fs.readFileSync(outlineFile, "utf8").split(/\r?\n/)) {
    const lemma = line.trim();
    if (lemma && !lemma.startsWith("#")) allowedLemmas.add(lemma.toLowerCase());
  }
}
const RELATIONS = new Set(["selection_basis", "quoted", "adapted", "exam_alignment"]);
const SKILLS = new Set(["listen", "speak", "read", "write"]);
let practiceItems = 0;
let assessmentItems = 0;

for (const source of catalog.sources ?? []) {
  if (!source.id || sourceIds.has(source.id)) {
    errors.push(`sources/catalog.json: 来源 id 缺失或重复 ${String(source.id)}`);
  }
  sourceIds.add(source.id);
  for (const field of ["kind", "title", "publisher", "url", "license", "checked_on", "usage_note"]) {
    if (!String(source[field] ?? "").trim()) {
      errors.push(`sources/catalog.json: ${source.id} 缺少 ${field}`);
    }
  }
  if (!String(source.url ?? "").startsWith("https://")) {
    errors.push(`sources/catalog.json: ${source.id} 必须使用 HTTPS 原始网址`);
  }
  if (source.license_url && !source.license_url.startsWith("https://")) {
    errors.push(`sources/catalog.json: ${source.id} 的 license_url 必须使用 HTTPS`);
  }
  if (source.local_path && !fs.existsSync(path.join(contentRoot, source.local_path))) {
    errors.push(`sources/catalog.json: ${source.id} 声明的本地文件不存在 ${source.local_path}`);
  }
}
if (sourceIds.size === 0) {
  errors.push("sources/catalog.json: 没有可核对的来源（ADR 0007）");
}
if (ngslAudit.source_id !== "ngsl-1.2" || !Array.isArray(ngslAudit.words) || ngslAudit.words.length === 0) {
  errors.push("sources/ngsl-1.2-used-words.json: 当前练习词的频率审计不完整");
}
for (const entry of ngslAudit.words ?? []) {
  if (!entry.lemma || !(entry.rank > 0) || (entry.frequency_per_million !== undefined && !(entry.frequency_per_million > 0))) {
    errors.push(`sources/ngsl-1.2-used-words.json: 非法词项 ${String(entry.lemma)}`);
  }
}

function validateRefs(refs, relative) {
  if (!Array.isArray(refs) || refs.length === 0) {
    errors.push(`${relative}: 缺少 source_refs（ADR 0007）`);
    return;
  }
  for (const ref of refs) {
    if (!sourceIds.has(ref.source_id)) {
      errors.push(`${relative}: 未知来源 ${ref.source_id}`);
    }
    if (!RELATIONS.has(ref.relation)) {
      errors.push(`${relative}: 非法来源关系 ${String(ref.relation)}`);
    }
    if (!ref.note?.trim()) {
      errors.push(`${relative}: ${ref.source_id} 的 note 不能空着`);
    }
    if (ref.locator_url && !ref.locator_url.startsWith("https://")) {
      errors.push(`${relative}: ${ref.source_id} 的 locator_url 必须使用 HTTPS`);
    }
  }
}

function readJson(relative) {
  const absolute = path.join(contentRoot, relative);
  if (!fs.existsSync(absolute)) {
    throw new Error(`缺少内容文件：content/${relative}`);
  }
  return JSON.parse(fs.readFileSync(absolute, "utf8"));
}

function normalized(text) {
  return text.replace(/\s+/g, " ").trim().toLowerCase();
}

function materialKeys(item) {
  const contexts = [item.sentence, item.text].filter(Boolean).map(normalized);
  return contexts.length > 0 ? contexts : [normalized(item.prompt)];
}

function validateItem(item, relative, assessment, deckRefs) {
  if (!item.id?.startsWith(assessment ? "en.assessment." : "en.")) {
    errors.push(`${relative}: 非法题目 id ${String(item.id)}`);
  }
  if (ids.has(item.id)) {
    errors.push(`${relative}: 重复题目 id ${item.id}，首次见于 ${ids.get(item.id)}`);
  } else {
    ids.set(item.id, relative);
  }
  if (item.choices) {
    const correct = item.choices.filter((choice) => choice.ok === true).length;
    if (correct !== 1) {
      errors.push(`${relative}: ${item.id} 必须且只能有一个正确选项，实际 ${correct}`);
    }
    if (!assessment && !item.variants?.length) {
      errors.push(`${relative}: ${item.id} 缺少错题出库所需的未见变式`);
    }
  } else if (assessment) {
    errors.push(`${relative}: ${item.id} 的独立考核暂不接受无法客观判分的开放题`);
  } else if (!(item.min_words > 0) || !item.reference || !item.checklist?.length) {
    errors.push(`${relative}: ${item.id} 的开放写作字段不完整`);
  }
  for (const [index, variant] of (item.variants ?? []).entries()) {
    const correct = (variant.choices ?? []).filter((choice) => choice.ok === true).length;
    if (correct !== 1) {
      errors.push(`${relative}: ${item.id} 变式 ${index + 1} 必须且只能有一个正确选项`);
    }
  }
  for (const asset of item.media ?? []) {
    if (!sourceIds.has(asset.source_id)) {
      errors.push(`${relative}: ${item.id} 的媒体引用了未知来源 ${asset.source_id}`);
    }
    if (!["audio", "video"].includes(asset.kind) || !asset.url?.startsWith("https://") || !asset.title) {
      errors.push(`${relative}: ${item.id} 的媒体字段不完整`);
    }
    const declared = [...(deckRefs ?? []), ...(item.source_refs ?? [])].some(
      (ref) => ref.source_id === asset.source_id,
    );
    if (!declared) {
      errors.push(`${relative}: ${item.id} 的媒体来源 ${asset.source_id} 没有出现在 source_refs`);
    }
  }
  validateRefs(item.source_refs, `${relative}#${item.id}`);
  if (!(item.source_refs ?? []).some((ref) => ref.relation === "quoted" || ref.relation === "adapted")) {
    errors.push(`${relative}: ${item.id} 必须直接绑定具体原文、例句或现实教材习题，选材依据和考试说明不能代替出处`);
  }
  if (assessment && ![...(deckRefs ?? []), ...(item.source_refs ?? [])].some((ref) => ref.relation === "exam_alignment")) {
    errors.push(`${relative}: ${item.id} 缺少英语二题型对齐依据`);
  }
  const materials = materialKeys(item);
  if (assessment) {
    assessmentMaterial.push([relative, item.id, materials]);
    assessmentItems += 1;
  } else {
    for (const material of materials) practiceMaterial.add(material);
    practiceItems += 1;
  }
}

const stageIds = new Set();
const trackIds = new Set();
for (const stage of curriculum.stages ?? []) {
  if (stageIds.has(stage.id)) errors.push(`curriculum.json: 重复阶段 id ${stage.id}`);
  stageIds.add(stage.id);
  for (const required of stage.requires ?? []) {
    if (!stageIds.has(required)) errors.push(`curriculum.json: ${stage.id} 的先修 ${required} 必须在它之前出现`);
  }
  const stageSkills = new Set();
  for (const track of stage.tracks ?? []) {
    if (trackIds.has(track.id)) errors.push(`curriculum.json: 重复轨道 id ${track.id}`);
    trackIds.add(track.id);
    if (!Array.isArray(track.skills) || track.skills.length === 0) {
      errors.push(`curriculum.json: ${track.id} 缺少听说读写 skills`);
    }
    for (const skill of track.skills ?? []) {
      if (!SKILLS.has(skill)) errors.push(`curriculum.json: ${track.id} 有非法 skill ${String(skill)}`);
      stageSkills.add(skill);
    }
    const level = stage.id.split(".").at(-1);
    const deckPaths = Array.isArray(track.decks) && track.decks.length > 0
      ? track.decks
      : typeof track.deck === "string" && track.deck
        ? [track.deck]
        : [];
    if (deckPaths.length === 0) {
      errors.push(`curriculum.json: ${track.id} 没有配置 deck 或 decks`);
    }
    for (const deckPath of deckPaths) {
      if (!deckPath.includes(`/${level}/`)) {
        errors.push(`curriculum.json: ${track.id} 的练习路径 ${deckPath} 没有落在 ${level} 等级目录`);
      }
    }
    if (!track.assessment.startsWith(`assessments/${level}/`)) {
      errors.push(`curriculum.json: ${track.id} 的考核路径没有落在 assessments/${level}/`);
    }
    const assessment = readJson(track.assessment);
    validateRefs(assessment.source_refs, track.assessment);
    if (assessment.topic_id !== track.id) errors.push(`${track.assessment}: topic_id 与 ${track.id} 不一致`);
    if (!assessment.assessment_id?.startsWith("en.assessment.")) {
      errors.push(`${track.assessment}: 缺少 en.assessment. 前缀的 assessment_id`);
    } else if (assessmentIds.has(assessment.assessment_id)) {
      errors.push(`${track.assessment}: 重复 assessment_id ${assessment.assessment_id}`);
    } else {
      assessmentIds.add(assessment.assessment_id);
    }
    const trackItems = [];
    for (const deckPath of deckPaths) {
      const practice = readJson(deckPath);
      validateRefs(practice.source_refs, deckPath);
      if (practice.topic_id !== track.id) errors.push(`${deckPath}: topic_id 与 ${track.id} 不一致`);
      if (deckPaths.length > 1 && practice.kind !== track.kind) {
        errors.push(`${deckPath}: 多单元题库的 kind 必须与轨道 ${track.kind} 一致`);
      }
      for (const item of practice.items ?? []) {
        validateItem(item, deckPath, false, practice.source_refs);
        trackItems.push(item);
        if (practice.kind === "vocab") {
          if (!item.word || !item.sentence || !item.senses?.length) {
            errors.push(`${deckPath}: ${item.id} 必须同时有 word、sentence 和 senses`);
          }
          if (item.word && !allowedLemmas.has(String(item.word).toLowerCase())) {
            errors.push(`${deckPath}: ${item.word} 不在本地 NGSL / NAWL / AWL 或已粘贴的大纲附录中`);
          }
        }
      }
      for (const asset of practice.media ?? []) {
        if (!sourceIds.has(asset.source_id) || !asset.url?.startsWith("https://")) {
          errors.push(`${deckPath}: 题库媒体来源或 HTTPS 地址无效`);
        }
        if (!(practice.source_refs ?? []).some((ref) => ref.source_id === asset.source_id)) {
          errors.push(`${deckPath}: 题库媒体来源 ${asset.source_id} 没有出现在 source_refs`);
        }
      }
    }
    for (const item of assessment.items ?? []) validateItem(item, track.assessment, true, assessment.source_refs);
    if ((assessment.items ?? []).length < 5) {
      errors.push(`${track.assessment}: 独立考核少于 5 题，无法稳定使用 80% 阈值`);
    }
    if (level === "beginner") {
      const minimums = track.kind === "vocab"
        ? { practice: 300, assessment: 30 }
        : track.kind === "sentence"
          ? { practice: 120, assessment: 30 }
          : { practice: 30, assessment: 20 };
      if (trackItems.length < minimums.practice) {
        errors.push(`curriculum.json: ${track.id} 只有 ${trackItems.length} 道练习，初级扩容基线为 ${minimums.practice}`);
      }
      if ((assessment.items ?? []).length < minimums.assessment) {
        errors.push(`${track.assessment}: 只有 ${(assessment.items ?? []).length} 道考核，初级扩容基线为 ${minimums.assessment}`);
      }
      if (track.kind === "sentence") {
        const translations = trackItems.filter((item) => item.kind === "translation").length;
        const passages = trackItems.filter((item) => item.kind === "passage_detail").length;
        if (translations < 60) errors.push(`curriculum.json: 初级英译汉只有 ${translations} 道，基线为 60`);
        if (passages < 30) errors.push(`curriculum.json: 初级短文只有 ${passages} 道，基线为 30`);
      }
    }
    if (track.passage && !fs.existsSync(path.join(contentRoot, track.passage))) {
      errors.push(`curriculum.json: 缺少短文 content/${track.passage}`);
    }
  }
  for (const skill of SKILLS) {
    if (!stageSkills.has(skill)) errors.push(`curriculum.json: ${stage.id} 没有覆盖 ${skill}`);
  }
}

for (const [relative, id, materials] of assessmentMaterial) {
  if (materials.some((material) => practiceMaterial.has(material))) {
    errors.push(`${relative}: ${id} 与练习材料完全相同`);
  }
}

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(
  `内容检查通过：${curriculum.stages.length} 个等级、${trackIds.size} 条轨、${practiceItems} 道练习、${assessmentItems} 道独立考核、${sourceIds.size} 个可核对来源、本地词表 ${allowedLemmas.size} 个 lemma。`,
);
