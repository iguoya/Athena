# Athena SymPy 教程精读 — 项目协作规则

本文档是 **`guide/sympy-tutorial` 独立应用** 的项目级指令，不依赖任何其他应用即可完成开发、构建与学习。
仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**学会一个数学工具**。精读 SymPy 官方「入门教程」（`sympy/sympy` 仓库 `doc/src/tutorials/intro-tutorial`，钉 `sympy-1.14.0`）：
  讲解、示例都跟着原教程走；每节配「试一试」，要求在本机 SymPy 里动手算出一个可核对的结果。用符号计算的表现力
  （求导、积分、极限、级数、解方程、矩阵运算）把高等数学与线性代数「算出来、看得见」（主仓库 ADR 0163）。
- **范围**：入门教程九页（准备工作 → 矩阵）；去掉与线代、高数无关的「高级表达式操作」。裁剪清单见 [`docs/COVERAGE.md`](docs/COVERAGE.md)。
  被裁掉的页不进课表、不放占位。页序与原教程一致，**不自编大纲**。
- **出处档位 open**（主仓库 ADR 0089）：教程原文逐字取自上游；原教程没有习题，「试一试」是自编，`source_refs` 里 `relation: authored`，
  不冒充原教程。不凭印象伪造出处。
- **学习方法原型**（主仓库 ADR 0113）：主 **预测–运行**（先预测输出，再在工具里运行对照），辅 **检索强化**。
- 工具安装不在教程里兜底（主仓库 ADR 0057）：假定使用者已装好 Python 与 SymPy。
- 与 `guide/octave-manual`、`guide/selinger-linear-algebra`、`guide/siefken-linear-algebra` **互不引用**。

## 技术栈（本应用自有，最初复制自 `guide/siefken-linear-algebra` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_section` / `get_exercises` / `record_attempt` / `get_attempts`。
- **界面**：Vite + React + TypeScript；公式 KaTeX；代码块是等宽的交互式会话（`>>>` 输入与输出分开着色）；行内 `代码`。
- **内容**：`content/scope.json`（范围，手写）→ `scripts/sync_upstream.py` → `content/sections/*.json`（段落快照）与
  `content/curriculum.json`（生成物，不手改）；`content/exercises/<页>.json` 是手写的「试一试」（题面、答案、做法、复算代码）。
- **进度**：SQLite，`AthenaSympyTutorial/learning.db`，不进 git，由启动器同步（主仓库 ADR 0155）；`attempts` 是事件表（append），
  **「最近一次」按 `answered_at` 认，不按自增 id**。知识点 ID 前缀 `sympy.`（页 id 即上游文件名，作答的 knowledge_id = 页 id）。
- dev 端口 1520；进程 `athena-sympy-tutorial`；环境变量 `ATHENA_SYMPY_TUTORIAL_ROOT`。

## 内容规则

- **原文不手写**：`en` 一律来自 sync。上游一变，跑 sync：指纹相同的段保留译文，原文变了的进 `stale_zh`；**只译 stale 与空的**，
  然后更新 `upstream.json`，一个上游版本一个提交。
- **译文里的公式与行内代码必须与原文一致**（`scripts/check.py` 校验）；只译公式和代码之外的文字。**代码不翻译**（`diff`、`subs`、`Matrix` 原样）。
  代码块（`>>>` 会话）整块逐字保留，不产生可译单元。术语见 [`docs/GLOSSARY.md`](docs/GLOSSARY.md)，并行翻译须知见 [`docs/TRANSLATOR-BRIEF.md`](docs/TRANSLATOR-BRIEF.md)。
- 不用「显然」「容易看出」「不难证明」「易知」「众所周知」等把难度推给读者的词（检查会拦）。
- **示例必须是真的**：`scripts/verify_examples.py` 用真 SymPy 复跑教程里每个 `>>>` 示例并对照输出；对不上的要么上游改了，
  要么本机版本变了，登记在脚本的 `KNOWN_STALE` 并写明原因，不悄悄放宽比较。
- **试一试**写法见 [`docs/EXERCISES-BRIEF.md`](docs/EXERCISES-BRIEF.md)：答案必须由真 SymPy 算出（`verify` 字段里写算它的代码，`check.py` 复跑），
  不能凭心算入库；题面要让学习者先预测、再运行、最后核对。需要写长证明的、答案写法不唯一的，不做核对点。

## 开发与验证

```sh
launcher open sympy-tutorial                  # 日常开发
python3 scripts/check.py                      # 内容结构、译文与原文公式/代码一致、试一试复算、出处契约、构建
python3 scripts/sync_upstream.py              # 从上游重新生成快照（保留已有译文）
<有 sympy 的 python> scripts/verify_examples.py   # 教程示例复跑（需要 sympy，仓库里 postgraduate/mathematics 的引擎环境有）
```

上游克隆：`git clone --depth 1 --branch sympy-1.14.0 --filter=blob:none --sparse https://github.com/sympy/sympy.git upstream/sympy`，
再 `git -C upstream/sympy sparse-checkout set doc/src/tutorials/intro-tutorial`。
