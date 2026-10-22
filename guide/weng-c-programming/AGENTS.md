# Athena 翁恺 C 语言 · 课堂工作台 — 项目协作规则

本文档是 **`guide/weng-c-programming` 独立应用** 的项目级指令，不依赖任何其他应用即可完成开发、构建与学习。
仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**跟着浙大翁恺的《C语言程序设计》视频课学会 C，并且课堂上就动手**。底本是 B 站 2022 年版 **BV1dr4y1n7vA**（100 集，入门 11 章；
  分集编号 `1.1.1` 起，第 2 集才是 1.1.1，第 3 集是 1.1.2），应用形态是 `guide/` 圈的视频课精读，挂「程序设计」圈（主仓库 ADR 0182，首个带播放窗格的视频课）。
- **视频只是界面的一个窗格，不是全部**：主角是课堂区的「节拍 → 任务 → 要点」；窗格可收起，收起后课堂区自己完整可用。不做无检索闭环的纯被动观看。
- 与 `machine`（C 与机器，Beej 系统视角）、`guide/chen-linear-algebra-mooc` 并存、互不引用，知识点前缀独立。

## 播放窗格与播放桥（ADR 0182 决策 3，改这里要先读）

- 主窗口由 Rust 创建（`src-tauri/src/lib.rs` 的 `setup`），一个窗口两个 webview：`ui`（应用界面，左）与 `player`（B 站外链播放器页面，右，可收起）。
  停靠用 Tauri 多 webview，**需要 `unstable` 特性**；升级 Tauri 时回归。退路：把 `add_child` 换成独立窗口，课堂区不受影响。
- 播放器页面只被放行**一个命令** `bridge_report`（`capabilities/player.json`，`remote.urls` 只含 `https://player.bilibili.com/*`；命令在 `build.rs` 的应用清单里声明）。
  注入脚本 `src-tauri/src/player_bridge.js` 只读时间/状态、执行 seek/pause/play、判定暂停点，**不下载、不抓取、不改页面内容，只用标准 `<video>`，不依赖 B 站私有 API**。
- 暂停点按「自然播放跨过」判定，拖动越过按已过处理；页面偶发自己暂停（原因未明）是正常状态，界面显示「已暂停，点这里继续」；播放窗格要保持可见，隐藏时暂停点精度不保证。
- **登录与清晰度由使用者处理**：「登录 B 站」按钮把右侧播放窗格导航到 B 站**官方**登录页（页面不在 capability 放行的域名里，调不了任何应用命令），使用者在窗格里扫码或输入账号，点「登录完成，回到视频」再载入播放器；登录状态存在本应用 webview 数据目录，应用不读取、不保存账号与密码。ADR 0182 决策 4 原写「独立窗口」，实测在同步命令里新建 webview 窗口会得到永远空白的窗口（about:blank），故改为窗格内导航。
- 视频引用只来自课堂脚本的 `video.{bvid,p}`，Rust 侧逐项校验后才拼 URL（`player_url`），不接受任意地址。

## 任务与出处（本应用最重的一条规则）

- 方法原型（主仓库 ADR 0113）：主**预测–运行**，辅**真做校验**。任务类型：`predict`（含追踪执行，机器可判的选择/数值，记「命中」但不进复习队列）、
  `quick`（速答，进掌握度）、`doit`（你来做：骨架代码在本机编译运行，贴回输出比对，进掌握度）、`selfexplain`（教学动作，不判分）。
- **进掌握度的只有 `quick`/`doit`**，且必须机器可核对（选择、数值、输出比对）。**掌握度只由作答写入，观看不算**（ADR 0052）。
- 每道 `quick`/`doit` 必须带 `source_refs`：`relation` 只许 `verbatim`/`adapted`（`adapted` 写明改动点），**`authored` 不入库**；
  `locator` 写「P3 05:12」（分集号 + 视频里的时间），**时间必须落在转写里讲师讲到该内容的位置附近**，不得凭印象写。`scripts/check.py` 校验。
- 题目内容只取自**本课程视频里讲到的内容**；视频没讲的不出，别拿自己的 C 语言知识当讲课内容。
- 数量门槛（`check.py` 校验）：一节 3–6 个节拍；一节总任务 ≤10；重任务（`doit`）≤2；每节拍暂停任务 ≤2；暂停点选在推导完成处，不选在推导中间。
- `doit` 的骨架代码不改一行也能编译运行（ADR 0059），`check.py` 用本机 C 编译器编译运行并核对 `expected`（ADR 0057：假定有 C 编译器）。

## 内容（`content/`，全部手写）

- `curriculum.json`：课表（章 → 课节）；`lessons/<课节 id>.json`：课堂脚本，课节 id 形如 `p003`（第 3 集）。
- 课堂脚本字段见 `src/types.ts` 的 `Lesson`：`video`（含 `kind:"bilibili"`，播放器适配器的引用）、`opening`（目标 + 预测）、`beats[]`（`id/title/concept/start/end/tasks/takeaway`）、
  `closing`（出口题 + 要点改写提示）、`transcript`（参考层）。`concept` 是知识点短名，复习卡、交错练习、「待巩固」都按它聚合。
- **时间戳**：节拍起止与暂停点 `at` 取自转写段时间（±1 秒），可用界面里的「边看边标」校正；校正结果存在本机，确认后再写进内容文件。没标的任务由使用者在节拍里手动打开。
- **转写**：本机 faster-whisper 出的参考层，标「机器转写，未逐句校对」；已按校正表全文替换 4 条同音错词。转写不是出处、不是教学正文，只供检索与对照；音频不入库。
- 不用「显然」「容易看出」「不难证明」等把难度推给读者的词（`check.py` 拦，主仓库 ADR 0013）。

## 技术栈（本应用自有，最初复制自 `guide/chen-linear-algebra-mooc` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_lesson` / `record_attempt` / `get_attempts` / `open_external`（只放行 https）/ `player_*`（load、seek、ping、poll、play、pause、set_pause_point、set_visible）/
  `bridge_report`（播放器页面专用）/ `player_open_login` / `save_marks` / `load_marks`；界面 Vite + React + TypeScript，行内公式 KaTeX。
- **进度**：SQLite，`AthenaWengCProgramming/learning.db`，不进 git，由启动器同步（主仓库 ADR 0037、0155，`app.json` 的 `progress`）。「边看边标」记录存在同目录 `marks/`。
- **知识点前缀 `wengc.`**：作答记录的 `knowledge_id` = `wengc.` + 课节 id（如 `wengc.p003`），`item_id` = `<课节 id>.<任务 id>`。
- dev 端口 **1532**；进程 `athena-weng-c-programming`；环境变量 `ATHENA_WENG_C_PROGRAMMING_ROOT`。

## 开发与验证

```sh
python3 scripts/check.py               # 课表/脚本结构、数量门槛、出处门禁、骨架编译运行、公式自检、前端构建、cargo check/test
python3 scripts/check.py --skip-rust   # 跳过 cargo
launcher open weng-c-programming       # 日常开发
```

## 协作（comms 舱 `video-course`）

- 设计与素材任务在 `comms/video-course/`：leader claude-code，worker zcode（转写、节拍与任务草案放 `artifacts/zcode/`，由 leader 抽查后写入 `content/`）。
- worker 不提交 git，不碰本目录，除非任务书另有明确归属。
