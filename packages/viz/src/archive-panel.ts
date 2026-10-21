// 历史归档条目的呈现件（ADR 0176）：多文件只读代码视图 + 行级批注 + 一键运行原代码。
//
// 纯呈现、props-only（ADR 0137）：不认识 Tauri，读文件与运行都通过 deps 回调交给应用。
// 原代码一个字符都不改，所以这里没有编辑器；批注是挂在行号上的新写内容。

export type ArchiveRunMode = "cli" | "toolchain" | "linux-only" | "read-only";

export interface ArchiveNote {
  file: string;
  line: number;
  /** 批注覆盖到哪一行（含）；省略即单行。 */
  end?: number;
  kind: "naming" | "ownership" | "coupling" | "testing" | "portability" | "style" | "design" | "other";
  text: string;
}

export interface ArchiveBlock {
  type: "archive";
  case: string;
  /** 参与编译的源文件（相对案例目录）；run 为 read-only 时可省略。 */
  sources?: string[];
  std?: string;
  run: ArchiveRunMode;
  /** 运行方式的补充说明，如“需要 Qt 6”“Windows 上请用 WSL”。 */
  run_note?: string;
  stdin?: string;
  summary?: string;
  origin: { repo: string; path: string; first_commit?: string; duplicates?: string[]; note?: string };
  notes: ArchiveNote[];
}

export interface ArchiveRunResult {
  ok: boolean;
  compiled: boolean;
  timed_out: boolean;
  exit_code: number | null;
  compile_log: string;
  stdout: string;
  stderr: string;
  duration_ms: number;
}

export interface ArchiveDeps {
  loadFiles(caseId: string): Promise<{ path: string; text: string }[]>;
  run(caseId: string, sources: string[], std?: string, stdin?: string): Promise<ArchiveRunResult>;
}

const KIND_LABEL: Record<ArchiveNote["kind"], string> = {
  naming: "命名",
  ownership: "资源与所有权",
  coupling: "耦合与职责",
  testing: "可测试性",
  portability: "可移植性",
  style: "风格",
  design: "设计",
  other: "其他",
};

const RUN_LABEL: Record<ArchiveRunMode, string> = {
  cli: "本机编译器可直接运行",
  toolchain: "需要额外工具链（见说明），仅看代码与批注",
  "linux-only": "依赖 Linux/POSIX，Windows 请在 WSL 里运行",
  "read-only": "只读：仅看代码与批注",
};

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/** 批注正文：先转义，再把 `反引号` 里的片段渲染成行内代码（批注里常要引用标识符）。 */
function noteHtml(s: string): string {
  return esc(s).replace(/`([^`]+)`/g, "<code>$1</code>");
}

export function mountArchivePanel(host: HTMLElement, block: ArchiveBlock, deps: ArchiveDeps): void {
  const o = block.origin;
  const dup = o.duplicates?.length ? `；另有重复拷贝：${o.duplicates.map(esc).join("、")}` : "";
  const runnable = block.run === "cli" || block.run === "linux-only";
  host.classList.add("arc-panel");
  host.innerHTML = `
    <div class="arc-origin"><b>出处</b> ${esc(o.repo)}/${esc(o.path)}${o.first_commit ? ` · 首次提交 ${esc(o.first_commit)}` : ""}${dup}${o.note ? ` · ${esc(o.note)}` : ""}</div>
    ${block.summary ? `<p class="arc-summary">${esc(block.summary)}</p>` : ""}
    <div class="arc-tabs" role="tablist"></div>
    <div class="arc-body">
      <pre class="arc-code" tabindex="0"></pre>
      <aside class="arc-notes"><h4>批注</h4><ol class="arc-note-list"></ol></aside>
    </div>
    <div class="arc-runbar">
      <button type="button" class="arc-run" ${runnable ? "" : "disabled"}>运行原代码</button>
      <span class="arc-run-hint">${esc(RUN_LABEL[block.run])}${block.run_note ? " · " + esc(block.run_note) : ""}</span>
    </div>
    <div class="arc-out" hidden></div>`;

  const tabs = host.querySelector<HTMLElement>(".arc-tabs")!;
  const code = host.querySelector<HTMLElement>(".arc-code")!;
  const noteList = host.querySelector<HTMLElement>(".arc-note-list")!;
  const runBtn = host.querySelector<HTMLButtonElement>(".arc-run")!;
  const out = host.querySelector<HTMLElement>(".arc-out")!;
  let files: { path: string; text: string }[] = [];

  function showFile(path: string, focusLine?: number) {
    tabs.querySelectorAll<HTMLElement>(".arc-tab").forEach((t) => t.classList.toggle("on", t.dataset.path === path));
    const f = files.find((x) => x.path === path);
    const lines = (f?.text ?? "").split("\n");
    // 行号 → 批注序号（全条目统一编号，跨文件也不重复）
    const marked = new Map<number, number>();
    block.notes.forEach((n, i) => {
      if (n.file !== path) return;
      for (let l = n.line; l <= (n.end ?? n.line); l++) if (!marked.has(l)) marked.set(l, i + 1);
    });
    code.innerHTML = lines
      .map((ln, i) => {
        const no = i + 1;
        const m = marked.get(no);
        return `<span class="arc-line${m ? " noted" : ""}" data-line="${no}"><i class="arc-no">${no}</i>${m ? `<b class="arc-mark" data-note="${m}">${m}</b>` : ""}<code>${esc(ln) || " "}</code></span>`;
      })
      .join("");
    noteList.innerHTML = block.notes.length
      ? block.notes
          .map(
            (n, i) =>
              `<li data-note="${i + 1}" data-file="${esc(n.file)}" data-line="${n.line}"><span class="arc-kind k-${n.kind}">${KIND_LABEL[n.kind] ?? "其他"}</span> <span class="arc-where">${esc(n.file)}:${n.line}${n.end ? "–" + n.end : ""}</span><div>${noteHtml(n.text)}</div></li>`,
          )
          .join("")
      : `<li class="arc-none">这个条目还没有批注。</li>`;
    if (focusLine) {
      const el = code.querySelector<HTMLElement>(`[data-line="${focusLine}"]`);
      el?.scrollIntoView({ block: "center" });
      el?.classList.add("flash");
      setTimeout(() => el?.classList.remove("flash"), 1200);
    }
  }

  noteList.addEventListener("click", (e) => {
    const li = (e.target as HTMLElement).closest<HTMLElement>("li[data-line]");
    if (li) showFile(li.dataset.file!, Number(li.dataset.line));
  });
  code.addEventListener("click", (e) => {
    const m = (e.target as HTMLElement).closest<HTMLElement>(".arc-mark");
    if (!m) return;
    const li = noteList.querySelector<HTMLElement>(`li[data-note="${m.dataset.note}"]`);
    li?.scrollIntoView({ block: "nearest" });
    li?.classList.add("flash");
    setTimeout(() => li?.classList.remove("flash"), 1200);
  });

  runBtn.addEventListener("click", async () => {
    if (!block.sources?.length) return;
    runBtn.disabled = true;
    out.hidden = false;
    out.innerHTML = `<div class="arc-wait">编译运行中…</div>`;
    try {
      const r = await deps.run(block.case, block.sources, block.std, block.stdin);
      const parts: string[] = [];
      if (!r.compiled) {
        parts.push(`<h5>编译失败</h5><pre>${esc(r.compile_log)}</pre>`);
      } else {
        if (r.compile_log.trim()) parts.push(`<details><summary>编译警告</summary><pre>${esc(r.compile_log)}</pre></details>`);
        parts.push(`<h5>标准输出</h5><pre>${esc(r.stdout) || "（无）"}</pre>`);
        if (r.stderr.trim()) parts.push(`<h5>标准错误</h5><pre>${esc(r.stderr)}</pre>`);
        const status = r.timed_out ? "运行超过 10 秒，已终止（老程序常等输入或常驻）" : `退出码 ${r.exit_code ?? "?"}`;
        parts.push(`<div class="arc-status ${r.ok ? "ok" : "bad"}">${status} · ${r.duration_ms} ms</div>`);
      }
      out.innerHTML = parts.join("");
    } catch (e) {
      out.innerHTML = `<div class="arc-status bad">${esc(String(e))}</div>`;
    } finally {
      runBtn.disabled = false;
    }
  });

  deps
    .loadFiles(block.case)
    .then((fs) => {
      files = fs;
      if (!fs.length) {
        code.textContent = "（案例目录是空的）";
        return;
      }
      const srcSet = new Set(block.sources ?? []);
      tabs.innerHTML = fs
        .map(
          (f) =>
            `<button type="button" class="arc-tab${srcSet.has(f.path) ? " src" : ""}" data-path="${esc(f.path)}" title="${srcSet.has(f.path) ? "参与编译" : "资源/配置"}">${esc(f.path)}</button>`,
        )
        .join("");
      tabs.addEventListener("click", (e) => {
        const t = (e.target as HTMLElement).closest<HTMLElement>(".arc-tab");
        if (t) showFile(t.dataset.path!);
      });
      const first = block.notes[0]?.file ?? block.sources?.find((s) => fs.some((f) => f.path === s)) ?? fs[0].path;
      showFile(first);
    })
    .catch((e) => {
      code.textContent = `读取案例失败：${e}`;
    });
}
