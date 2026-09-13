// 随堂练习与章末小考（ADR 0014）。
// 与「先猜再验」的预测题分工不同：预测题制造好奇，练习题检验会不会。
// 这里必须有要动笔算的题型——全是看图选，人可以一次笔不动就「走完」整章。

export interface DrillOption {
  text: string;
  ok?: boolean;
  why?: string;
  misread?: string;
}

export interface DrillItem {
  id: string;
  /** number 要算出数值，choice 是判断题 */
  kind: "number" | "choice";
  stem: string;
  /** number 题的答案与容差 */
  answer?: number;
  tol?: number;
  options?: DrillOption[];
  /** 卡住时先给方向，不直接给答案（ADR 0011 第 1 节） */
  hint?: string;
  /** 判完之后说明它为什么是这样 */
  why?: string;
  /** 这一题是在前一题基础上改了什么——变式练习的关键（ADR 0014 第 1 节） */
  varies?: string;
}

export interface DrillSet {
  title: string;
  intro?: string;
  items: DrillItem[];
}

export interface DrillState {
  picked?: string;
  value?: string;
  correct?: boolean;
  hintShown?: boolean;
}

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** 正文里的重点标记，与 main.ts 的 rich 保持一致 */
function rich(src: string): string {
  return esc(src)
    .replace(/\*\*(.+?)\*\*/g, '<b class="em">$1</b>')
    .replace(/==(.+?)==/g, '<mark class="hl">$1</mark>')
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

export function numberOk(item: DrillItem, raw: string): boolean {
  const v = Number(raw.trim().replace(/。|，/g, ""));
  if (!Number.isFinite(v)) return false;
  return Math.abs(v - (item.answer ?? NaN)) <= (item.tol ?? 1e-6);
}

function renderItem(it: DrillItem, idx: number, st: DrillState | undefined, ns: string): string {
  const done = st?.correct === true;
  const wrong = st?.correct === false;

  const body =
    it.kind === "number"
      ? `<div class="dr-num">
           <input type="text" inputmode="decimal" id="${ns}-in-${it.id}"
                  value="${st?.value ?? ""}" placeholder="填一个数"${done ? " disabled" : ""}>
           <button type="button" data-drill="${it.id}" data-ns="${ns}"${done ? " disabled" : ""}>对一下</button>
         </div>`
      : `<div class="dr-opts">
           ${(it.options ?? [])
             .map(
               (o) =>
                 `<button type="button" data-drill="${it.id}" data-ns="${ns}"
                    data-pick="${esc(o.text).replace(/"/g, "&quot;")}" data-ok="${o.ok ? 1 : 0}"
                    class="${st?.picked === o.text ? (o.ok ? "picked right" : "picked wrong") : ""}"
                    ${done ? "disabled" : ""}>${rich(o.text)}</button>`,
             )
             .join("")}
         </div>`;

  let fb = "";
  if (done) {
    fb = `<div class="dr-fb ok"><b>对。</b>${rich(it.why ?? "")}</div>`;
  } else if (wrong) {
    const chosen = (it.options ?? []).find((o) => o.text === st?.picked);
    fb = `<div class="dr-fb re">${
      chosen?.misread
        ? `<b>这个选项通常是这么想的：</b>${rich(chosen.misread)}`
        : "<b>再算一次。</b>"
    }${
      st?.hintShown && it.hint ? `<div class="dr-hint">提示：${rich(it.hint)}</div>` : ""
    }</div>`;
  }

  return `<li class="dr-item${done ? " done" : ""}">
      <div class="dr-stem"><span class="dr-no">${idx + 1}</span>${rich(it.stem)}</div>
      ${it.varies ? `<div class="dr-varies">与上一题相比：${rich(it.varies)}</div>` : ""}
      ${body}
      ${fb}
      ${
        !done && it.hint && !st?.hintShown
          ? `<button type="button" class="dr-hintbtn" data-hint="${it.id}" data-ns="${ns}">看提示</button>`
          : ""
      }
    </li>`;
}

export function renderDrills(
  set: DrillSet,
  states: Map<string, DrillState>,
  ns: string,
): string {
  const done = set.items.filter((i) => states.get(i.id)?.correct).length;
  return `<div id="s-${ns}" class="drills">
      <h3>${esc(set.title)}<span class="dr-prog">${done} / ${set.items.length}</span></h3>
      ${set.intro ? `<p class="dr-intro">${rich(set.intro)}</p>` : ""}
      <ol class="dr-list">
        ${set.items.map((it, i) => renderItem(it, i, states.get(it.id), ns)).join("")}
      </ol>
    </div>`;
}
