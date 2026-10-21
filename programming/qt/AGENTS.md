# Qt 应用协作规则

仓库级规则见根 `AGENTS.md`，本文只写本应用自己的约定。目录 id `qt`，进程 `athena-qt`，知识点前缀 `qt.`，
dev 端口 **1526**，进度库目录 `AthenaQt`。本应用是**学习应用**（三类判据见 `docs/REPOSITORY.md`）。

## 现状：只有「历史归档」，主线尚未编写

- 本应用由 ADR 0176 建立，目的是接收旧 GitHub 仓库里Qt Widgets / QML / PyQt 方面的练习：原代码原样保留、能运行的可运行、另有行级批注指出写法与程序组织上的不足。
- **主线章节还没有写**（不留空骨架，ADR 0129）。`content/curriculum.json` 的 `chapters` 为空；唯一的章是 `content/archive.json` 里的「历史归档」章，启动时由共用壳接在课表末尾。写主线时才往 `curriculum.json` 加章，归档章保持最后、不并入主线。
- 归档章的条目写作规范与验收标准见 `comms/legacy-archive/AUTHORING.md`；条目格式以 `programming/design-patterns/content/archive.json` 里的 `dp.arc.observer` 为样板。根检查 `scripts/archive_check.py` 校验案例目录、源文件、批注行号与孤儿目录。
- 归档条目**不判分、不计入进度**：它们是留待使用者人工审视、决定并入主线、保留还是删除的历史材料。删除须显式——提交信息写清删了什么、原仓库路径在哪（旧仓库只会被设为 archived，历史仍在）。

## 技术栈与选型理由

- 壳是 **Tauri 2**（Rust + 系统 WebView），Rust 侧只有 `athena_course_shell::run` 加一份 `ShellConfig`（ADR 0161）；前端是原生 TypeScript + Vite，无框架。最初复制自 `postgraduate/data-structures`，此后独立演进；复制来的实验编辑器等主线用具暂不使用，等写主线时再取舍。
- 归档面板（多文件只读代码视图、批注、运行）来自仓库 `packages/viz` 的 `archive-panel`；读文件与运行用共用壳的 `load_case_files`、`run_archive_case`（案例目录 `content/cases/arc_*`，10 秒超时）。
- 运行分级（`run` 字段）：`cli`（本机编译器）、`toolchain`（需要额外工具链，应用内只读）、`linux-only`、`read-only`。Qt 条目几乎都是 `toolchain`：旧代码是 Qt5，本机装的是 Qt 6.8.1，API 差异写成 `portability` 批注而不改源码；应用内的 Qt 构建运行器尚未实现，不要把它写成已有。

## 开发与验证

```sh
python3 scripts/check.py qt            # 内容 JSON、前端类型检查与构建、Rust 侧检查与测试
python3 programming/qt/scripts/check.py --skip-rust   # 只改了内容或前端时
launcher open qt                       # 从启动器打开
```
