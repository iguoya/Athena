# Athena Mathematics · ADR 索引

本目录只记录 **`apps/mathematics` 独立应用** 的架构与内容写作决策。主仓库
`docs/decisions/` 约束 GTK 主程序；精神可对齐，编号与文件互不混用。

| 编号 | 决策 | 状态 |
|---|---|---|
| [0001](0001-judge-not-calculator-and-resident-engine.md) | 工具当裁判不当计算器；符号引擎随包常驻前端 | 已接受 |
| [0002](0002-ideas-are-the-main-line-not-decoration.md) | 思想、直观与现实闭环是主线，不是解题之外的装饰 | 已接受（「双重目标」一节由 0003 取代） |
| [0003](0003-practical-learning-modeling-line-exam-as-constraint.md) | 经世致用是总纲；建模独立成线，考试只是约束 | 已接受 |
| [0004](0004-algorithm-vs-trick-and-unified-organization.md) | 算法与技巧分界；按统一视角组织，不按计算对象分章 | 已接受 |
| [0005](0005-natural-order-intuition-first.md) | 按直观、直觉、自然的顺序讲数学；以及两条防线 | 已接受 |
| [0006](0006-four-layers-generality-decides-weight.md) | 思想、方法、算法、技巧四层；通用性决定权重 | 已接受（细化 0004 的二分） |
| [0007](0007-scope-math2-first.md) | 先做数学二；范围用标记表达，不做物理删除 | 已接受（范围表每年核对） |
| [0008](0008-topological-path-and-problem-as-motivation.md) | 学习路径按先修图拓扑序；现实问题作为引入动机而非课后应用 | 已接受 |
| [0009](0009-textbook-and-syllabus-coordinates.md) | 每个知识点标注教材与考纲坐标 | 已接受（教材版本每年核对） |
| [0010](0010-external-math-software-roles.md) | 外部数学软件按三种角色分别裁定 | 已接受（Manim 待用） |
| [0011](0011-design-for-focus-and-sustained-engagement.md) | 为专注与持续投入设计；区分有效困难与无效挫折 | 已接受 |
| [0012](0012-spiral-three-passes.md) | 螺旋式三遍；第一遍求通不求全 | 已接受（调整 0008 第 4 节的编写顺序） |
| [0013](0013-writing-serves-confidence-patience-focus.md) | 编写学习内容时时刻服务信心、耐心、专心 | 已接受（含可 lint 的禁用词表） |
| [0014](0014-exercises-verify-and-teach.md) | 习题是检验器，也是学习动作本身；梯度按变式与渐隐设计 | 已接受 |
| [0015](0015-starting-point-and-prerequisites.md) | 显式声明学习者起点；前置基础独立成层并按需诊断 | 已接受（修正 0007 的 scope 与 REFERENCES 第六节） |
| [0016](0016-building-it-is-studying-it.md) | 编写这个软件本身就是学习动作；但要划清内容与工程的界 | 已接受（撤销 REFERENCES 第六节的「净支出」判断） |
| [0017](0017-anchor-each-stage-to-a-real-textbook.md) | 每个阶段锚定一份真实教材；严格表述必须可核对 | 已接受（部分作废 0012 第 4 节） |
| [0018](0018-voice-and-scripted-animation.md) | 概念节可用语音讲解与脚本动画；二者跟课表走 | 已接受 |
| [0019](0019-exercises-must-be-sourced-and-worked-examples.md) | 练习与测验必须有所本；每节配标准例题 | 已接受（修正 0017 第 1 节，补齐 0014 第 2 节） |
