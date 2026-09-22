# 仓库级 ADR 索引

这里收**影响仓库结构或多个应用**的架构决策记录。只管某一个应用的决策记在该应用自己的
`docs/decisions/` 下，例如 [`apps/cpp/docs/decisions/`](../../apps/cpp/docs/decisions/README.md)。
两处各自延续编号，所以两边都有跳号（ADR 0045）。

架构决策记录保存重要取舍的背景、决策与后果，**不是实时功能清单**：一条 ADR 说明当时
为什么这样选，后来的修订以 [`AGENTS.md`](../../AGENTS.md) 等当前规范为准。影响架构边界
或不可逆方向的新决定，先新增 ADR 再动代码；编号只增不改，被取代的记录保留原文。

## 跨应用教学规范

| 编号 | 决策 | 状态 |
|---|---|---|
| [0028](0028-outline-process-experiment-layering.md) | 大纲、教学过程、教学实验三层分工 | 已接受，`type_semantics` 已跟进 |
| [0029](0029-difficulty-and-mastery-goal.md) | 知识点按难度与掌握目标两个维度评级 | 已接受 |
| [0030](0030-knowledge-point-prerequisites.md) | 知识点级前置依赖与依赖方向校验 | 已接受，`type_semantics` 已声明 |
| [0031](0031-knowledge-type-drives-teaching-actions.md) | 知识类型（概念/技能/策略）决定教学动作 | 已接受，`type_semantics` 已标注 |
| [0040](0040-lesson-length-matches-mastery-goal.md) | 学习内容拒绝八股，篇幅与掌握目标匹配 | 已接受，第一章已按此精简 |
| [0043](0043-sourced-content-across-apps.md) | 「内容必须有出处」跨应用统一规范 | 已接受（统一 mathematics 0019、c 0003、english 0007–0009；第 7 节补充 cpp AI 出题反例） |
| [0052](0052-incentives-and-records-cooperate.md) | 激励与统计是同一条回路，必须互相配合 | 已接受（裁定 mathematics 0011 待定项；对齐 english 0009） |
| [0058](0058-content-driven-block-based-ui.md) | 内容驱动 UI：有限块类型胜过按章手写整页 | 已接受（统一 dsa 块架构与 cpp 反面案例） |
| [0059](0059-experiments-ship-skeletons-not-blank-slates.md) | 教学实验给骨架，不给白板 | 已接受（统一 dsa 0003、cpp 0053、mathematics 0014） |

## 应用边界与启动

| 编号 | 决策 | 状态 |
|---|---|---|
| [0032](0032-independent-apps-launched-as-processes.md) | 异构学习应用作为独立进程共处一个仓库 | 已接受；启动路径见 0041 |
| [0037](0037-independent-apps-own-their-progress-store.md) | 每个独立应用自建自管自己的进度库 | 已接受；库位置由 0053 修订 |
| [0041](0041-independent-apps-launch-in-dev-mode.md) | 独立应用从源码以开发模式启动，不经打包副本 | 已接受 |
| [0042](0042-c-language-qt-qml-lessons.md) | C 语言学习应用用 Qt Quick / QML 写教案 | 已接受 |
| [0044](0044-menubar-launcher.md) | 常驻菜单栏的启动器，主程序也只是其中一项 | 已接受 |
| [0045](0045-apps-are-peers.md) | C++ 教程降级为 `apps/cpp`，所有学习应用平级 | 已接受 |

## 仓库工程

| 编号 | 决策 | 状态 |
|---|---|---|
| [0007](0007-unified-check-entry.md) | 统一验证入口（现为 `scripts/check.py`） | 已接受；各应用均已接入 |
| [0046](0046-unified-dev-orchestrator.md) | 统一开发编排器，各应用只声明怎么启动 | 已接受 |
| [0047](0047-portable-by-default.md) | 跨平台优先：选型、代码与构建过程的默认原则 | 已接受 |
| [0048](0048-menubar-launcher-stays-macos-only.md) | 菜单栏启动器保留为 macOS 专属，只消费编排器结论 | 已接受 |
| [0049](0049-portability-is-a-cost-benefit-call.md) | 跨平台是成本收益判断，成本过高的整体排除 | 已接受；限定 0047 的边界 |
| [0050](0050-ci-runs-on-release-not-every-push.md) | 跨平台稳定之前，CI 推送即跑 | 已接受（阶段性，带退出条件） |
| [0051](0051-platform-priority-macos-windows-first.md) | 平台优先级：macOS 与 Windows 优先，Linux 降级 | 已接受；`apps/cpp` 的选型冲突已解决 |
| [0053](0053-progress-travels-with-the-repository.md) | 进度库随仓库走，换机器 clone 下来进度还在 | 已接受；修订 0037 第 1 条 |
| [0054](0054-prefer-adding-over-deleting.md) | 内容工作宁增勿删，参考不得用来重划结构 | 已接受；推翻 polaris ADR 0004、0005 的主干重划 |
| [0055](0055-no-institute-names-in-product-content.md) | 软件内容不出现具体院所名，一律用「某所」 | 已接受（强制，`scripts/check.py` 拦截） |
| [0056](0056-visualization-and-interaction-first.md) | 可视化与交互是学习内容本身，不是装饰 | 已接受（强制方针） |
| [0057](0057-assume-a-developer-machine.md) | 基线是一台开发机——依赖自行安装，不写兜底 | 已接受 |
