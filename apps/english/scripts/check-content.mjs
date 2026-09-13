import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const contentRoot = path.join(appRoot, "content");
const curriculum = readJson("curriculum.json");
const errors = [];
const ids = new Map();
const assessmentIds = new Set();
const practiceMaterial = new Set();
const assessmentMaterial = [];
let practiceItems = 0;
let assessmentItems = 0;

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

function validateItem(item, relative, assessment) {
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
  for (const track of stage.tracks ?? []) {
    if (trackIds.has(track.id)) errors.push(`curriculum.json: 重复轨道 id ${track.id}`);
    trackIds.add(track.id);
    const level = stage.id.split(".").at(-1);
    if (!track.deck.includes(`/${level}/`)) {
      errors.push(`curriculum.json: ${track.id} 的练习路径没有落在 ${level} 等级目录`);
    }
    if (!track.assessment.startsWith(`assessments/${level}/`)) {
      errors.push(`curriculum.json: ${track.id} 的考核路径没有落在 assessments/${level}/`);
    }
    const practice = readJson(track.deck);
    const assessment = readJson(track.assessment);
    if (practice.topic_id !== track.id) errors.push(`${track.deck}: topic_id 与 ${track.id} 不一致`);
    if (assessment.topic_id !== track.id) errors.push(`${track.assessment}: topic_id 与 ${track.id} 不一致`);
    if (!assessment.assessment_id?.startsWith("en.assessment.")) {
      errors.push(`${track.assessment}: 缺少 en.assessment. 前缀的 assessment_id`);
    } else if (assessmentIds.has(assessment.assessment_id)) {
      errors.push(`${track.assessment}: 重复 assessment_id ${assessment.assessment_id}`);
    } else {
      assessmentIds.add(assessment.assessment_id);
    }
    for (const item of practice.items ?? []) validateItem(item, track.deck, false);
    for (const item of assessment.items ?? []) validateItem(item, track.assessment, true);
    if ((assessment.items ?? []).length < 5) {
      errors.push(`${track.assessment}: 独立考核少于 5 题，无法稳定使用 80% 阈值`);
    }
    if (track.passage && !fs.existsSync(path.join(contentRoot, track.passage))) {
      errors.push(`curriculum.json: 缺少短文 content/${track.passage}`);
    }
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
  `内容检查通过：${curriculum.stages.length} 个等级、${trackIds.size} 条轨、${practiceItems} 道练习、${assessmentItems} 道独立考核。`,
);
