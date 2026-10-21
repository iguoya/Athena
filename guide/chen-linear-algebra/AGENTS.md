# Athena 大众线性代数精读 — 项目协作规则

本文档是 **`guide/chen-linear-algebra` 独立应用** 的项目级指令，不依赖任何其他应用即可完成
开发、构建与学习。仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**用 Octave 做着题学会线性代数**。精读陈怀琛《实用大众线性代数（MATLAB版）》
  （西安电子科技大学出版社 2014，ISBN 978-7-5606-3462-3，约 156 页），它是「用 MATLAB
  改造线性代数教学」路线的大众读本。应用形态是 `guide/` 圈的教材精读（主仓库 ADR 0177；
  形态判据同 ADR 0143、0162、0163），「数学」圈。
- **本书是中文书**：没有翻译管线、没有原文快照同步（不同于 selinger/siefken/octave-manual）。
  章导学自编，重心在**原书题目**。
- 与 `guide/` 其他应用**互不引用**。

## 出处（本应用最重的一条规则）

- 出处档位 `open`（主仓库 ADR 0089：不对着外部考试），但**题源是应用级硬门禁**
  （ADR 0177 决策 2，使用者的硬要求「出题必须有所本，不要凭空制造」）：
  - 每道入库题目必须带 `source_refs`，`relation` 只许 **`verbatim`**（原书例题/习题原样）或
    **`adapted`**（以原书题为底改数字/改问法，`note` 写明改动点）。
  - `locator` 必须给到**页码与题号/例题号**，如「p.23 题 1.3」「第7章官方doc 第16页 例7.14」。
  - **`authored`（自编题）不入题库**——要入须先经使用者认可并修订本规则；`scripts/check.py`
    见到 authored 直接报错。
  - 原书公式在扫描/doc 里不可复制时按原书重排 LaTeX，在 `note` 里注明「公式重排」——内容
    同一，仍是 verbatim。
  - 原书笔误照录（如 7.14 节正文「pla614」实为 pla714），另加注说明，不改原文。
- 不凭印象伪造出处；locator 写不出来就说明题还没核对过，不入库。

## 底本与配套资源（`upstream/`）

- `upstream/` 是**官方配套资源**（作者主页发布，原站已下线，经 Wayback Machine 取回；按
  公域口径入库，主仓库 ADR 0159；SHA-256 记录在 `upstream.json`，`check.py` 核对完整性）：
  - `实用大众线性代数程序集.rar` 与解出的 `programs/*.m`——115 个 M/fig 文件，文件头标注
    例题号（pla201 = 例题 2.01），是**题目代码的权威核对源**，比扫描 OCR 可靠；
  - `第7章-线性代数在工程中的应用实例.doc`——第 7 章全文（目前唯一在手的原书文字）；
  - 课件 rar、封面扉页 doc、教改论文 pdf。
- **书 PDF（纸书扫描）仍缺**：1–6 章的题目采集要等它到位（使用者取得后放 `upstream/`，
  更新 `upstream.json` 的 sha256；或由协作代理按任务书取得）。
- 配套视频是西电官方慕课《实用大众线性代数（MATLAB版）》（陈怀琛、杨威主讲，
  <https://www.icourse163.org/course/XIDIAN-1001775006>），只登记链接不下载入库。

## 学习方法与界面

- 方法原型（主仓库 ADR 0113）：主**预测–运行**（题面先预测输出，再在本机 Octave 里运行
  对照），辅**真做校验**（`verify` 字段写 Octave 复算代码，`check.py` 在装有 Octave 时复跑，
  答案不许凭心算入库）。
- 原书代码是 MATLAB：题面一律以 **Octave 等价写法**呈现（线代核心语法兼容），确有差异处
  （图形、个别函数）在题面加注，不冒充原书原文。使用者本机需装 Octave（命令行版即可，
  工具安装不兜底，主仓库 ADR 0057）。
- 内容薄厚分层（主仓库 ADR 0164）：`stage: 2` 的函数卡与图默认折叠进「进阶」。
- 不用「显然」「容易看出」「不难证明」等把难度推给读者的词（检查会拦，主仓库 ADR 0013）。

## 技术栈（本应用自有，最初复制自 `guide/octave-manual` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_section` / `get_exercises` / `get_figure` /
  `record_attempt` / `get_attempts`；界面 Vite + React + TypeScript，公式 KaTeX。
- **内容**（全部手写，无生成器）：`content/scope.json`（范围：收哪些章）↔
  `content/curriculum.json`（课表，两者须一致）；`content/sections/<章id>.json`（章导学）；
  `content/exercises/<章id>.json`（原书题目）；`content/figures/*.svg`（插图，手工/脚本自备）。
- **进度**：SQLite，`AthenaChenLinearAlgebra/learning.db`，不进 git，由启动器同步（主仓库
  ADR 0155）；`attempts` 事件表 append，「最近一次」按 `answered_at` 认，不按自增 id。
- **知识点前缀 `chen.`**：作答记录的 `knowledge_id` = 章 id（如 `ch7`）。当前章节 id 尚未进
  任何持久数据，将来若改前缀或 id 不受「id 不改嫁」约束——一旦有真实作答数据就受。
- dev 端口 **1528**；进程 `athena-chen-linear-algebra`；环境变量 `ATHENA_CHEN_LINEAR_ALGEBRA_ROOT`。

## 题目写法

- 题 `id` 用原书编号：习题 1.3 → `ex1-3`，例题 1.4 → `exl1-4`（点号留给 chapter.item 分隔，
  正则 `exl?\d+-\d+[a-z]?`）。
- `stem`：中文，可含 `$公式$`、`$$展示公式$$`、`` `代码` ``、``` 围栏代码块```；题面里先给
  原书情境与代码，再要求「先预测，再运行」。
- `check.kind`：`numbers`（必须带 `verify` 或 `verify_note`）或 `choice`（恰好 1 个 `ok`，
  每个选项都有 `why`）。
- `sol`：参考解答，写清预测的依据与 Octave 实跑输出。
- 写完跑 `python3 scripts/lint_exercises.py <章id>` 快查（含真 Octave 复算），完整检查走
  `scripts/check.py`。

## 开发与验证

```sh
launcher open chen-linear-algebra         # 日常开发
python3 scripts/check.py                  # 结构、题目出处门禁、Octave 复算、底本校验、构建
python3 scripts/check.py --skip-rust      # 跳过 cargo check
python3 scripts/lint_exercises.py ch7     # 单章题目快查
```

## 协作（comms 舱 `chen-linear-algebra`）

- leader：zcode；worker：cursor。习题数字化采集（底本 → `content/exercises/`）按章拆给
  worker，任务书写明验收口径；格式以本文「题目写法」与 `content/exercises/ch7.json` 示范为
  准。worker 交 review 必须附：每题 locator 核对记录、`check.py` 输出摘要。
- 底本 PDF 到位后由 leader 更新 `upstream.json` 的 sha256 并广播。
