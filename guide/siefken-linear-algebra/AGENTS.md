# Athena Siefken 线性代数精读 — 项目协作规则

本文档是 **`guide/siefken-linear-algebra` 独立应用** 的项目级指令，不依赖任何其他应用即可完成开发、构建与学习。
仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**吃透一本书**。精读 Jason Siefken《MAT223 Workbook: Linear Algebra》（多伦多大学一学期线代课程的开源教材，CC BY-SA 4.0，
  GitHub 项目名 IBLLinearAlgebra）。几何直观先行、概念导向：每个模块先讲思想，再给练习题（带解答）。内容与习题并存，
  读完有练习、有收获（主仓库 ADR 0162）。
- **范围**：模块 1–16 与附录 1–4（原书只有 284 页，其中很大一部分是留给学生写答案的空白与课堂探究题）。本应用**只收每个模块的讲解
  与练习题**，不收课堂用的核心探究题、教师批注与幻灯片（它们没有标准答案，且依赖课堂组织）。覆盖了哪些考纲点、哪些没讲，
  见 [`docs/COVERAGE.md`](docs/COVERAGE.md)。原书没讲的考纲点（二次型、施密特正交化、实对称矩阵的正交对角化、克拉默法则等）
  不在这里补别的教材的内容。
- 模块与附录的顺序、编号以原书为准；**不自编大纲**。
- **出处档位 open**（主仓库 ADR 0089）：练习题逐字取自原书，`relation: verbatim`；我补的「核对点」标 `authored`，不冒充原书答案。
- **学习方法原型**（主仓库 ADR 0113）：主 **问题解决**（先自己想，再看原书解法），辅 **检索强化**。
- 与 `guide/selinger-linear-algebra`（另一本书）**互不引用**：不共享内容、不互相链接路径，各自钉各自的上游。

## 技术栈（本应用自有，最初复制自 `guide/selinger-linear-algebra` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_section` / `get_checks` / `get_figure` / `record_attempt` / `get_attempts`。
- **界面**：Vite + React + TypeScript；公式 KaTeX（`src/macros.ts` 翻译上游 `common/preamble.tex` 的宏）；
  TikZ/pgfplots 图预先编译成 SVG 入库（`scripts/render_figures.py`，开发期需要本机 TeX，使用者不需要）。
- **内容**：`content/scope.json`（范围，手写）→ `scripts/sync_upstream.py` → `content/sections/*.json`（段落快照）、
  `content/curriculum.json`（生成物，不手改）、`content/figures/`；`content/checks/*.json` 是手写核对点。
- **进度**：SQLite，`AthenaSiefkenLinearAlgebra/learning.db`，不进 git，由启动器同步（主仓库 ADR 0155）；`attempts` 是事件表（append），
  **「最近一次」按 `answered_at` 认，不按自增 id**。知识点 ID 前缀 `siefken.`（页 id 即上游文件名，作答的 knowledge_id = 页 id）。
- dev 端口 1518；进程 `athena-siefken-linear-algebra`；环境变量 `ATHENA_SIEFKEN_LINEAR_ALGEBRA_ROOT`。

## 内容规则

- **原文不手写**：`en` 一律来自 sync。上游一变，跑 sync：指纹相同的段保留译文，原文变了的进 `stale_zh`；**只译 stale 与空的**，
  然后更新 `upstream.json` 的 `pinned_commit`，一个上游版本一个提交。
- **译文里的公式必须与原文逐条一致**（`scripts/check.py` 校验）；只译公式外的文字。术语见 [`docs/GLOSSARY.md`](docs/GLOSSARY.md)，
  并行翻译的须知见 [`docs/TRANSLATOR-BRIEF.md`](docs/TRANSLATOR-BRIEF.md)。
- 不用「显然」「容易看出」「不难证明」「易知」「众所周知」等把难度推给读者的词（检查会拦）。
- 本书是工作册：习题是「练习题」，原书给了解答；核对点（`content/checks/`）每题一个可机器判的最终答案（`numbers` 或 `choice`），
  用 SymPy 复核后入库；需要写证明的题只展开原书解答，不做自评，不计入进度。
- 图：TikZ/pgfplots 由 sync 抽出源码到 `content/figures/src/`，`render_figures.py` 编译成 SVG；不手改 svg。

## 开发与验证

```sh
launcher open siefken-linear-algebra     # 日常开发
python3 scripts/check.py                 # 内容结构、公式、核对点、出处契约、构建
python3 scripts/sync_upstream.py         # 从上游重新生成快照（保留已有译文）
```
