// 跨应用检查「内容必须有出处」（ADR 0043）。
//
// 三个独立应用各自写了一份「题目要有出处」的 ADR，精神一致、落地程度天差地别：
// mathematics 有 19 处机械校验，c 一处都没有——而它的 ADR 白纸黑字要求每条都有
// source_refs。规范写在文档里而没有检查兜住，等于没写。
//
// 这个脚本只读不写，不参与任何应用的构建，因此不构成 ADR 0032 禁止的耦合——
// 那条禁的是运行时与构建期依赖，开发期的横向检查不在其列。
//
// 各应用字段名不同，靠 subjects/<app>/content-contract.json 认路。没有那份文件的
// 应用报「未接入」而不是默默跳过：沉默地通过是最坏的结果。
//
// 跑法：node scripts/check-app-sources.mjs

import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const appsDir = join(root, "subjects");

/**
 * 与原材料的关系（ADR 0043 第 2 节第 3 条）。
 * 分两类是 english 的实践逼出来的：它用了 quoted / selection_basis /
 * exam_alignment 四种值，其中后两个根本不是「这段内容出自哪」，而是
 * 「为什么选它」和「对应考纲哪一条」——把它们和内容来源混在一个枚举里，
 * 就没法要求「每条至少有一个内容来源」了。
 */
const CONTENT_RELATIONS = new Set(["verbatim", "quoted", "adapted", "authored"]);
/** 这些是补充说明，可以有，但不能拿来顶替内容来源 */
const META_RELATIONS = new Set(["selection_basis", "exam_alignment", "see_also"]);

function readJson(p) {
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

/** 递归收集内容目录下的 json；node_modules 之类不会出现在 content/ 里，无需排除 */
function jsonFiles(dir, out = []) {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) jsonFiles(p, out);
    else if (name.endsWith(".json")) out.push(p);
  }
  return out;
}

/**
 * 深度遍历，找出所有「判分条目」——由契约里的 itemMarkers 认定。
 *
 * 带 `inherited`：一道题的变式（english 的 variants）自己不写来源，
 * 它共享母题的。这是合理设计，不是缺口——第一版没考虑，误报了 471 条，
 * 而误报多了人就会把整项检查一起忽略掉。
 */
function collectItems(node, markers, sourceField, inherited = null, acc = []) {
  if (Array.isArray(node)) {
    for (const v of node) collectItems(v, markers, sourceField, inherited, acc);
    return acc;
  }
  if (node && typeof node === "object") {
    const own = node[sourceField];
    const nextInherited = own ?? inherited;
    if (markers.some((m) => m in node)) acc.push({ item: node, inherited });
    for (const v of Object.values(node)) collectItems(v, markers, sourceField, nextInherited, acc);
  }
  return acc;
}

/** 从一条条目里取出它的来源引用，拉平成统一形状 */
function refsOf(item, c) {
  const raw = item[c.sourceField];
  if (!raw) return [];
  const list = Array.isArray(raw) ? raw : [raw];
  return list.map((r) => ({
    relation: r[c.relationField],
    sourceId: c.sourceIdField ? r[c.sourceIdField] : undefined,
    url: c.urlFields.map((f) => r[f]).find(Boolean),
    locator: c.locatorFields.map((f) => r[f]).find(Boolean),
    why: c.whyFields.map((f) => r[f]).find(Boolean),
    raw: r,
  }));
}

let hardFail = 0;
const report = [];

for (const app of readdirSync(appsDir).sort()) {
  const appDir = join(appsDir, app);
  if (!statSync(appDir).isDirectory()) continue;

  const contractPath = join(appDir, "content-contract.json");
  if (!existsSync(contractPath)) {
    report.push({ app, state: "未接入", detail: "缺 content-contract.json（ADR 0043 第 5 节）" });
    continue;
  }
  const c = readJson(contractPath);
  if (!c) {
    report.push({ app, state: "契约损坏", detail: "content-contract.json 不是合法 JSON" });
    hardFail++;
    continue;
  }
  // 契约字段给默认值，免得每个应用都要写全
  c.urlFields ??= ["url", "locator_url"];
  c.locatorFields ??= ["locator", "ref", "loc"];
  c.whyFields ??= ["why", "note"];
  c.relationField ??= "relation";
  // 条目的标识字段。默认认 id / stem，但 subjects/cpp 的知识点用 name——认不出来
  // 时每条的 key 都会退化成「(无 id)」，全部撞在一起，豁免名单写了也不生效。
  c.idFields ??= ["id", "stem"];

  const contentDir = join(appDir, c.contentDir ?? "content");
  const catalogIds = new Set();
  if (c.catalog) {
    const cat = readJson(join(contentDir, c.catalog));
    if (cat) {
      const list = Array.isArray(cat.sources) ? cat.sources : Object.keys(cat).map((k) => ({ id: k }));
      for (const s of list) if (s?.id) catalogIds.add(s.id);
    }
  }

  const issues = [];
  let total = 0;
  let sourced = 0;
  let authored = 0;
  const perSection = new Map(); // 节 → [总数, 自造数]，用来查配额

  for (const file of jsonFiles(contentDir)) {
    // catalog 与参考材料本身不是判分条目
    if (c.catalog && file.endsWith(c.catalog)) continue;
    if (file.includes(`${c.contentDir ?? "content"}/sources/`)) continue;
    const data = readJson(file);
    if (!data) continue;
    const rel = relative(appDir, file);

    for (const { item, inherited } of collectItems(data, c.itemMarkers, c.sourceField)) {
      total++;
      const id =
        c.idFields.map((f) => item[f]).find((v) => typeof v === "string")?.slice(0, 18) ??
        "(无 id)";
      // 一个条目一个 key，报错和豁免都用它。分成两种写法（一处带空格一处不带）
      // 会让豁免名单看着写了却不生效——而且两边单看都正常。
      const key = `${rel} :: ${id}`;
      let refs = refsOf(item, c);
      // 自己没写就看母题的（变式共享来源）
      let viaInherit = false;
      if (!refs.length && inherited) {
        refs = refsOf({ [c.sourceField]: inherited }, c);
        viaInherit = refs.length > 0;
      }
      if (!refs.length) {
        // 存量豁免：契约里列出的，先记着不当失败
        if (!(c.legacyUnsourced ?? []).includes(key)) {
          issues.push(`${key} 没有来源标记`);
        }
        continue;
      }
      sourced++;
      // 继承来的不重复计入配额：配额管的是「这一节自己出了多少自造题」
      const st = perSection.get(rel) ?? [0, 0];
      if (!viaInherit) st[0]++;

      let hasContentRel = false;
      for (const r of refs) {
        if (META_RELATIONS.has(r.relation)) continue; // 补充说明，不算内容来源
        if (!CONTENT_RELATIONS.has(r.relation)) {
          issues.push(
            `${key} 的关系「${r.relation ?? "缺失"}」既不是内容来源` +
              `（verbatim/quoted/adapted/authored）也不是已知的补充说明`,
          );
          continue;
        }
        hasContentRel = true;
        if (r.relation === "authored") {
          authored++;
          if (!viaInherit) st[1]++;
          if (!r.why) issues.push(`${key} 标了 authored 却没说明为什么没有现成材料`);
        } else {
          // 可核对：要么 URL 打得开，要么 catalog 里有这条，要么指到本地文件
          const okUrl = r.url && /^https?:\/\//.test(r.url);
          const okCatalog = r.sourceId && catalogIds.has(r.sourceId);
          if (r.sourceId && catalogIds.size && !catalogIds.has(r.sourceId)) {
            issues.push(`${key} 引的来源 id「${r.sourceId}」不在 catalog 里`);
          } else if (!okUrl && !okCatalog && !r.locator) {
            issues.push(`${key} 的出处指不到具体位置`);
          }
        }
      }
      const allMeta = refs.every((r) => META_RELATIONS.has(r.relation));
      if (!hasContentRel && !viaInherit && allMeta) {
        issues.push(`${key} 只标了补充说明，没有一条说明内容出自哪里`);
      }
      perSection.set(rel, st);
    }
  }

  // 自造配额：一节内不得过半（ADR 0043 第 2 节第 4 条）
  for (const [sec, [n, a]] of perSection) {
    if (n >= 2 && a * 2 > n) issues.push(`${sec} 的 ${n} 条里有 ${a} 条自造（过半）`);
  }

  report.push({
    app,
    state: issues.length ? "有问题" : "达标",
    total,
    sourced,
    authored,
    legacy: (c.legacyUnsourced ?? []).length,
    issues,
    blocking: c.blocking !== false,
  });
  if (issues.length && c.blocking !== false) hardFail += issues.length;
}

// ── 输出 ──
console.log("跨应用「内容必须有出处」检查（ADR 0043）\n");
for (const r of report) {
  if (r.state === "未接入" || r.state === "契约损坏") {
    console.log(`  ${r.app.padEnd(12)} ${r.state} —— ${r.detail}`);
    continue;
  }
  const quota = r.total ? ` 自造 ${r.authored}` : "";
  const legacy = r.legacy ? ` 存量豁免 ${r.legacy}` : "";
  const mode = r.blocking ? "" : "（只报告）";
  console.log(
    `  ${r.app.padEnd(12)} ${r.state}${mode}：${r.sourced}/${r.total} 条有出处${quota}${legacy}`,
  );
  for (const i of r.issues.slice(0, 8)) console.log(`      · ${i}`);
  if (r.issues.length > 8) console.log(`      · …另有 ${r.issues.length - 8} 条`);
}

const notWired = report.filter((r) => r.state === "未接入").map((r) => r.app);
if (notWired.length) {
  console.log(`\n未接入：${notWired.join("、")}。加一份 content-contract.json 即可纳入检查。`);
}
if (hardFail) {
  console.error(`\n共 ${hardFail} 处问题（只报告模式的应用不计入）。见 ADR 0043。`);
  process.exit(1);
}
console.log("\n通过。");
