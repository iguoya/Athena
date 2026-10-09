// 把本机的教材资料（tiger 自己的课本/词表，个人自用，ADR 0019 `textbook` 来源）解析成
// content/private/textbook/<教材id>/parsed.json，供后续脚本生成句组、短文与写作素材（ADR 0022）。
//
//   pnpm content:textbook
//
// 放文件的位置和格式见 content/README.md「教材导入」。这里不下载任何东西：
// 教材内容永远不进 git、不进安装包，parsed.json 写在 private/ 里。

import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { CONTENT, today } from "./lib.mjs";

const TEXTBOOK_DIR = join(CONTENT, "private", "textbook");

// 词表行：`word<TAB>音标<TAB>释义` 或 `word<TAB>释义`；纯单词行也收（释义留空）。
function parseWordList(text) {
  const words = [];
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const [word, phonetic, ...rest] = trimmed.split(/\s*[\t|]\s*/);
    const cn = rest.length ? rest.join("；") : phonetic && /[^\x00-\x7F]/.test(phonetic) ? phonetic : "";
    if (!/^[A-Za-z][A-Za-z'-]*$/.test(word)) continue;
    words.push({ word: word.toLowerCase(), phonetic: cn && phonetic !== cn ? phonetic : "", cn });
  }
  return words;
}

if (!existsSync(TEXTBOOK_DIR)) {
  console.error(`没有找到 ${TEXTBOOK_DIR}。先按 content/README.md「教材导入」放好本机文件再运行。`);
  process.exit(1);
}

for (const book of readdirSync(TEXTBOOK_DIR, { withFileTypes: true })) {
  if (!book.isDirectory()) continue;
  const dir = join(TEXTBOOK_DIR, book.name);
  const wordFile = join(dir, "words.txt");
  if (!existsSync(wordFile)) {
    console.log(`${book.name}：没有 words.txt，跳过（放好后再跑一次）。`);
    continue;
  }
  const words = parseWordList(readFileSync(wordFile, "utf8"));
  const parsed = {
    about: `本机教材《${book.name}》的解析结果（个人自用，永远不进 git）。由 pnpm content:textbook 生成。`,
    book: book.name,
    generated: today(),
    wordCount: words.length,
    words,
  };
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "parsed.json"), JSON.stringify(parsed, null, 2) + "\n");
  console.log(`${book.name}：解析 ${words.length} 个词 → parsed.json`);
}
