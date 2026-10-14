# Athena Octave 手册精读 — 项目协作规则

本文档是 **`guide/octave-manual` 独立应用** 的项目级指令，不依赖任何其他应用即可完成开发、构建与学习。
仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**学会一个数学工具**。精读 GNU Octave 官方手册（`gnu-octave/octave` 仓库 `doc/interpreter`，钉 `release-8-4-0`），
  **按「用 Octave 学线代与高数」裁剪**（主仓库 ADR 0163）：每页取手册某章的若干节，只收列出的函数说明。手册是参考手册、不是教程，
  所以每页配「试一试」：要求在本机 Octave 里动手算出一个可核对的结果，把矩阵、特征值、积分、微分方程「算出来、画出来」。
- **范围与厚度**：十二页（数值类型与矩阵 → 方程求根与最优化），清单与理由见 [`docs/COVERAGE.md`](docs/COVERAGE.md)。**内容分基础与进阶两档**（使用者的要求：前期简明扼要、有成果有成就感，后期再加知识量与复杂度）：`scope.json` 里 `functions` 是基础、`functions_more` 是进阶，界面默认只显示基础，进阶译文与练习照常入库、一键展开。新增内容先进「进阶」，要升到基础需要有理由。被裁掉的节与函数不进课表、不放占位。
  页内顺序与手册一致，页序是学习顺序；**不自编大纲**。
- **出处档位 open**（主仓库 ADR 0089）：手册原文逐段取自上游；手册没有习题，「试一试」是自编，`source_refs` 里 `relation: authored`，
  不冒充手册内容。不凭印象伪造出处。
- **学习方法原型**（主仓库 ADR 0113）：主 **预测–运行**（先预测输出，再在工具里运行对照），辅 **检索强化**。
- 工具安装不在教程里兜底（主仓库 ADR 0057）：假定使用者已装好 Octave（命令行版即可）。
- 与 `guide/sympy-tutorial`、`guide/selinger-linear-algebra`、`guide/siefken-linear-algebra` **互不引用**。

## 技术栈（本应用自有，最初复制自 `guide/sympy-tutorial` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_section` / `get_exercises` / `record_attempt` / `get_attempts`。
- **界面**：Vite + React + TypeScript；公式 KaTeX；函数说明是「签名 + 说明」卡片（`def` 块），例子是等宽代码块（`code` 块），
  选项说明是定义列表（`dl` 块）。
- **内容**：`content/scope.json`（范围，手写：页、取的节、收的函数）→ `scripts/sync_upstream.py` → `content/sections/*.json`
  （段落快照）与 `content/curriculum.json`（生成物，不手改）；`content/exercises/<页>.json` 是手写的「试一试」。
- **函数说明来自本机 Octave**：手册里 `@DOCSTRING(名字)` 的正文在源码注释里，同步时用本机**同版本**（8.4.0）Octave 的
  `get_help_text` 展开，缓存在 `upstream/docstrings.json`（gitignore）。所以**同步**需要装有 Octave 8.4；使用与日常检查不需要。
- **进度**：SQLite，`AthenaOctaveManual/learning.db`，不进 git，由启动器同步（主仓库 ADR 0155）；`attempts` 是事件表（append），
  **「最近一次」按 `answered_at` 认，不按自增 id**。知识点 ID 前缀 `octave.`（页 id 即上游文件名，作答的 knowledge_id = 页 id）。
- dev 端口 1519；进程 `athena-octave-manual`；环境变量 `ATHENA_OCTAVE_MANUAL_ROOT`。

## 内容规则

- **原文不手写**：`en` 一律来自 sync。上游一变，跑 sync：指纹相同的段保留译文，原文变了的进 `stale_zh`；**只译 stale 与空的**。
- **译文里的公式与行内代码必须与原文一致**（`scripts/check.py` 校验）；只译公式和代码之外的文字。**代码不翻译**（函数名、选项字符串、
  变量名原样）。函数签名与 `@example` 块整块逐字保留，不产生可译单元。术语见 [`docs/GLOSSARY.md`](docs/GLOSSARY.md)，
  并行翻译须知见 [`docs/TRANSLATOR-BRIEF.md`](docs/TRANSLATOR-BRIEF.md)。
- 不用「显然」「容易看出」「不难证明」「易知」「众所周知」等把难度推给读者的词（检查会拦）。
- 手册文字里偶有对被裁掉章节的交叉引用（如 "See also: `eigs`"）：照译，不补内容。
- **试一试**写法见 [`docs/EXERCISES-BRIEF.md`](docs/EXERCISES-BRIEF.md)：答案必须由真 Octave 算出（`verify` 字段里写算它的 Octave 代码，
  `check.py` 在装有 Octave 时复跑），不能凭心算入库；题面让学习者先预测、再运行、最后核对。

## 开发与验证

```sh
launcher open octave-manual               # 日常开发
python3 scripts/check.py                  # 内容结构、译文与原文公式/代码一致、试一试复算（有 Octave 时）、出处契约、构建
python3 scripts/sync_upstream.py          # 从上游重新生成快照（保留已有译文；需要 Octave 8.4）
```

上游克隆：`git clone --depth 1 --branch release-8-4-0 --filter=blob:none --sparse https://github.com/gnu-octave/octave.git upstream/octave`，
再 `git -C upstream/octave sparse-checkout set doc/interpreter`。
