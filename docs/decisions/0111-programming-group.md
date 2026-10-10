# ADR 0111：「编程」圈改名「程序设计」，linux 入圈（去挂靠）

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「Linux程序设计的课程 挂靠在编程分组下面
  编程分组改名 程序设计」）
- 关系：修订 [ADR 0109](0109-linux-subapp.md) 决策 1 的 `parent: software`（由本条
  改为无挂靠、group 入「程序设计」圈）；改名沿 [0102](0102-exam-apps-as-top-level-groups.md)
  的领域圈改名先例；挂靠转内容指引沿 [0098](0098-minimal-links.md) 的既有模式；
  领域圈成员即兄弟沿 [0101](0101-domain-circle-siblings-no-links.md)

## 背景

1. tiger 决定 Linux 程序设计在启动器里归入「编程」分组，并把该分组改名为
   「程序设计」。
2. 机制说明：挂靠节点画在挂靠者外一圈、不占领域圈位置（ADR 0092）——linux
   若保留 `parent: software`，无论 group 写什么，都不会出现在「程序设计」圈里。
   入圈即去挂靠。
3. linux 与 software 的实质关系是「软设第 4 章 Linux 命令实验的承接」（ADR 0109），
   这层关系由课程树的文字指引表达即可（0098 先例：dsa 曾从挂靠降为内容指引）；
   linux 作为独立学科与 gtkmm 平级入圈，语义更准。

## 决策

1. **「编程」领域圈改名「程序设计」**：gtkmm 的 group「编程」→「程序设计」；
   c-gui-lab 的 group「编程」→「程序设计」（其 parent=software 挂靠保留，沿用
   挂靠者领域圈不变，此字段保持语义一致备将来）。
2. **linux 入圈、去挂靠**：group「Linux」→「程序设计」，删除 `parent: software`；
   与 gtkmm 同圈并肩（领域圈成员即兄弟，ADR 0101）。启动器领域圈「Linux」退役，
   「程序设计」圈两成员（gtkmm、linux）。
3. **承接降为内容指引**：软设第 4 章 Linux 命令实验仍由 linux 承载，software
   课程树在对应章节放「去 linux 做实验」的文字指引（0098 模式），无挂靠连线。
   ADR 0109 决策 1 的 `parent: software` 由本条取代（原文不改）。
4. 图标（Tux）、端口 1499、前缀 `linux.`、技术架构不变。

## 后果

- 领域圈「编程」→「程序设计」（gtkmm、linux 两成员）；「Linux」圈退役；
  software 的挂靠子应用减为 8 个。
- content-plan 的 Linux 承接表述同步；启动器零改动。
