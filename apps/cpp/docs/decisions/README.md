# ADR 索引

架构决策记录保存重要取舍的背景、决策与后果。它们**不是实时功能清单**：一条 ADR 说明
当时为什么这样选，后来的修订以 [ARCHITECTURE](../ARCHITECTURE.md)、
[LEARNING_DESIGN](../LEARNING_DESIGN.md) 等当前规范为准。

影响架构边界或不可逆方向的新决定，先新增 ADR 再动代码；编号只增不改，被取代的记录保留原文。

本索引只收 **apps/cpp 自己的** ADR。影响仓库结构或多个应用的决策在仓库级
[`../../../../docs/decisions/`](../../../../docs/decisions/README.md)——两处各自延续编号，
所以两边都有跳号（ADR 0045）。

## 配置、生成与代码组织

| 编号 | 决策 | 状态 |
|---|---|---|
| [0001](0001-data-driven-chapter-model.md) | `athena.json` 单一数据源与确定性代码生成 | 已接受 |
| [0004](0004-athena-core-static-library.md) | 领域核心编译为 `athena-core` 静态库，与 GTK 解耦 | 已接受 |
| [0005](0005-no-top-level-namespace.md) | 不使用项目顶层命名空间，优先 `using namespace std` | 已接受 |
| [0013](0013-single-author-validation-runtime-catalog.md) | Python 独占作者配置校验，C++ 只解码运行时 Catalog | 已接受 |
| [0014](0014-modularize-main-window-by-feature.md) | 按页面与用例拆分 `MainWindow` | 已接受，实施完成 |
| [0016](0016-split-learning-dialogs-by-responsibility.md) | 按单一职责拆分 `LearningDialogs` | 已接受，实施完成 |

## 学习内容与界面形态

| 编号 | 决策 | 状态 |
|---|---|---|
| [0002](0002-cpp-specific-content-scope.md) | 内容聚焦 C++ 特有语义，淡化与 C 重叠的基础 | 已接受 |
| [0012](0012-handbook-replaces-article-chapters.md) | 静态文档合并为「手册」，废弃 `content: article` 章节类型 | 部分失效，手册已由 0034 删除 |
| [0021](0021-category-index-page-replaces-chapter-tab-strip.md) | 分类索引页取代常驻章节标签条 | 已接受，实施中 |
| [0024](0024-widget-native-learning-content.md) | 学习内容统一由 GTK 控件承载，退出 Markdown/WebView 路线 | 已接受，载体迁移完成 |
| [0026](0026-native-learning-scenes-and-reference-material.md) | 原生学习场景与参考资料分离；Markdown 不约束表现形式 | 部分失效，参考资料一侧由 0034 删除 |
| [0027](0027-self-contained-multimedia-lessons.md) | 学习页自足讲解与多媒体教案 | 已接受，按单元逐步实施 |
| [0033](0033-live-visuals-and-interaction.md) | 大纲与教学过程用活的可视化和互动元素表达 | 已接受，`type_semantics` 大纲已改造 |
| [0034](0034-remove-markdown-handbook.md) | 删除 Markdown 参考手册，大纲只有原生一份 | 已接受，手册正文与页面已移除 |
| [0035](0035-use-gtk-expressive-ceiling.md) | 把 GTK 的表达上限用满，自绘层迁向 `Gtk::Snapshot` | 已接受，按收益分批迁移 |
| [0036](0036-chapter-guide-first.md) | 「本章导览」置于首位，作为极简概要 | **已被 0039 取代** |
| [0038](0038-figures-as-widgets-and-cairo.md) | 插图改由 GTK 控件与 Cairo 自绘承载，退出 SVG 图片路线 | 已接受，`type_semantics` 先行改造 |
| [0039](0039-merge-guide-into-outline.md) | 撤销「本章导览」，主旨并入教学大纲并精简 | 已接受，取代 0036 |
| [0053](0053-editable-scaffold-experiments.md) | 教学实验改为可编辑的骨架案例，本机编译运行 | 已接受，机制先行 |
| [0054](0054-sourced-teaching-content.md) | 教学内容与习题一律有据可依，官方规范优先 | 已接受，登记表与校验先行 |
| [0055](0055-lesson-content-as-data.md) | 学习页内容改由数据驱动，`.blp` 降为块模板 | 已接受，新章走数据、存量不迁 |

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
