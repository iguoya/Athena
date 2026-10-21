# 线性代数（自考）— 项目协作规则

本文档是 **`self-study/linear-algebra` 独立应用**的项目级指令，不依赖任何其他应用即可完成
开发、构建与学习全流程。仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- **学习应用，对应真实外部考试**：高等教育自学考试本科「线性代数（工）」，课程代码
  13175 / 02198（2024 年起考试计划课改过渡中，**新旧代码并记**，报考以所在省考试院当年
  安排为准；应用不断言某省用哪个代码）。出处档位 **`exam`**（仓库级 ADR 0175；判分内容
  必须有真实出处，检查阻断）。
- **对准官方指定教材**：申亚男、卢刚主编《线性代数（工）》（附自学考试大纲），北京大学
  出版社 2023 年版。章节结构跟随教材目录与考纲；**节级划分在逐章编写时与教材实物核对**，
  与二手资料出入时以版权页目录为准，就地修正并在提交信息里说明。
- **自编教案，不是教材精读**：教材是版权出版物，不逐字复制原文；讲解全部自编，
  `textbook_ref` 与 `syllabus_ref` 必填（每个知识点），界面上显示、可反查。
- **方法原型**（ADR 0113）：主**问题解决**（先自己动笔算，再看分步解答——例题折叠、
  练习先答后看），辅**检索强化**（节首提取题、跨知识点混合练习）。
- 起点假设：会初等代数与基本的函数概念。更高的前置写进知识点 `requires`。

## 出处规则（exam 档）

1. 判分内容（`exercise`、`retrieval` 块）必带 `source_refs`，`relation` 三选一：
   - `verbatim`：历年真题原文。`locator` 写「全国 YYYY 年 M 卷 第 N 题」；整卷原文入
     `content/exams/YYYY-MM.json`（格式见该目录 README）。
   - `adapted`：真题或教材例题的改编。`locator` 指向原题，`note` 写明改了什么。
   - `authored`：自造。`note` 写明理由。
2. **不凭印象伪造出处**：没有核实过的真题不标 `verbatim`；教材例题没有教材实物在手
   不标 `adapted` 挂教材。
3. **过渡期规则**：历年真题整卷采集入库前，允许 `authored` 计算题与辨析题如实标注
   上线；真题整卷入库后**逐批把 `authored` 替换为 `verbatim`/`adapted`，`authored`
   数量只许降不许升**。替换完成前不设 authored 配额门禁；真题目录建成后收紧为
   「一节内 authored 不过半」。
4. 例题（`example` 块）不判分，不受门禁，但引用了外部题目时同样要标出处，不冒充。

## 内容格式

- **课表** `content/curriculum.json`：课程信息（教材坐标、代码并记、方法原型）+ 章。
  节的明细只登记**已写出内容**的节，课表随内容生长；不放空占位。
- **知识点** `content/knowledge.json`：只给已写出内容的知识点评级（难度 1–5 与掌握目标
  两维，ADR 0029）；类型三选一（概念/技能/策略）；先修写 `requires`（ADR 0030）；
  ID 前缀 `linalg.`，已进进度库的 ID 不改。
- **节内容** `content/sections/<节id>.json`：块类型只有六种（ADR 0058）——
  `retrieval`（节首提取题，出现在一切揭示内容之前）、`prose`（正文，KaTeX 公式用
  `$...$` 行内、`$$...$$` 块级）、`example`（例题，折叠分步解答，每步带 `why`）、
  `pitfall`（正反例并排）、`exercise`（判分练习：`choice`/`numeric` 两种答案形态，
  带 `varies` 写明这道题换了什么角度）、`figure`（SVG 插图，文件放
  `content/sections/assets/`）。
- **每节必有可提取的东西**（ADR 0096）：节首 `retrieval` 是底线；答错的常见误解进
  `pitfall`，不写「看懂了」自评。
- **能画的就画**（ADR 0056）：几何意义、变换过程画成 SVG；能由数据算出来的后续做成
  交互，不放假交互。
- 篇幅与掌握目标匹配，不写八股（ADR 0040）。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust），Rust 侧只传一份 `ShellConfig` 给共用课程壳
  `athena_course_shell`（仓库级 ADR 0161；本应用不自带任何窗口与进度逻辑）。
  更新器按仓库级 ADR 0172 接入（`@athena/app-update` + updater 插件）。
- **界面**：Vite + TypeScript + React（catalog 版本）。KaTeX 本地打包渲染公式，
  不走 CDN。内容 JSON 构建期打包进前端，应用独立可运行。
- **进度**：SQLite（共用壳的 store），用户数据目录 `AthenaLinearAlgebra/learning.db`，
  不进 git、由启动器同步到路由器（ADR 0037、0155）。`mastery` 由作答派生
  （答对 +1 上限 5、答错 −1 下限 0），只由作答写入；`quiz_picks` 存每次作答。
  知识点 ID 前缀 `linalg.`。
- 端口 1524（HMR 1624）；进程 `athena-linear-algebra`；数据目录 `AthenaLinearAlgebra`。

## 目录与所有权

| 路径 | 职责 |
|---|---|
| `content/` | 课表、知识点、节内容、真题整卷；**唯一内容源** |
| `src/` | 前端：课表导航 / 节页块渲染 / 判分作答 |
| `src-tauri/` | 只有 `ShellConfig` 名字配置，窗口与进度在共用壳 |
| `scripts/check.py` | 本应用验证入口（内容一致性 + 判分出处 + 构建） |
| `app.json` | 声明怎么启动与进度库（ADR 0046、0155） |
| `docs/decisions/` | 本应用 ADR |
| `AGENTS.md` | 本文 |

## 开发与验证

```sh
launcher open linear-algebra            # 日常开发：tauri:dev，热更新
python3 scripts/check.py linear-algebra # 仓库根执行：内容校验 + 构建 + Rust 检查
python3 scripts/check.py linear-algebra --skip-rust   # 只改内容/前端时用
```

- 验证改动一律走 `tauri:dev`，不做打包副本循环。
- `ATHENA_LINEAR_ALGEBRA_ROOT` 可强制指定应用根目录（含 `content/`）。

## 修改流程

1. 改内容：只动 `content/`，改完跑 check（内容校验会拦知识点引用错、判分题缺出处、
   数值答案与解析不一致的算术错误要靠自查——提交前把每道计算题手算一遍）。
2. 改界面：先确认块类型表达得了，新增块类型先在本文登记再动 `src/`（ADR 0058）。
3. 改运行时：`src-tauri` 只动名字配置与版本；窗口、进度逻辑在共用壳，改壳是仓库级决定。
4. 真题整卷录入按 `content/exams/README.md` 的格式与录入规则；录入的代理只写
   `content/exams/`，改节内容挂接出处由内容负责人做。
