# ADR 0185：新增 `lecture/advanced-mathematics-video` 与 `lecture/linear-algebra-video`——自考高数（工本）、线代（工）视频课

- 日期：2026-10-24
- 状态：已接受（使用者指示：「按推荐：高数用 BV1UU4y1t7ix（只做 P40 起的正课，补课部分以后作 prereq），线代用 BV1d7wAzsE8V。题源按设计草案第 8 节第 3 点执行」）
- 关系：沿 [ADR 0182](0182-weng-c-programming.md)（课堂工作台）、[ADR 0183](0183-weng-player-uses-video-page.md)（播放窗格载视频页）、
  [ADR 0184](0184-lecture-directory-for-video-courses.md)（`lecture/` 目录）；对应真实考试，出处精神沿 [ADR 0175](0175-self-study-math-exam-apps.md)；
  方法原型 [ADR 0113](0113-method-archetypes-per-course.md)；掌握度只由作答写入 [ADR 0052](0052-incentives-and-records-cooperate.md)；
  播放桥先复制 [ADR 0132](0132-defer-shared-layer.md)；宁缺毋滥 [ADR 0129](0129-prefer-quality-over-quantity.md)；公域口径 [ADR 0159](0159-jiuzhou-academic-layer-in-repo.md)
- 设计过程与视频核对：`comms/video-course/artifacts/claude-code/DESIGN-selfstudy-lectures.md`、`CANDIDATES-VERIFIED.md`；候选调研在 `artifacts/zcode/candidates/`

## 背景

`self-study/` 里已有两个自考文本应用（线代 24 节、高数 28 节），按教材节讲课、刷题。使用者要再做两个**视频课**应用，用翁恺应用的课堂工作台形态：
视频是界面的一个窗格，节拍 + 任务驱动。候选视频由 zcode 调研、claude-code 打开视频页核对：

- 高数（工本）00023：B 站「一点小感动」转载的腾讯课堂录播，72 集 69.5 小时。P1–P39 是初等数学与一元微积分补课（教材不含），P40 起才是对应教材六章的正课（P40 二三阶行列式、P41–43 空间解析几何、
  P44–46 多元微分、P47–50 重积分、P51–53 曲线曲面积分、P54–55 微分方程、P56–59 级数），P60–P72 是考点串讲与 2015–2019 年真题解析。正课单集约 2 小时。
- 线代（工）：宋浩老师官方号 3.0 版 BV1d7wAzsE8V，39 集 29.6 小时，章节与申亚男教材几乎一一对应（教材外的是第 7 章向量空间的概念、基维数坐标 P37–P39）。
  页面标记字幕**需登录**才能取。

## 决策

1. **新增两个学习应用**，放 `lecture/`（ADR 0184）：
   | | `advanced-mathematics-video` | `linear-algebra-video` |
   |---|---|---|
   | 界面名 | 高等数学（工本）·视频课 | 线性代数（工）·视频课 |
   | `group` | 自考 | 自考 |
   | 进程 / 数据目录 | `athena-advanced-mathematics-video` / `AthenaAdvancedMathematicsVideo` | `athena-linear-algebra-video` / `AthenaLinearAlgebraVideo` |
   | 知识点前缀 | `advvideo.` | `lavideo.` |
   | dev 端口 | 1533 | 1534 |
   | 环境变量 | `ATHENA_ADVANCED_MATHEMATICS_VIDEO_ROOT` | `ATHENA_LINEAR_ALGEBRA_VIDEO_ROOT` |
   id 用完整英文单词；`-video` 区别于 `self-study/` 下同科目的文本应用。两者与文本应用**并存、互不引用**（ADR 0062），知识点前缀独立。
2. **底本范围**：
   - 高数：BV1UU4y1t7ix **P40–P58 的正课**。P1–P39 补课不做，以后若做作 `prereq` 层，不进考纲章；P59–P72 的考点串讲与真题解析在正课稳定后再议。
   - 线代：BV1d7wAzsE8V **P1–P36**，对照申亚男教材六章；P37–P39（教材外）不做；教材 §3.5 标准正交基对应的 P32（内积与正交矩阵）并入第 3 章。
3. **课节 = 一集里的一段**：`video.{bvid,p,start,end}`，一般 10–25 分钟，一集可拆几个课节，id 形如 `p055a`。数量门槛沿翁恺：一节 3–6 个节拍、总任务 ≤10、重任务 ≤2、每拍暂停任务 ≤2。
4. **方法原型：主问题解决，辅检索强化**（ADR 0113）。暂停点放在讲师**开始解例题之前**，让使用者先动笔，再继续看讲师的解法对照。任务类型：
   - `workout`（先自己算）：暂停点上给题，纸上算完把答案填回（选择 / 数值），机器核对，进掌握度；
   - `quick`（速答）：概念辨析、判定，选择或数值，进掌握度；
   - `predict`：预测讲师接下来的结果，机器可判的记「命中」，不进复习队列；
   - `selfexplain`：教学动作，不判分。
   进掌握度的只有 `workout` 与 `quick`。
5. **机器核对用 sympy**：数值题带 `verify`（一小段 Python/sympy），`check.py` 复算并要求与 `expected` 一致，算不出来的题不入库（对应翁恺的 C 编译器、西电慕课的 Octave，ADR 0057 基线）。
6. **题源与出处**（设计草案 §8 第 3 点）：进掌握度的题只取自**视频里讲到的例题与习题**，以及**复制进本应用自己素材目录**的历年真题整卷（线代已有 2018 年 4 月整卷，高数的真题整卷待采集）；
   `relation` 只许 `verbatim`/`adapted`，**`authored` 不入库**；`locator` 写「P6 05:12」，时间必须落在讲师讲到该题的位置，用字幕或转写核对，不凭印象。结果是每节题量会比文本应用少，这是有意的取舍。
7. **文本底本**：优先平台字幕（需使用者在应用的播放窗格里登录 B 站后取，应用不读账号密码）；没有字幕的集用本机 faster-whisper 转写（音频只在本机临时使用、不入库，转写标「机器转写，未逐句校对」）。
   **数学课的转写只用于定位**——切课节、定节拍时间、核对 locator 的大致位置；**题干与解答以画面为准，人工摘录并用 sympy 复算，不得把转写当题干**（讲师念「x 平方加 y 平方」，公式细节在板书）。
8. **壳与播放桥**：最初复制自 `lecture/weng-c-programming`，此后独立演进；Tauri `unstable` 多 webview、播放桥只放行 `bridge_report`、`player_url` 逐项校验 `video` 字段等安全约束全部沿用（ADR 0182 决策 3、0183）。
   播放桥现在有第 2、3 份拷贝，仍不抽共用件（ADR 0132 的判断：等三份拷贝都稳定、差异清楚再抽到 `packages/`）。
9. **第一批可交付内容**：每个应用先落**一个试点课节**，跑通播放桥、暂停点、作答与复习闭环，再按章推进（ADR 0129）。试点：高数 P55「二阶微分方程」（30 分钟），线代 P6「1.6 克拉默法则」（22 分钟）。
   在试点课节写出来之前不提交空应用目录。
10. **出处档位 `exam`**（对应真实考试，ADR 0175）：`content-contract.json` 声明阻断；内容文件、`app.json` 的 `progress`（进度库 `learning.db`，不进 git，由启动器同步，ADR 0037、0155）与翁恺应用同形。

## 后果

- 新增两个应用；登记 `docs/REPOSITORY.md` 结构树与名字表、根 `README.md`、根 `AGENTS.md` 结构树、`docs/LEARNING-METHODS.md` 画像、`ci.yml`。
- 转写与节拍草案由 zcode 出（comms 舱 `video-course`），claude-code 抽查入库；字幕需要使用者登录一次，这是一个人工环节。
- 高数那套是 2021 年前后按旧教材录的转载稿（UP 声明「请勿转载录播」，原课在腾讯课堂）；按 ADR 0159 公域口径直接使用，出处照记，视频不下载入库。
- 风险：B 站页面改版会使播放桥失效（沿 ADR 0182，退回档位 ① 文本 + 外链）；高数转载稿分集过长，节拍时间要自己打；转载稿随时可能下架，课表里只登记链接。
