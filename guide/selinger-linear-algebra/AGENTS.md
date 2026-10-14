# Athena Selinger 线性代数精读 — 项目协作规则

本文档是 **`guide/selinger-linear-algebra` 独立应用** 的项目级指令，不依赖任何其他应用即可完成开发、构建与学习。
仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**吃透一本书**。精读 Peter Selinger《Linear Algebra: A First Course》（CC BY 4.0，Lyryx/Kuttler 教材的开源改编）——
  讲解、例题、习题、书末解答都跟着原书走，不被别的教材干扰；内容与习题并存，读完有练习、有收获（主仓库 ADR 0162）。
- **按考研数学二线代考纲裁剪，但不过分裁剪**：保留体系骨架与「理解必需」的节，去掉远离考纲的专题（抽象向量空间专章、叉积、
  直线平面、有限域、各类应用章等）。裁剪清单与理由在 [`docs/COVERAGE.md`](docs/COVERAGE.md)；被裁掉的节不进课表、不放占位。
  讲解重心不偏离考纲太远，也不被考纲捆住：考纲外但帮助理解的内容可以留。
- 章节顺序与原书一致；节标题保留原书英文名，附中文名。**不自编大纲**。
- **出处档位 open**（主仓库 ADR 0089）：习题逐字取自原书，`relation: verbatim`，locator 给出节与题号；
  我补的「核对点」标 `authored`，不冒充原书答案。不凭印象伪造出处。
- **学习方法原型**（主仓库 ADR 0113）：主 **问题解决**（先自己算，再看原书解法），辅 **检索强化**（节首目标自测、节末回顾）。
- 与 `guide/siefken-linear-algebra`（另一本书）**互不引用**：不共享内容、不互相链接路径，各自钉各自的上游。

## 技术栈（本应用自有，最初复制自 `guide/gtkmm` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust），只读内容与记作答：`get_curriculum` / `get_section` / `get_checks` / `record_attempt` / `get_attempts`。
- **界面**：Vite + React + TypeScript；公式用 KaTeX（`src/macros.ts` 是上游 `LyryxLinAlgStyle.sty` 宏的翻译）。
- **内容**：`content/scope.json`（范围，手写）→ `scripts/sync_upstream.py` → `content/sections/*.json`（段落快照）
  与 `content/curriculum.json`（目录与译文进度，**生成物，不手改**）；`content/checks/*.json` 是手写的核对点。
- **进度**：SQLite，用户数据目录 `AthenaSelingerLinearAlgebra/learning.db`，不进 git，由启动器同步（主仓库 ADR 0155）；
  `attempts` 是事件表（append），**「最近一次」按 `answered_at` 认，不按自增 id**（主仓库 ADR 0160 前后的同类修复）。
  知识点 ID 前缀 `selinger.`（节 id 即上游文件名，作答的 knowledge_id = 节 id）。
- dev 端口 1517；进程 `athena-selinger-linear-algebra`；环境变量 `ATHENA_SELINGER_LINEAR_ALGEBRA_ROOT`。

## 目录与所有权

| 路径 | 职责 |
|---|---|
| `content/scope.json` | 课表范围与中文节名；手写 |
| `content/sections/` | 段落快照：`en` 逐字、`zh` 手写译文；由 sync 生成，**只有 `zh` 与 `title_zh` 是手写内容** |
| `content/checks/` | 习题核对点（最终答案可机器判）；手写 |
| `content/curriculum.json` | 目录与进度；生成物 |
| `upstream/` | 上游克隆（gitignore）；基准在 `upstream.json` |
| `scripts/` | `sync_upstream.py`、`check-math.mjs`、`check.py`、`make-preview.mjs` |
| `src/` `src-tauri/` | 前端与壳 |
| `docs/` | `COVERAGE.md`（考纲覆盖表）、`LICENSE-NOTICE.md`（许可与署名）、`decisions/`（本应用 ADR） |

## 内容规则

- **原文不手写**：`en` 一律来自 sync。上游一变，跑 sync：指纹相同的段保留译文，原文变了的标 `stale`，新增的 `zh` 为空；
  **只译 stale 与空的**，然后更新 `upstream.json` 的 `pinned_commit`，一个上游版本一个提交。
- **译文里的公式必须与原文逐条一致**（`scripts/check.py` 校验：`zh` 里的 `$…$` 集合等于 `en` 里的）；只译公式外的文字。
  专有名词首次出现用「中文（English）」，之后用中文。术语对照参照同济《线性代数》通行译法，不另造。
- 译文要**通俗易懂**但不改数学含义：不省略条件，不把「当且仅当」译成「如果」；原书的例与解必须保留，不压缩。
- 习题核对点：每道题给一个可机器判的最终答案（`numbers` 或 `choice`），答案用 SymPy 复核后入库（`scripts/verify_checks.py`）；
  需要写证明的题只展开原书解答，不做自评，不计入掌握度。
- 图（TikZ）暂不移植，界面显示占位并指向原书；移植时在 `figures/` 另做，不改快照。

## 开发与验证

```sh
launcher open selinger-linear-algebra   # 日常开发
python3 scripts/check.py                # 内容结构、公式、核对点、出处契约、构建
python3 scripts/sync_upstream.py        # 从上游重新生成快照（保留已有译文）
```

浏览器里看样式：`pnpm exec vite build && node scripts/make-preview.mjs`，再起一个静态服务器打开 `dist/preview.html#<节 id>`。
