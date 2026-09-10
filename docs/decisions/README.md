# ADR 索引

架构决策记录保存重要取舍的背景、决策与后果。它们**不是实时功能清单**：一条 ADR 说明
当时为什么这样选，后来的修订以 [ARCHITECTURE](../ARCHITECTURE.md)、
[LEARNING_DESIGN](../LEARNING_DESIGN.md) 等当前规范为准。

影响架构边界或不可逆方向的新决定，先新增 ADR 再动代码；编号只增不改，被取代的记录保留原文。

## 配置、生成与代码组织

| 编号 | 决策 | 状态 |
|---|---|---|
| [0001](0001-data-driven-chapter-model.md) | `athena.json` 单一数据源与确定性代码生成 | 已接受 |
| [0004](0004-athena-core-static-library.md) | 领域核心编译为 `athena-core` 静态库，与 GTK 解耦 | 已接受 |
| [0005](0005-no-top-level-namespace.md) | 不使用项目顶层命名空间，优先 `using namespace std` | 已接受 |
| [0007](0007-unified-check-entry.md) | 统一验证入口 `scripts/check.sh` | 已接受 |
| [0013](0013-single-author-validation-runtime-catalog.md) | Python 独占作者配置校验，C++ 只解码运行时 Catalog | 已接受 |
| [0014](0014-modularize-main-window-by-feature.md) | 按页面与用例拆分 `MainWindow` | 已接受，实施完成 |
| [0016](0016-split-learning-dialogs-by-responsibility.md) | 按单一职责拆分 `LearningDialogs` | 已接受，实施完成 |

## 学习内容与界面形态

| 编号 | 决策 | 状态 |
|---|---|---|
| [0002](0002-cpp-specific-content-scope.md) | 内容聚焦 C++ 特有语义，淡化与 C 重叠的基础 | 已接受 |
| [0012](0012-handbook-replaces-article-chapters.md) | 静态文档合并为「手册」，废弃 `content: article` 章节类型 | 已接受 |
| [0021](0021-category-index-page-replaces-chapter-tab-strip.md) | 分类索引页取代常驻章节标签条 | 已接受，实施中 |
| [0024](0024-widget-native-learning-content.md) | 学习内容统一由 GTK 控件承载，退出 Markdown/WebView 路线 | 已接受，载体迁移完成 |
| [0026](0026-native-learning-scenes-and-reference-material.md) | 原生学习场景与参考资料分离；Markdown 不约束表现形式 | 已接受，第一条纵切实施中 |
| [0027](0027-self-contained-multimedia-lessons.md) | 学习页自足讲解与多媒体教案 | 已接受，按单元逐步实施 |
| [0028](0028-outline-process-experiment-layering.md) | 大纲、教学过程、教学实验三层分工 | 已接受，`type_semantics` 已跟进 |
| [0029](0029-difficulty-and-mastery-goal.md) | 知识点按难度与掌握目标两个维度评级 | 已接受 |
| [0030](0030-knowledge-point-prerequisites.md) | 知识点级前置依赖与依赖方向校验 | 已接受，`type_semantics` 已声明 |
| [0031](0031-knowledge-type-drives-teaching-actions.md) | 知识类型（概念/技能/策略）决定教学动作 | 已接受，`type_semantics` 已标注 |
| [0032](0032-independent-apps-launched-as-processes.md) | 异构学习应用作为独立进程共处一个仓库 | 已接受，`apps/c` 链路已通 |

## 学习数据与 AI

| 编号 | 决策 | 状态 |
|---|---|---|
| [0009](0009-sqlite-learning-store.md) | 学习数据持久化采用 SQLite | 已接受 |
| [0010](0010-deepseek-ai-explain-via-curl.md) | 知识点讲解经 `curl` 子进程调用 DeepSeek API | 已接受 |
| [0011](0011-multi-provider-ai-fallback.md) | 多服务商按优先级回退 | 已接受 |
| [0015](0015-ai-quiz-determines-mastery.md) | 熟练度由完整 AI 自测成绩自动评定 | 已接受 |

## 打包与发行

| 编号 | 决策 | 状态 |
|---|---|---|
| [0006](0006-macos-packaging-pipeline.md) | macOS 发行统一由 `package_macos.py` 与标签 CI 承担 | 已接受 |
| [0008](0008-version-single-source.md) | 版本号以 `meson.build` 为单一来源 | 已接受 |
| [0018](0018-linux-deb-appimage-release.md) | Ubuntu 同时发行 DEB 与 AppImage | 已接受 |
| [0019](0019-ubuntu-26-release-baseline.md) | Linux 发行以 Ubuntu 26.04 为基线 | 已接受 |

## 已归档的编号

下列 ADR 记录的是已经放弃的渲染后端或已被取代的布局方案，原文移入
[历史归档](../archive/README.md)，默认不读、不作为实现依据：

| 编号 | 决策 | 现状 |
|---|---|---|
| 0003 | 文章章节统一 WebView 渲染 | 由 0024 取代（退出 WebView） |
| 0017 | Ubuntu 使用 WebKitGTK 渲染文章 | 由 0024 取代 |
| 0020 | 文档主导的学习工作台与实验坞 | 由 0026 取代 |
| 0022 | 文档独立成窗口，实验坞作为对话框 | 由 0023、0026 取代 |
| 0023 | 单画布连续学习流 | 单一主要任务区域、跨页协调、退出运行历史仍有效；旧窗口布局与迁移步骤失效 |
| 0025 | 内联微型学习单元与专注实验工作区 | 学习单元与专注实验保留，Markdown 决定插入位置的部分被 0026 取代 |
