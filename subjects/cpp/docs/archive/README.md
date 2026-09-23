# 历史归档

这里保存被取代的架构快照、旧布局 ADR 和未采用的提案**原文**。它们记录当时的判断和路径
语境，方便追溯"为什么曾经那样做、后来为什么改"，但**不描述现状，也不作为实现依据**。

- 开始新任务不需要读本目录；当前入口见 [开发文档](../README.md)。
- 归档文件保持原样，包括其中已经失效的路径、命令和状态描述；发现与现状不符不必回改，
  改的是当前规范。
- 归档不删除。若某个决定重新生效，新增 ADR 说明理由，而不是把旧文搬回。

## 2026-09-09

ADR 0027 落地时的一次整理：架构与代码组织文档瘦身为现状说明，学习工作台的多份平行提案
与已被取代的布局 ADR 一并归档。

| 归档文件 | 当时作用 | 现在看哪里 |
|---|---|---|
| [ARCHITECTURE.md](2026-09-09/ARCHITECTURE.md) | 含大量历史沿革的架构长文 | [ARCHITECTURE](../ARCHITECTURE.md) |
| [CODE_ROLES.md](2026-09-09/CODE_ROLES.md) | 代码组织的完整比喻体系 | [CODE_ROLES](../CODE_ROLES.md) |
| [LEARNING_WORKSPACE_PROPOSAL.md](2026-09-09/LEARNING_WORKSPACE_PROPOSAL.md) | 学习工作台总提案 | [LEARNING_DESIGN](../LEARNING_DESIGN.md) |
| [LEARNING_WORKSPACE_LOOP_ENGINE.md](2026-09-09/LEARNING_WORKSPACE_LOOP_ENGINE.md) | 学习闭环引擎设想 | 同上；通用引擎已由 ADR 0027 排除 |
| [LEARNING_WORKSPACE_BENCH.md](2026-09-09/LEARNING_WORKSPACE_BENCH.md) | 实验台形态探索 | [ARCHITECTURE](../ARCHITECTURE.md) 的专注实验部分 |
| [LEARNING_WORKSPACE_SKETCH.html](2026-09-09/LEARNING_WORKSPACE_SKETCH.html)、[LEARNING_WORKSPACE_FLOW_SKETCH.html](2026-09-09/LEARNING_WORKSPACE_FLOW_SKETCH.html) | 早期布局草图 | 具体教案自带布局方案，如 [类型推导](../lessons/type_deduction.md) |
| [decisions/](2026-09-09/decisions/) | ADR 0003、0017、0020、0022、0023、0025 | [ADR 索引](../decisions/README.md) 的「已归档的编号」 |

被归档的 ADR 中仍然有效的结论，已在 [ADR 索引](../decisions/README.md) 中逐条注明；
其余部分不再指导开发。
