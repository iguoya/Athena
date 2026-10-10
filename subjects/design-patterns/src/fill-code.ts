/**
 * 「代码填空」块：软考下午设计模式大题的作答形态（仓库 ADR 0121：软考作为专题练习）。
 *
 * 原题代码照样展示，在原来的「（n）」处放输入框。判分两道：
 * 1. 与官方答案比对（去掉空白与分号、全角符号转半角后逐字比较）；
 * 2. 比对不上时可以「代入编译运行」——把填写内容代入一份可编译的完整程序（template），
 *    用本机编译器真编译、真运行，输出满足 expect 即算通过。写法不同但等价的答案由
 *    编译器判对，不必穷举答案的各种写法。
 */

export type FillBlank = { n: number; answers: string[] };

export type FillSource = {
  relation: "verbatim" | "adapted";
  sourceId: string;
  locator: string;
  url?: string;
  why?: string;
};

export type FillCodeBlock = {
  type: "fillcode";
  id: string;
  title: string;
  statement: string;
  /** 展示用代码，「{{n}}」处渲染为输入框 */
  code: string;
  /** 代码之后的非代码填空（如「至少需要设计（7）个类」），同样用 {{n}} 标记，不参与编译 */
  after?: string;
  blanks: FillBlank[];
  /** 可编译的完整程序，代码里的空同样标 {{n}} */
  template: string;
  /** 运行输出必须全部包含这些子串 */
  expect: string[];
  /** 揭示答案时一并显示的要点 */
  notes?: string;
  source: FillSource;
};

export type FillStatus = "none" | "started" | "tried" | "done";

export type RunOutcome =
  | { kind: "unavailable"; message: string }
  | { kind: "result"; ok: boolean; compileLog: string; stdout: string; stderr: string };

export type FillContext = {
  escapeHtml: (s: string) => string;
  loadDraft: (key: string) => string | undefined;
  saveDraft: (key: string, value: string) => void;
  status: (key: string) => FillStatus;
  setStatus: (key: string, status: FillStatus) => Promise<void>;
  run: (block: FillCodeBlock, source: string) => Promise<RunOutcome>;
  /** 某道题的状态变了（用于刷新掌握度与导航） */
  onProgress: () => void;
};

export function fillKey(id: string): string {
  return `fill::${id}`;
}

const FULLWIDTH: Record<string, string> = {
  "（": "(", "）": ")", "＜": "<", "＞": ">", "，": ",", "；": ";", "：": ":", "＝": "=", "＊": "*",
  "－": "-", "＆": "&", "［": "[", "］": "]", "“": "\"", "”": "\"",
};

/** 比对前的规范化：全角转半角，去掉所有空白与末尾分号。 */
export function normalizeAnswer(s: string): string {
  return s
    .replace(/[（）＜＞，；：＝＊－＆［］“”]/g, (c) => FULLWIDTH[c] ?? c)
    .replace(/\s+/g, "")
    .replace(/;+$/, "");
}

function blankWidth(b: FillBlank): number {
  const longest = Math.max(...b.answers.map((a) => a.length), 4);
  return Math.min(48, longest + 3);
}

function renderWithInputs(text: string, block: FillCodeBlock, esc: (s: string) => string): string {
  const parts = text.split(/\{\{(\d+)\}\}/);
  return parts
    .map((part, i) => {
      if (i % 2 === 0) return esc(part);
      const n = Number(part);
      const blank = block.blanks.find((b) => b.n === n);
      const size = blank ? blankWidth(blank) : 10;
      return `<label class="fill-slot"><span class="fill-no">(${n})</span><input class="fill-input" data-blank="${n}" size="${size}" spellcheck="false" autocomplete="off" /></label>`;
    })
    .join("");
}

export function renderFillCode(block: FillCodeBlock, ctx: FillContext): string {
  const esc = ctx.escapeHtml;
  const st = ctx.status(fillKey(block.id));
  const statusText = st === "done" ? "已完成" : st === "tried" ? "未完成" : st === "started" ? "已开始" : "未作答";
  const src = block.source;
  const label = `${src.relation === "verbatim" ? "真题原题" : "真题改编"} · ${src.locator}`;
  const link = src.url
    ? `<a href="${esc(src.url)}" data-external target="_blank" rel="noreferrer">${esc(label)}</a>`
    : esc(label);
  return `<div class="card fillcode" data-fill="${esc(block.id)}">
    <h3>${esc(block.title)} <span class="badge fill-badge is-${st}">${statusText}</span></h3>
    <p class="prose fill-statement">${esc(block.statement)}</p>
    <pre class="fill-code">${renderWithInputs(block.code, block, esc)}</pre>
    ${block.after ? `<p class="prose fill-after">${renderWithInputs(block.after, block, esc)}</p>` : ""}
    <div class="fill-actions">
      <button type="button" class="primary" data-fill-check>核对答案</button>
      <button type="button" data-fill-run>代入编译运行</button>
      <button type="button" data-fill-reveal>显示参考答案</button>
      <span class="fill-summary" aria-live="polite"></span>
    </div>
    <div class="fill-result is-hidden"></div>
    <p class="quiz-source">${link}</p>
  </div>`;
}

function readValues(card: HTMLElement): Record<number, string> {
  const values: Record<number, string> = {};
  card.querySelectorAll<HTMLInputElement>(".fill-input").forEach((inp) => {
    values[Number(inp.dataset.blank)] = inp.value;
  });
  return values;
}

export function wireFillCode(panel: HTMLElement, blocks: FillCodeBlock[], ctx: FillContext): void {
  const esc = ctx.escapeHtml;
  for (const block of blocks) {
    const card = panel.querySelector<HTMLElement>(`[data-fill="${CSS.escape(block.id)}"]`);
    if (!card) continue;
    const key = fillKey(block.id);
    const inputs = Array.from(card.querySelectorAll<HTMLInputElement>(".fill-input"));
    const result = card.querySelector<HTMLElement>(".fill-result")!;
    const summary = card.querySelector<HTMLElement>(".fill-summary")!;

    // 恢复草稿
    try {
      const saved = JSON.parse(ctx.loadDraft(key) ?? "{}") as Record<string, string>;
      for (const inp of inputs) inp.value = saved[inp.dataset.blank ?? ""] ?? "";
    } catch {
      /* 坏草稿当作没有 */
    }

    let saveTimer = 0;
    for (const inp of inputs) {
      inp.addEventListener("input", () => {
        inp.classList.remove("is-ok", "is-bad");
        window.clearTimeout(saveTimer);
        saveTimer = window.setTimeout(() => ctx.saveDraft(key, JSON.stringify(readValues(card))), 400);
        if (ctx.status(key) === "none") void ctx.setStatus(key, "started");
      });
    }

    const show = (html: string) => {
      result.innerHTML = html;
      result.classList.remove("is-hidden");
    };

    const markDone = async () => {
      if (ctx.status(key) !== "done") {
        await ctx.setStatus(key, "done");
        ctx.onProgress();
      }
      const badge = card.querySelector(".fill-badge");
      if (badge) {
        badge.className = "badge fill-badge is-done";
        badge.textContent = "已完成";
      }
    };

    card.querySelector("[data-fill-check]")?.addEventListener("click", async () => {
      const values = readValues(card);
      let right = 0;
      for (const inp of inputs) {
        const n = Number(inp.dataset.blank);
        const blank = block.blanks.find((b) => b.n === n);
        const ok = !!blank && blank.answers.some((a) => normalizeAnswer(a) === normalizeAnswer(values[n] ?? ""));
        inp.classList.toggle("is-ok", ok);
        inp.classList.toggle("is-bad", !ok);
        if (ok) right += 1;
      }
      const total = inputs.length;
      summary.textContent = `与官方答案一致 ${right}/${total} 空`;
      if (right === total) {
        await markDone();
        show(`<p class="fill-ok">全部与官方答案一致。</p>`);
      } else {
        if (ctx.status(key) !== "done") await ctx.setStatus(key, "tried");
        show(
          `<p>标红的空与官方答案字面不一致。写法不同但意思相同的，可以点「代入编译运行」让编译器判断。</p>`,
        );
      }
    });

    card.querySelector("[data-fill-run]")?.addEventListener("click", async () => {
      const values = readValues(card);
      const source = block.template.replace(/\{\{(\d+)\}\}/g, (_, n: string) => values[Number(n)] ?? "");
      summary.textContent = "编译运行中…";
      const outcome = await ctx.run(block, source);
      if (outcome.kind === "unavailable") {
        summary.textContent = "";
        show(`<p>${esc(outcome.message)}</p>`);
        return;
      }
      const passed = outcome.ok && block.expect.every((s) => outcome.stdout.includes(s));
      summary.textContent = passed ? "编译运行通过" : outcome.compileLog.trim() && !outcome.stdout ? "编译未通过" : "运行结果不符";
      const log = outcome.compileLog.trim();
      show(`
        ${passed ? `<p class="fill-ok">代入后编译通过，运行结果符合题意。</p>` : `<p>代入后${log && !outcome.stdout ? "编译未通过" : "运行结果不符合题意"}。期望输出包含：${block.expect.map((s) => `<code>${esc(s)}</code>`).join("、")}</p>`}
        ${log ? `<div class="pane-title">编译信息</div><pre class="fill-out">${esc(log)}</pre>` : ""}
        ${outcome.stdout ? `<div class="pane-title">运行输出</div><pre class="fill-out">${esc(outcome.stdout)}</pre>` : ""}
        ${outcome.stderr ? `<pre class="fill-out">${esc(outcome.stderr)}</pre>` : ""}`);
      if (passed) await markDone();
      else if (ctx.status(key) !== "done") await ctx.setStatus(key, "tried");
    });

    card.querySelector("[data-fill-reveal]")?.addEventListener("click", () => {
      const rows = block.blanks
        .map((b) => `<li><b>(${b.n})</b> <code>${esc(b.answers[0])}</code>${b.answers.length > 1 ? `<span class="muted">（亦可：${b.answers.slice(1).map((a) => esc(a)).join("；")}）</span>` : ""}</li>`)
        .join("");
      show(`<div class="pane-title">参考答案</div><ul class="fill-answers">${rows}</ul>${block.notes ? `<p class="prose">${esc(block.notes)}</p>` : ""}`);
    });
  }
}
