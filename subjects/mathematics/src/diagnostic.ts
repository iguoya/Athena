// 前置基础诊断页（ADR 0015 第 4 节）。
// 只判「需不需要补」：不打分、不排名、不显示正确率，结果只用来决定要不要把这一项
// 插进学习路径。措辞受 ADR 0013、ADR 0015 第 5 节约束。

export interface DiagOption {
  text: string;
  ok?: boolean;
  /** 选它通常对应什么想法——不是「你错了」，是「这个选项是这么想的」（ADR 0014 第 5 节） */
  misread?: string;
  /** 选对时补一句它后面用在哪，建立前置与主线的连接（ADR 0008） */
  note?: string;
}
export interface DiagSource {
  relation: "verbatim" | "adapted" | "authored";
  site?: string;
  locator?: string;
  url?: string;
  note?: string;
}
export interface DiagItem {
  id: string;
  stem: string;
  /** 出处（主仓库 ADR 0043）。答完之后显示，顺着它能去补这一块 */
  source_refs?: DiagSource[];
  options: DiagOption[];
}
export interface DiagGroup {
  id: string;
  title: string;
  blocks_what: string;
  items: DiagItem[];
}
/**
 * 出处一行。诊断页答完就显示（不像练习题要等答对）——这一页的目的本来就是
 * 「看看哪些需要补」，答错的人最需要的正是「去哪里补」。
 */
function sourceLine(refs?: DiagSource[]): string {
  // 每题一个来源，渲染第一条（字段名见主仓库 ADR 0043 的统一命名）。
  const src = refs?.[0];
  if (!src) return "";
  if (src.relation === "authored") return "";
  const who = [src.site, src.locator].filter(Boolean).join(" · ");
  const link = src.url
    ? `<a href="${src.url}" target="_blank" rel="noreferrer">${esc(who)}</a>`
    : esc(who);
  return `<div class="d-src">要补这一块，看 ${link}</div>`;
}

export interface Diagnostics {
  title: string;
  intro: string;
  advice_rule: Record<string, string>;
  groups: DiagGroup[];
}

export interface Answer {
  picked: string;
  correct: boolean;
}

/** 错题数 → 建议。三档，不是分数。 */
export function adviceOf(rule: Record<string, string>, wrong: number): string {
  return rule[String(Math.min(wrong, 3))] ?? "建议先补";
}

export function adviceClass(advice: string): string {
  if (advice.includes("跳过")) return "skip";
  if (advice.includes("扫")) return "glance";
  return "study";
}

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export function renderDiagnostics(
  d: Diagnostics,
  answers: Map<string, Answer>,
): string {
  const key = (g: string, i: string) => `${g}::${i}`;

  const doneGroups = d.groups.filter((g) =>
    g.items.every((it) => answers.has(key(g.id, it.id))),
  ).length;

  const groupsHtml = d.groups
    .map((g) => {
      const answered = g.items.filter((it) => answers.has(key(g.id, it.id)));
      const complete = answered.length === g.items.length;
      const wrong = answered.filter((it) => !answers.get(key(g.id, it.id))!.correct).length;
      const advice = complete ? adviceOf(d.advice_rule, wrong) : "";

      const itemsHtml = g.items
        .map((it, idx) => {
          const a = answers.get(key(g.id, it.id));
          const opts = it.options
            .map((o) => {
              const picked = a?.picked === o.text;
              const cls = [
                "d-opt",
                picked ? "picked" : "",
                picked && o.ok ? "right" : "",
                picked && !o.ok ? "wrong" : "",
              ]
                .filter(Boolean)
                .join(" ");
              return `<button class="${cls}" data-g="${g.id}" data-i="${it.id}"
                        data-ok="${o.ok ? 1 : 0}" data-text="${esc(o.text)}">${esc(o.text)}</button>`;
            })
            .join("");

          let feedback = "";
          if (a) {
            const chosen = it.options.find((o) => o.text === a.picked);
            if (chosen?.ok) {
              // 通用表扬（「答对了」）廉价且可疑；说清你避开了哪些具体误解才有分量
              const traps = it.options
                .filter((o) => !o.ok && o.misread)
                .map((o) => o.misread!.split("。")[0])
                .join("；");
              feedback = `<div class="d-fb ok">
                  ${chosen.note ? `<b>这一点后面会用到。</b>${esc(chosen.note)}` : ""}
                  ${
                    traps
                      ? `<div class="d-traps">另外两个选项是这么想的：${esc(traps)}。
                         你没往那边走。</div>`
                      : ""
                  }
                  ${sourceLine(it.source_refs)}
                </div>`;
            } else if (chosen?.misread) {
              const right = it.options.find((o) => o.ok);
              feedback = `<div class="d-fb re"><b>这个选项通常是这么想的：</b>${esc(
                chosen.misread,
              )}${right ? `<div class="d-right">正确的是：${esc(right.text)}</div>` : ""}${sourceLine(
                it.source_refs,
              )}</div>`;
            }
          }

          return `<div class="d-item">
              <div class="d-stem"><span class="d-no">${idx + 1}</span>${esc(it.stem)}</div>
              <div class="d-opts">${opts}</div>
              ${feedback}
            </div>`;
        })
        .join("");

      const passed = complete && wrong === 0;
      return `<section class="d-group${complete ? " done" : ""}${passed ? " passed" : ""}">
          <header>
            <h3>${passed ? '<span class="tick">✓</span>' : ""}${esc(g.title)}</h3>
            ${
              advice
                ? `<span class="d-advice ${adviceClass(advice)}">${esc(advice)}</span>`
                : `<span class="d-advice pending">${answered.length} / ${g.items.length}</span>`
            }
          </header>
          <p class="d-blocks">不补的话，后面会卡在：${esc(g.blocks_what)}</p>
          ${itemsHtml}
        </section>`;
    })
    .join("");

  return `<div class="page">
      <h2 class="title">${esc(d.title)}</h2>
      <div class="hook"><p>${esc(d.intro)}</p></div>
      <div class="d-progress">六组里已答完 <b>${doneGroups}</b> 组</div>
      ${groupsHtml}
    </div>`;
}
