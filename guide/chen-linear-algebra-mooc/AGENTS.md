# Athena 大众线性代数·视频课 — 项目协作规则

本文档是 **`guide/chen-linear-algebra-mooc` 独立应用** 的项目级指令，不依赖任何其他应用即可完成
开发、构建与学习。仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**跟着西电慕课学会线性代数，并在本机 Octave 里做出来**。底本是中国大学 MOOC 西安电子科技大学
  《实用大众线性代数（MATLAB版）》（陈怀琛、杨威、樊松涛主讲，14 周、5 章、约 45 小节，
  <https://www.icourse163.org/course/XIDIAN-1001775006>）。应用形态是 `guide/` 圈的视频课精读（主仓库
  ADR 0180，首个视频课应用），「数学」圈。
- **视频是原材料，不是内容本身**：应用的主角是「看前提示 → 课件精读 → 自答 → Octave 上机 → 练习」这条
  检索闭环；不做无检索闭环的纯被动观看（ADR 0180 决策 1）。
- **播放档位 ①（文本 + 外链）**：应用不内嵌播放器、不下载视频、不绕过任何平台保护；视频在系统浏览器里
  打开课程页，点链接即可。档位 ②（本地文件，暂停点）等使用者说明视频文件形态后另议，内容模型已按时间锚点
  （slide 的 `start`/`end` 秒）组织，加播放源不改内容。
- 与 `guide/chen-linear-algebra`（同一作者的图书精读应用）**并存、互不引用**：内容有重叠（同一套程序集、
  部分例题），但本应用以「周 → 节」为单位，那边以书题为单位；各自入库、各自登记出处，知识点前缀独立。

## 出处与题源（本应用最重的一条规则）

- 出处档位 `open`（ADR 0089），但**题源是应用级硬门禁**（ADR 0180 决策 5，沿 ADR 0177 决策 2）：
  - 每道入库练习必须带 `source_refs`，`relation` 只许 `verbatim`（课件习题/题解/程序集例题原样）或
    `adapted`（以其为底改数字或问法，`note` 写明改动点）。
  - `locator` 必须落在**课件页码**（如「课件 第1章 p.12」）或**程序集号**（如「程序集 pla106」，
    文件须在 `upstream/programs/`）。
  - **`authored`（自编题）不入题库**；`scripts/check.py` 见到直接报错。
  - 不凭印象伪造出处；locator 写不出来就说明题还没核对过，不入库。
- **看前提示 / 自答块**（`prewatch`、`recall`）是教学动作：不判分、不进掌握度，可以是自写文字。
  进掌握度的只有 `exercises/` 里的题，且必须机器可核对（`numbers` 用 Octave 复算，或 `choice`）。
- `lesson.outline_title` 逐字取自课程页大纲；周/节号来自大纲，不自己编。

## 底本与配套资源（`upstream/`）

- `upstream/实用大众线性代数课件.rar`（官方课件，8 个 PPT 共 393 页）与 `程序集.rar`，以及本应用用到的
  程序集 M 文件（拍平放在 `upstream/programs/`，文件头标注例题号）。原站已下线，经 Wayback Machine
  取回，按公域口径入库（主仓库 ADR 0159）；SHA-256 记录在 `upstream.json`，`check.py` 核对完整性。
- 文本主底本是**课件 + 程序集**，不靠字幕；平台字幕/Whisper 转写只是补充，取得与否不阻塞内容。

## 学习方法与界面

- 方法原型（主仓库 ADR 0113）：主**预测–运行**（看前提示、题面先预测输出，再在本机 Octave 里运行对照），
  辅**真做校验**（`verify` 写 Octave 复算代码，`check.py` 在装有 Octave 时复跑）。
- 原书与课程代码是 MATLAB：题面一律以 **Octave 等价写法**呈现，确有差异处（图形、个别函数）在题面加注。
  使用者本机需装 Octave（命令行版即可，工具安装不兜底，主仓库 ADR 0057）。
- 一节 = 课程大纲里的一小节，节 id 形如 `w1s1`（第 1 周第 1 节）。导航是周/节时间轴，不是知识点列表页。
- 不用「显然」「容易看出」「不难证明」等把难度推给读者的词（检查会拦，主仓库 ADR 0013）。
- 内容薄厚分层（主仓库 ADR 0164）：`stage: 2` 的函数卡与图默认折叠进「进阶」。

## 技术栈（本应用自有，最初复制自 `guide/chen-linear-algebra` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_section` / `get_exercises` / `get_figure` /
  `open_external`（只放行 https 外链）/ `record_attempt` / `get_attempts`；界面 Vite + React + TypeScript，
  公式 KaTeX。
- **内容**（全部手写，无生成器）：`content/scope.json`（范围）↔ `content/curriculum.json`（课表，两者须一致）；
  `content/sections/<节id>.json`（课节：`lesson` 元数据 + 块流；块含 `slide` 课件段落、`prewatch`、`recall`）；
  `content/exercises/<节id>.json`（练习）；`content/figures/*.svg`（插图）。
- **进度**：SQLite，`AthenaChenLinearAlgebraMooc/learning.db`，不进 git，由启动器同步（主仓库
  ADR 0037、0155，`app.json` 的 `progress`）。**掌握度只由作答写入，观看不算**（ADR 0052）。
- **知识点前缀 `chenmooc.`**：作答记录的 `knowledge_id` = `chenmooc.` + 节 id（如 `chenmooc.w1s1`）。
- dev 端口 **1531**；进程 `athena-chen-linear-algebra-mooc`；环境变量 `ATHENA_CHEN_LINEAR_ALGEBRA_MOOC_ROOT`。

## 开发与验证

```sh
python3 scripts/check.py               # 结构 + 出处门禁 + Octave 复算 + 底本校验 + 公式自检 + 构建 + cargo check
python3 scripts/check.py --skip-rust   # 跳过 cargo check
launcher open chen-linear-algebra-mooc # 日常开发
```

## 协作（comms 舱 `video-course`）

- 设计讨论与素材任务在 `comms/video-course/`：leader claude-code，worker zcode。zcode 把课件抽成逐页文本
  快照放 `comms/video-course/artifacts/zcode/slides/`，本应用的内容由 leader 据此写入 `content/`。
- worker 不提交 git，不碰本目录下的文件，除非任务书另有明确归属。
