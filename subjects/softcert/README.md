# 软考(软考中级备考)

以软考中级·软件设计师为目标的学习应用:考纲对齐、分值驱动,当前包含**计算机
系统基础**与**操作系统**等公共共用课程(章节树对齐官方教材第 5 版),章节
课后考核与历年真题演练,掌握度由作答写入 `progress/learning.db`。嵌入式系统
设计师已拆出为 [`subjects/esd`](../esd)(仓库 ADR 0090),两应用同挂启动器「软考」分组。

- 打开:`launcher open softcert`
- 验证:`python3 scripts/check.py`
- 结构与规则:`AGENTS.md`;真题导入:`content/past-exams/README.md`

与驾考(`driver`)同构——以考试为学科。考试事实:两科同时 ≥45 分通过;
综合知识 75 空单选;案例分析约 5 道大题。
