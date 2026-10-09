# ADR 0108：dsa 拆分为「数据结构」与「算法设计」两个独立应用

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「数据结构和算法设计 有必要拆分成两门课
  我觉得有必要吧」；Q5 选 B 按软考教材章硬切内容边界）
- 关系：拆分 [ADR 0092](0092-launcher-tree-attach-and-softcert-rename.md)
  决策 4 建立的应用（原 algorithm，[0105](0105-dsa-rename-back.md) 复名 dsa）；
  修订 [0103](0103-practice-courses-as-attached-subapps.md) 决策 2 表格的 dsa 行
  与决策 6 的承接表述；[0099](0099-dsa-reattach.md) 的挂靠承接由两个新应用延续；
  命名按 [0100](0100-single-word-app-ids.md)、[0104](0104-os-rename.md)

## 背景

1. dsa 一个应用承接整门 DSA 学科与软设第 3、8 章的编码实验，curriculum 按
   四条 track 组织（度量与线性 / 关联与层次 / 排序与图 / 解题范式，共 7 章），
   spine 是贯通主线「选结构 → 选策略」。
2. tiger 2026-10-10 提出拆分：「数据结构和算法设计有必要拆分成两门课」。学科
   上「数据结构」与「算法设计与分析」本就是两门独立课程（大学课程表可证），
   软考考纲也是两个知识域：第 3 章（数据结构——线性、树、图、**查找、排序**）、
   第 8 章（算法设计——**复杂度**、算法策略）。
3. 按 0103 三判据两门各自成立：各自成课；实践性强（ADR 0107 三维评级两章
   全高，B ✓✓）；有具体产出（可编译运行的 C++ 实验，dsa 的即时编译体系现成）。
   dsa 进度库仅 6 行记录，拆分迁移近零成本。

## 决策

1. **拆分与命名**：新增 `subjects/data-structures`（title「数据结构」，group
   「数据结构」）与 `subjects/algorithms`（title「算法设计」，group「算法」），
   均为技术学习类学习应用（出处 open 档，沿 dsa 现档），壳与实验引擎沿用
   dsa 架构（Tauri 2 + C++ 即时编译）。命名：`algorithms` 是领域通行词；
   `data-structures` 是显式词组例外——单词候选无一达课程全意，按 0104 的
   operating-system 先例收完整词组。
2. **内容边界按软考教材章硬切**（tiger 选 B，不按 curriculum 现有 track 切）：
   - **data-structures**（软设第 3 章）：linear（线性结构）、hash（查找）、
     tree（树与堆）、sorting（排序与查找）、graph（图）——查找与排序是第 3 章
     的组成小节，随章走；
   - **algorithms**（软设第 8 章）：complexity（复杂度与度量——第 8 章算法
     基础）、paradigm（算法范式——第 8 章算法策略）；cases 实验按知识点
     归属随章分（big_o_growth、climb_stairs 等复杂度/策略实验归 algorithms）。
   切分后各自的 spine 在迁移时重写为单课程主线，不再共用「选结构 → 选策略」
   贯通叙事。
3. **挂靠与承接**：两个应用都 `parent: software`（Q6 A）——data-structures
   承接软设第 3 章编码实验，algorithms 承接第 8 章；softcert→software 侧
   课程树的「去 dsa 做实验」指引改指对应新应用。0103 决策 2 表格中
   「dsa | 算法 | software | 软设第 3、8 章」一行由本条的两应用取代（原文不改）。
4. **端口与前缀**：data-structures 端口 1497、进程 `athena-data-structures`；
   algorithms 端口 1498、进程 `athena-algorithms`。知识点前缀新起 `ds.` 与
   `algo.`——dsa 进度库仅 6 行记录，**不迁移**，两应用各自建新进度库
   （「已写进进度库的前缀不改」约束随旧库退役一并消失）。
5. **dsa 退役**：内容与实验迁空后删除 `subjects/dsa` 目录，git 历史保留全部；
   其应用级 ADR（0001–0004）随之成为历史档案——两个新应用把其中仍然成立的
   架构约束（大纲先行、随章测验、实验给骨架、可追踪可视化）写进各自的
   AGENTS.md 作为现行规则，不整篇拷贝（ADR 0040 同一组东西不写两遍；
   ADR 0062 约束不继承、自己写下理由）。

## 后果

- 应用 +2 −1；领域圈「算法」变为「数据结构」「算法」两圈，software 挂四个
  实践子应用（database、design-patterns、os、network）+ 两个学科应用
  （data-structures、algorithms）+ c-gui-lab。
- 启动器零改动：parent/group 声明驱动，`仓库里的真实清单排得干净` 测试
  守住新布局。
- 已知代价：跨应用的交错练习（ADR 0094 主导策略之一）在两应用间无自动机制，
  由课程树的文字指引缓解；后续若要做跨应用交错，另立 ADR。
- 根 `AGENTS.md` 的 subjects 清单、software 的 content-plan 承接表述同步。
