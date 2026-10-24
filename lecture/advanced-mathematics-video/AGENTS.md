# Athena 高等数学（工本）·视频课 — 项目协作规则

本文档是 **`lecture/advanced-mathematics-video` 独立应用** 的项目级指令，不依赖任何其他应用即可完成开发、构建与学习。
仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**跟着一套视频课学会高等数学（工本），并且课堂上就动手**。对应真实考试：高等教育自学考试「高等数学（工本）」00023（教材：陈兆斗、马鹏，北京大学出版社 2023 年版，六章）。
  应用形态是 `lecture/` 圈的视频课（主仓库 ADR 0184、0185），挂「自考」圈。
- **底本**：B 站 BV1UU4y1t7ix（UP「一点小感动」转载的腾讯课堂录播，72 集）。**只做 P40–P58 的正课**；P1–P39 的初等数学与一元微积分补课教材不含，以后若做作 `prereq` 层。
- 这套是直播录播，**分集标题与内容并不一一对应**（P53 标「曲面积分」实为第五章开头，P55 标「二阶微分方程」实为第五章真题讲解），课节划分以字幕内容为准（ADR 0185 勘误）。
- **视频只是界面的一个窗格，不是全部**：主角是课堂区的「节拍 → 任务 → 要点」；窗格可收起，收起后课堂区自己完整可用。不做无检索闭环的纯被动观看。
- 与同科目的文本应用 `self-study/advanced-mathematics`（同科目文本应用，按教材节讲课、刷题） **并存、互不引用**（主仓库 ADR 0062），知识点前缀独立。
- 视频的版权归原作者与平台；本应用自用学习，**不含、不下载、不转存任何视频**（原课为腾讯课堂录播（转载稿，UP 声明「请勿转载录播」）），出处照记（主仓库 ADR 0159）。

## 播放窗格与播放桥（沿 ADR 0182 决策 3、ADR 0183；改这里要先读）

- 主窗口由 Rust 创建（`src-tauri/src/lib.rs` 的 `setup`），一个窗口两个 webview：`ui`（应用界面，左）与 `player`（B 站视频页，右，可收起）。
  停靠用 Tauri 多 webview，**需要 `unstable` 特性**；升级 Tauri 时回归。退路：把 `add_child` 换成独立窗口，课堂区不受影响。
- 播放器页面只被放行**一个命令** `bridge_report`（`capabilities/player.json`，`remote.urls` 为 `https://www.bilibili.com/*`——IPC 请求只带来源、带路径的模式匹配不上；命令在 `build.rs` 的应用清单里声明）。
  注入脚本 `src-tauri/src/player_bridge.js` 只读时间/状态、执行 seek/pause/play、判定暂停点，**不下载、不抓取、不改页面内容，只用标准 `<video>`，不依赖 B 站私有 API**。
- 暂停点按「自然播放跨过」判定，拖动越过按已过处理；页面偶发自己暂停是正常状态，界面显示「已暂停，点这里继续」；播放窗格要保持可见，隐藏时暂停点精度不保证。
- **登录与清晰度由使用者处理**：「登录 B 站」把右侧播放窗格导航到 B 站**官方**登录页（页面不在 capability 放行的域名里，调不了任何应用命令），使用者在窗格里登录，点「登录完成，回到视频」再载入播放器；登录状态存在本应用 webview 数据目录，应用不读取、不保存账号与密码。
- 视频引用只来自课堂脚本的 `video.{bvid,p}`，Rust 侧逐项校验后才拼视频页 URL（`player_url`），不接受任意地址。
- 播放桥这份代码是**从 `lecture/weng-c-programming` 复制来的**，此后独立演进（ADR 0185 决策 8；等三份拷贝稳定、差异清楚再抽到 `packages/`，ADR 0132）。

## 任务与出处（本应用最重的一条规则）

- 方法原型（主仓库 ADR 0113）：主**问题解决**，辅**检索强化**。核心动作：**暂停点放在讲师开始解题之前，让使用者先动笔，再看讲师的解法**。任务类型：
  `workout`（先自己算：暂停点上给题，纸上算完把答案填回，机器核对，进掌握度）、`quick`（速答：概念辨析、判定，选择或数值，进掌握度）、
  `predict`（预测讲师接下来的结果，机器可判的记「命中」，不进复习队列）、`selfexplain`（教学动作，不判分）。
- **进掌握度的只有 `quick`/`workout`**，且必须机器可核对（选择、数值）。**掌握度只由作答写入，观看不算**（ADR 0052）。
- 每道 `quick`/`workout` 必须带 `source_refs`：`relation` 只许 `verbatim`/`adapted`（`adapted` 写明改动点，如「原题求表达式，这里改成求某点的值便于机器核对」），**`authored` 不入库**；
  `locator` 写「P6 05:12」（分集号 + 视频里的时间），**时间必须落在字幕里讲师讲到该内容的位置附近，且在本课节区间内**，不得凭印象写。`scripts/check.py` 校验。
- 题目内容只取自**本课程视频里讲到的例题与习题**（含讲师讲解的真题）；视频没讲的不出，别拿自己的数学知识当讲课内容。
- **题干以画面为准**：字幕只用于定位。字幕里公式靠念白，负号、指数、下标常丢（例如把 −2 听成 2）；每道进掌握度的题，题干都要到视频画面上核对（跳到 locator 时间截图），不得照字幕转抄。
- **数值题必须带 `verify`**：一小段 Python/sympy 代码，把答案算出来放进变量 `result`；`scripts/check.py` 执行它并要求与 `check.answer` 一致（ADR 0185 决策 5）。选择题的 `verify` 可选，结果是正确选项的下标。
- 数量门槛（`check.py` 校验）：一节 3–6 个节拍；一节总任务 ≤10；重任务（`workout`）≤2；每节拍暂停任务 ≤2；暂停点选在推导完成处，不选在推导中间。

## 内容（`content/`，全部手写）

- `curriculum.json`：课表（章 → 课节）；`lessons/<课节 id>.json`：课堂脚本，课节 id 形如 `p006`（第 6 集整集）或 `p055a`（第 55 集的第 a 段）。
- **课节 = 一集里的一段**：`video.{start,end}` 是区间（秒），一般 10–25 分钟；整集作课节时可省略。
- 课堂脚本字段见 `src/types.ts` 的 `Lesson`：`video`、`opening`（目标 + 预测）、`beats[]`（`id/title/concept/start/end/tasks/takeaway`）、`closing`（出口题 + 要点改写提示）、`transcript`（参考层）。
- **文本底本（参考层）**：优先用 B 站平台字幕（使用者在应用窗格里登录后，`x/player/wbi/v2` 给出 `subtitle_url`），标「平台 AI 字幕，未逐句校对」；没有字幕的集才用本机转写，标「机器转写，未逐句校对」。
  它们不是出处、不是教学正文，只供检索与对照；音频不入库。
- 不用「显然」「容易看出」「不难证明」等把难度推给读者的词（`check.py` 拦，主仓库 ADR 0013）。
- 文字排版：界面的 `Inline` 认 `$公式$`、`**加粗**`、`*斜体*`、`` `代码` ``，题面与参考用空行分段；不支持表格与标题。公式里的行分隔符在 JSON 里要写成 `\\\\`，用脚本生成内容时用 `chr(92)` 或原始字符串，别用 shell 内联。

## 技术栈（本应用自有，最初复制自 `lecture/weng-c-programming` 的壳，此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_lesson` / `record_attempt` / `get_attempts` / `open_external`（只放行 https）/ `player_*`（load、seek、ping、poll、play、pause、set_pause_point、set_visible）/
  `bridge_report`（播放器页面专用）/ `player_open_login` / `save_marks` / `load_marks`；界面 Vite + React + TypeScript，行内公式 KaTeX。
- **进度**：SQLite，`AthenaAdvancedMathematicsVideo/learning.db`，不进 git，由启动器同步（主仓库 ADR 0037、0155，`app.json` 的 `progress`）。「边看边标」记录存在同目录 `marks/`。
- **知识点前缀 `advvideo.`**：作答记录的 `knowledge_id` = `advvideo.` + 课节 id（如 `advvideo.p006`），`item_id` = `<课节 id>.<任务 id>`。
- dev 端口 **1533**；进程 `athena-advanced-mathematics-video`；环境变量 `ATHENA_ADVANCED_MATHEMATICS_VIDEO_ROOT`。

## 开发与验证

```sh
python3 scripts/check.py               # 课表/脚本结构、数量门槛、出处门禁、sympy 复算、公式自检、前端构建、cargo check/test
python3 scripts/check.py --skip-rust   # 跳过 cargo
launcher open advanced-mathematics-video   # 日常开发
```

## 协作（comms 舱 `video-course`）

- 设计与素材任务在 `comms/video-course/`：leader claude-code，worker zcode（字幕整理、节拍与任务草案放 `artifacts/zcode/`，由 leader 抽查后写入 `content/`）。
- worker 不提交 git，不碰本目录，除非任务书另有明确归属。
- 字幕存档在 `comms/video-course/artifacts/claude-code/subs-math/`。
