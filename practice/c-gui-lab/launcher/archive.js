// 历史归档查看器（ADR 0176）：左侧按 [分组] 列条目，右侧显示讲解与代码批注面板。
// 面板来自仓库 packages/viz 的 archive-panel（vendor/ 下是它的 tsc 产物，改那边后重新生成）。
// 本应用不编译、不运行旧代码：run 回调一律拒绝（面板里的运行按钮对 toolchain/read-only 本就是禁用的）。
import { mountArchivePanel } from "./vendor/archive-panel.js";

const navEl = document.getElementById("nav");
const mainEl = document.getElementById("main");

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inline(text) {
  return esc(text).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
}
function groupOf(t) {
  const m = /^\[([^\]]+)\]\s*([\s\S]*)$/.exec(t.guide_line || "");
  return m ? { group: m[1], line: m[2] } : { group: "未分组", line: t.guide_line || "" };
}

function showTopic(t) {
  mainEl.innerHTML = `<article><h2>${esc(t.title)}</h2><p class="muted">${esc(groupOf(t).line)}</p></article>`;
  const article = mainEl.querySelector("article");
  for (const b of t.lesson.blocks) {
    if (b.type === "archive") {
      const host = document.createElement("div");
      article.appendChild(host);
      mountArchivePanel(host, b, {
        loadFiles: (caseId) => window.lab.archiveFiles(caseId),
        run: () => Promise.reject(new Error("本应用不运行旧代码")),
      });
    } else {
      const el = document.createElement(b.type === "callout" ? "aside" : "p");
      if (b.type === "lead") el.className = "lead";
      if (b.type === "callout") el.className = "callout";
      el.innerHTML = inline((b.title ? b.title + "：" : "") + b.text);
      article.appendChild(el);
    }
  }
  navEl.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x.dataset.id === t.id));
}

(async () => {
  const data = await window.lab.archiveData();
  const ch = data.chapters[0];
  document.getElementById("summary").textContent = ch.summary;
  const groups = new Map();
  for (const t of ch.topics) {
    const g = groupOf(t).group;
    groups.set(g, [...(groups.get(g) || []), t]);
  }
  for (const [g, ts] of groups) {
    const h = document.createElement("h3");
    h.textContent = g;
    navEl.appendChild(h);
    for (const t of ts) {
      const b = document.createElement("button");
      b.textContent = t.title;
      b.dataset.id = t.id;
      b.addEventListener("click", () => showTopic(t));
      navEl.appendChild(b);
    }
  }
})();
