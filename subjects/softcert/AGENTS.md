# 软考应用协作规则

仓库级规则见根 `AGENTS.md`,本文只写本应用自己的约定。本应用是**学习应用**
(三类判据见 `docs/REPOSITORY.md`):要教会人考过软考中级,并用可观察的证据
证明掌握度在进步。跨应用教学规范(`docs/TEACHING.md`)全部生效。

## 应用定位

- **以考试为学科**(与驾考 `driver` 同构):一门应用绑定一个考试——本应用只
  承载软考中级·软件设计师,`swd` 一门课程,计算机系统基础、操作系统等公共
  共用章节都在它的课程树里。**一个考试一个应用**(仓库 ADR 0095):软考其他
  方向(网络工程师等)落地时独立成新应用,不再作为课程加进本应用;
  `courses.json` 的多课程注册表是拆分前的历史结构,保留但不再扩。嵌入式系统
  设计师已拆出为 `subjects/esd`(仓库 ADR 0090、本应用 `docs/decisions/0001`)。
- **考纲对齐、分值驱动**。每章带 `exam_weight`(1–3,分值权重的粗分档)与
  `grade`(S 核心 / A 重要 / B 次要 / C 突击),取值依据近五年真题分值统计
  (登记在 `content/sources.json`),不是拍脑袋。大纲层长在考试结构上,不长在
  教材目录上。
- 考试硬事实写死在 UI 常量里要给出处:两科同时 ≥45 分通过、综合知识 75 空
  单选、案例分析约 5 道大题。(嵌入式系统设计师的一年一考事实随内容迁至 esd 应用。)

## 内容组织

```
content/
├── sources.json            来源登记(出处检查的 catalog)
├── courses.json            课程注册表(两门课的入口)
├── <course>/course.json    课程内章节树 + 知识点评级 + 考纲权重
├── <course>/chapters/*.json   章节教学内容(blocks)
├── <course>/quizzes/*.json    章节课后考核题(带出处)
├── textbooks/              官方教材 OCR 原文(swd5ed 12 章,按章与节)
├── references/             参考资料 OCR 文本(考试大纲、专业英语词汇、三色笔记)
└── past-exams/             历年真题演练(导入格式见其 README)
```

- **内容驱动 UI(ADR 0058)**:全部讲解由 9 种块类型承载——`lead` `text`
  `formula` `compare` `steps` `table` `code` `callout` `viz`。新章不许手写整页;
  确需专属可视化时做成 `viz` 组件注册进 `src/viz/`,组件是内容的一部分。
- **知识点评级只给已写出教学内容的章节**:难度 1–5、掌握目标
  (`proficient` 熟练 / `understand` 理解 / `aware` 了解)、类型
  (`concept` / `skill` / `strategy`)、先修 `requires`(知识点 id 数组)。
- **篇幅与掌握目标匹配(ADR 0040)**:`aware` 档的章节不许比 `proficient`
  档写得还长;写完对照评级校准。
- **章节建设顺序与练习形态**按 [docs/content-plan.md](docs/content-plan.md)
  的实践路径评级执行——实践只有两条路径：真硬件实验（路径 A）或独立技术体系
  真编码/真执行（路径 B），纸笔计算题属理论侧；理论章只做讲解、viz 演示与
  记忆卡测验，不冒充实实验。可执行实验落地前先立 ADR 扩展 ADR 0058。

## 判分与出处(ADR 0043)

- **题目必须带 `source`**。两种合法形态:
  - `authored`(自造考点题):`{"relation":"authored","sourceId":"self-authored",
    "why":"为什么没有现成材料","locator":"依据 2019 版考纲 §2.2"}`。
  - 真题引用:`{"relation":"verbatim","sourceId":"past-exam-2021a","locator":"第 12 题"}`。
    **年份与题号必须来自导入的真实试卷,严禁凭记忆编造真题编号。**
- 真题数据只经 `content/past-exams/` 导入流程进仓库:整卷、带官方出处,
  `papers.json` 登记。当前已入库 34 卷软件设计师历年真题(2006–2024),导入格式见该目录 README。
- 每道题 4 个选项、单选,`answer` 是正确项下标;解析写 `explanation`,
  至少说清错误选项错在哪。

## 掌握度与激励(ADR 0052)

- **掌握度只由作答写入**:作答进 `progress/learning.db` 的 `attempts`,
  掌握率由最近作答派生,不单独存"掌握度"字段。
- 激励只展示派生量(今日作答、连对、章节完成度);没有记录就没有徽章。

## 进度库

- `progress/learning.db` 随仓库走(ADR 0037、0053),Rust 侧自建自迁移:
  仓库工作树内(以 `app.json` 存在为准)写 `progress/learning.db`,
  发行包写系统数据目录。schema 变更直接改 `store.rs` 的建表语句并保证
  旧库可迁移——进度库很小,`ALTER TABLE` 兜底即可,不引迁移框架。

## 验证与构建

```sh
python3 scripts/check.py                 # 内容校验 + 前端构建 + Rust 检查与测试
python3 scripts/check.py --skip-rust     # 只改内容或前端时用
```

- 内容 JSON 语法、章节/知识点/题目结构、`requires` 引用存在性、题目出处
  字段齐备,由 `check.py` 的 `check_content` 把关;跨应用出处检查由根
  `scripts/check-app-sources.mjs` 按 `content-contract.json` 接入。
- 前端构建(`tsc && vite build`)与 Rust `cargo check` + `cargo test` 都要过;
  跨平台是硬约束,脚本用 Python 写,不依赖 shell。
