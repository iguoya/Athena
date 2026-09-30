// Shared helpers for the content import scripts (ADR 0019).
// Downloads are cached in .cache/content/ (git-ignored), so re-running a script does not re-download.

import { createWriteStream, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const Bunzip = createRequire(import.meta.url)("./vendor/seek-bzip/index.cjs");

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
export const CACHE = join(ROOT, ".cache/content");
export const CONTENT = join(ROOT, "content");

/** Download `url` into the cache (or reuse the cached copy) and return the local path. */
export async function download(url, name = url.split("/").pop()) {
  mkdirSync(CACHE, { recursive: true });
  const dest = join(CACHE, name);
  if (existsSync(dest)) return dest;
  console.log(`下载 ${url}`);
  const res = await fetch(url);
  if (!res.ok || !res.body) {
    throw new Error(
      `下载失败 ${res.status}: ${url}\n可以手动下载这个文件放到 ${dest} 再重新运行。` +
        `\n如果走代理，先设置 NODE_USE_ENV_PROXY=1 和 HTTPS_PROXY。`,
    );
  }
  const tmp = `${dest}.part`;
  await pipeline(Readable.fromWeb(res.body), createWriteStream(tmp));
  renameSync(tmp, dest);
  return dest;
}

/** Read a file as text, transparently decompressing `.bz2`. */
export function readText(path) {
  const buf = readFileSync(path);
  return (path.endsWith(".bz2") ? Bunzip.decode(buf) : buf).toString("utf8");
}

/** Split TSV text into rows of columns, skipping empty lines. */
export function tsvRows(text) {
  return text
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => line.replace(/\r$/, "").split("\t"));
}

/** Write JSON with one array item per line: readable in git diffs, small on disk. */
export function writeJsonLines(path, header, key, items) {
  mkdirSync(dirname(path), { recursive: true });
  const head = JSON.stringify(header, null, 2).replace(/\n}$/, "");
  const body = items.map((item) => "    " + JSON.stringify(item)).join(",\n");
  writeFileSync(path, `${head},\n  ${JSON.stringify(key)}: [\n${body}\n  ]\n}\n`);
  console.log(`写入 ${path.slice(ROOT.length + 1)}（${items.length} 条）`);
}

export function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function today() {
  return new Date().toISOString().slice(0, 10);
}
