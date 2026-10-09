# 嵌入式系统设计师应用协作规则

仓库级规则见根 `AGENTS.md`,本文只写本应用自己的约定。本应用目录 id `embedded-system-designer`(ADR 0097 全称化;内容层的 `esd-`
章节 id 与 `esd.*` 知识点前缀是内容层短名,保留)。本应用是**学习应用**
(三类判据见 `docs/REPOSITORY.md`):要教会人考过软考中级·嵌入式系统设计师,
并用可观察的证据证明掌握度在进步。跨应用教学规范(`docs/TEACHING.md`)全部生效。

## 应用定位

- **以考试为学科**,从 `softcert` 拆出独立成应用(仓库 ADR 0090、本应用
  `docs/decisions/0001`):一门应用承载一门考试,`content/esd/course.json`
  就是课程根,单课程不再有注册表层。
- **考纲对齐、分值驱动**。每章带 `weight`(1–3,分值权重的粗分档)与
  `grade`(S 核心 / A 重要 / B 次要 / C 突击),取值依据近五年真题分值统计
  (登记在 `content/sources.json`)。大纲层长在考试结构上,不长在教材目录上。
- 考试硬事实写死在 UI 里要给出处:两科各 75 分、同时 ≥45 通过;综合知识
  75 空单选;案例分析约 5 道大题(硬件接口/ARM 体系/RTOS 编程/C 填空/方案
  选型);一年一考,2024 年起为上半年 5 月底。

## 技术栈与选型理由

- **Tauri 2**(Rust 壳 + 系统 WebView)+ **Vue 3 + TypeScript + Vite** +
  **Tailwind CSS 4**(经 `@tailwindcss/vite` 接入)+ **motion-v**(入场编排,
  基础转场用 Vue 内置 `<Transition>`)+ **lucide-vue-next** 图标 +
  **katex**(公式块)。与 `subjects/math-tools` 同一套技术体系(使用者点名要
  与 softcert 不同的体验),选型理由见该应用 `AGENTS.md`。
- 包管理用 **npm**(本机 corepack 无权限写 Program Files,不引入 pnpm 依赖)。
- dev 端口 **1480**(strictPort);进程/二进制 `athena-embedded-system-designer`;
  窗口标题「嵌入式系统设计师」;应用内文案用中文。

## 内容组织

```
content/
├── sources.json            来源登记(出处检查的 catalog)
├── esd/course.json         课程:章树 + 知识点评级 + 考纲权重
├── esd/chapters/*.json     章节教学内容(blocks)
├── esd/quizzes/*.json      章节课后考核题(带出处)
├── textbooks/esd2ed/       官方教材 OCR 原文(第 2 版 11 章,按章与节)
└── past-exams/             历年真题演练(2010–2020 十一卷;导入格式见其 README)
```

- **内容驱动 UI(ADR 0058)**:全部讲解由 9 种块类型承载——`lead` `text`
  `formula` `compare` `steps` `table` `code` `callout` `viz`。新章不许手写整页;
  确需专属可视化时做成 `viz` 组件注册进 `src/viz/index.ts`,组件是内容的
  一部分。
- **知识点评级只给已写出教学内容的章节**:难度 1–5、掌握目标
  (`proficient` / `understand` / `aware`)、类型(`concept` / `skill` /
  `strategy`)、先修 `requires`(知识点 id 数组,**先修只在本应用内引用**——
  跨应用先修写进 `guide_line` 文字提示,如「在软考·软件设计师应用学」)。
- 知识点 id 前缀 `esd.`(如 `esd.mcu`、`esd.os.rtos`):从 softcert 迁出时
  由 `sc.esd.*` 改写(当时无任何作答数据,零损失)。
- **篇幅与掌握目标匹配(ADR 0040)**:`aware` 档的章节不许比 `proficient`
  档写得还长;写完对照评级校准。

## 判分与出处(ADR 0043、0089:考试档)

- **题目必须带 `source`**。合法形态:
  - `verbatim` 真题:`{"relation":"verbatim","sourceId":"past-exam-esd-201011","locator":"第 12 题"}`,
    年份与题号必须来自导入的真实试卷,严禁凭记忆编造。
  - `adapted` 教材改编:`{"relation":"adapted","sourceId":"textbook-esd-2ed","why":"...","locator":"§2.6.2"}`。
  - `authored` 自造:`{"relation":"authored","sourceId":"self-authored","why":"...","locator":"依据 2019 版考纲 §2.2"}`。
- 真题数据只经 `content/past-exams/` 导入流程进仓库:整卷、带官方出处,
  `papers.json` 登记。**当前 16 道章节考核是 adapted/authored 存量,属考试档
  欠账**(契约 `blocking: false` + 备注写明);替换为对应章节真题精选后把
  `content-contract.json` 的 `blocking` 改回 `true`。
- 每道题 4 个选项、单选,`answer` 是正确项下标;解析写 `explanation`,
  至少说清错误选项错在哪。

## 掌握度与激励(ADR 0052)

- **掌握度只由作答写入**:作答进 `progress/learning.db` 的 `attempts`,
  掌握率由最近作答派生,不单独存「掌握度」字段。
- 激励只展示派生量(今日作答、连对、章节完成度);没有记录就没有徽章。

## 进度库

- `progress/learning.db` 随仓库走(ADR 0037、0053),Rust 侧自建自迁移:
  仓库工作树内(以 `app.json` 存在为准)写 `progress/learning.db`,
  发行包写系统数据目录。schema 变更直接改 `store.rs` 的建表语句并保证
  旧库可迁移——进度库很小,`ALTER TABLE` 兜底即可,不引迁移框架。

## 界面组织

与 softcert 刻意保持两种成体系的体验（ADR 0090 的拆分目的就是好做对比），
差异落在四个层面，改界面前先想清楚对应差异还在不在：

1. **导航骨架**：顶部指挥台（固定顶栏承载全部全局导航：视图胶囊 + 皮肤切换），
   不设侧栏；softcert 是左侧栏章树 + 内容区。
2. **课程呈现**：学习路径时间线——章是轨道里程碑、节是路径节点，纵向一条线；
   softcert 是章节列表卡片。
3. **首页取向**：行动面板——打开即「现在学什么」（接着学/开始学习主卡），
   介绍性大标语压缩为一行事实；softcert 是介绍式 hero + 课程卡。
4. **学习与考核流**：学习页是阅读器（内容块直接铺在学习流上，无容器大卡，
   列宽收窄到 820）；随堂考核支持键盘流（A–D / 1–4 作答、Enter 下一题）；
   softcert 是卡片包内容的阅读 + 纯点击作答。

## 皮肤机制

一套组件、令牌换氛围(与 math-tools skins 同构):三套浅色皮肤(电路/晨读/
草稿)定义在 `src/style.css` 的 `--tk-*` 令牌块,清单与切换在 `src/theme.ts`,
偏好存 localStorage(`esd-skin`)。组件里**不硬编码主色**——用 `accent-gradient`、
`accent-soft`、`accent-fg`、`text-gradient`、`tk-card`、`tk-display` 这些
类;品牌绿 `#0E8A6D` 只出现在令牌与 icon.svg。新增皮肤 = 加一段 `--tk-*`
令牌 + `SKINS` 一行,不动组件。

## 验证与构建

```sh
python3 scripts/check.py                 # 内容校验 + 前端类型检查与构建 + Rust 检查与测试
python3 scripts/check.py --skip-rust     # 只改内容或前端时用
python3 scripts/check.py --content-only  # 只跑内容校验
```

- 内容 JSON 语法、章树/节评级/题目结构、`requires` 引用存在性(限本应用)、
  题目出处字段齐备、viz 组件注册对账,由 `check.py` 把关;跨应用出处检查由
  根 `scripts/check-app-sources.mjs` 按 `content-contract.json` 接入。
- 前端(`vue-tsc --noEmit && vite build`)与 Rust `cargo check` + `cargo test`
  都要过;跨平台是硬约束,脚本用 Python 写,不依赖 shell。

## 约定

- 影响本应用架构边界的新决定,在 `docs/decisions/` 增补 ADR 后再动代码。
- 与 `softcert` 构建完全隔离(ADR 0032、0062):不引用它的路径、配置或代码;
  内容格式同构是历史渊源,不是运行时依赖。
