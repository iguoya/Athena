// 把每个词库按真实难度信号先易后难切成子阶段，生成 content/vocab/<考试>/stages.json（ADR 0022）。
//
//   pnpm content:stages
//
// 排序只用已入库的真实信号（ECDICT 词频与星级、Oxford 3000、本机统计的四级真题词频），
// 不引入出处不明的第三方数据；公式改系数后重跑本脚本即可，stages.json 是产物不手改。

import { join } from "node:path";
import { CONTENT, readJson, today, writeJsonLines } from "./lib.mjs";

const EXAMS = [
  { id: "hs", label: "高中" },
  { id: "cet4", label: "四级" },
  { id: "cet6", label: "六级" },
];

// 每阶目标词数：约等于每天 15 个新词（AGENTS.md 上限）学一个月。
const TARGET_SIZE = 450;

// 登山段落名呼应「拾阶」；阶段数变化时超出部分回退成「第 N 阶」。
const TIER_NAMES = {
  hs: ["山脚起步", "稳步石阶", "林间小径", "半山小憩", "拾级陡梯", "云雾栈道", "峰顶在望", "登顶摘星"],
  cet4: ["起步", "进阶", "强化", "冲刺"],
  cet6: ["拓界", "进阶", "强化", "冲刺"],
};

const TIER_BLURBS = {
  hs: [
    "真实语料里最常见的词，先和它们混个脸熟。",
    "高频词站稳了，句子就开始眼熟了。",
    "换成更书面的常用词，句子复杂了一点点。",
    "过半啦。这些词在考试里很能打。",
    "开始吃力是正常的：这批词不那么「日常」了。",
    "云雾路段，慢慢走，别贪多。",
    "峰顶在望，这批学完高中词就通关了。",
    "最后一批。走完这段，高中词库全部踩过一遍。",
  ],
  cet4: [
    "四级新增词里最常用的先来。",
    "读物和真题里的常客，见得会越来越多。",
    "中坚段：阅读理解卡分的就是它们。",
    "最后一批，背完四级新增词全部过一遍。",
  ],
  cet6: [
    "六级比四级多出来的词里最常用的。",
    "更书面、更学术，报刊里常见。",
    "难啃的一段，一天 15 个就够。",
    "最后一批。背完这里，六级词库全部踩过一遍。",
  ],
};

/** 难度分，越小越易（ADR 0022 的公式）。frq 是 ECDICT 语料词频「排名」，1 最常用。 */
function difficulty(word, medianFrq, examHits) {
  return (
    Math.log10((word.frq || medianFrq) + 1) +
    (word.collins ? (5 - word.collins) * 0.35 : 0.35) +
    (word.oxford3000 ? -0.3 : 0) +
    Math.min(word.word.length, 12) * 0.02 -
    Math.log10((examHits || 0) + 1) * 0.2
  );
}

for (const exam of EXAMS) {
  const dir = join(CONTENT, "vocab", exam.id);
  const words = readJson(join(dir, "words.json")).words;
  const seen = new Set(words.map((w) => w.word));
  if (seen.size !== words.length) throw new Error(`${exam.id} 词表有重复词`);

  const freqFile = readJson(join(dir, "exam-frequency.json"));
  const examHits = new Map(freqFile.words.map((f) => [f.word, f.hits]));

  // 没有词频排名的词（约 3%）按该词库的中位数给保守难度。
  const ranked = words
    .map((w) => w.frq || 0)
    .filter((f) => f > 0)
    .sort((a, b) => a - b);
  const medianFrq = ranked[Math.floor(ranked.length / 2)] ?? 5000;

  const sorted = [...words]
    .map((w) => ({ ...w, score: difficulty(w, medianFrq, examHits.get(w.word)) }))
    .sort((a, b) => a.score - b.score || a.word.localeCompare(b.word));

  // 阶段数取「每阶约 450 词」的最近值，各阶均匀（最后一位余数摊薄）。
  const count = Math.max(1, Math.round(words.length / TARGET_SIZE));
  const size = Math.ceil(words.length / count);

  const names = TIER_NAMES[exam.id];
  const blurbs = TIER_BLURBS[exam.id];
  const stages = Array.from({ length: count }, (_, i) => {
    const slice = sorted.slice(i * size, (i + 1) * size);
    const name = names[i] ?? `第 ${i + 1} 阶`;
    return {
      id: `${exam.id}-${String(i + 1).padStart(2, "0")}`,
      title: `${exam.label} · 第 ${i + 1} 阶 · ${name}`,
      blurb: blurbs[i] ?? "一步一步来。每天 15 个，一个月一阶。",
      words: slice.map((w) => w.word),
    };
  });

  writeJsonLines(
    join(dir, "stages.json"),
    {
      about:
        `词库分阶（ADR 0022）：按真实难度信号先易后难。难度分 = log10(ECDICT 词频排名 frq+1，缺排名按中位数) ` +
        `+ (5-Collins 星级)×0.35 + Oxford3000 减 0.3 + 词长×0.02 - log10(四级真题词频+1)×0.2，` +
        `分小者先学。每阶约 ${TARGET_SIZE} 词 ≈ 每天 15 个新词学一个月。产物由 pnpm content:stages 生成，不手改。`,
      exam: exam.id,
      stageSize: size,
      generated: today(),
      source: "ecdict",
    },
    "stages",
    stages,
  );
}
