# ADR 0126：software 与 database 入「计算机」圈，软考系聚回一处

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「软件设计师 挂靠在计算机下面吧 数据库也是」）
- 关系：修订 [ADR 0124](0124-software-to-programming-group.md) 的 software 领域圈
  归属（程序设计圈改回计算机圈）；修订 [ADR 0103](0103-practice-courses-as-attached-subapps.md)
  决策表格 database 行的挂靠安排；「入圈即去挂靠」沿
  [ADR 0111](0111-programming-group.md)、[ADR 0121](0121-design-patterns-to-programming-group.md)、
  [ADR 0123](0123-embedded-practice-subapps-to-electronic-info.md) 先例

## 背景

1. ADR 0124 把 software 放进「程序设计」圈，是当时对「软件设计师也挂靠程序设计
   下面」的解读；tiger 随后明确组织意图：软考系应用聚在「计算机」圈（与 cs408
   同圈），不散在技术圈里。
2. database 是 software 的挂靠子应用（`parent: software`，ADR 0103），画在挂靠者
   外一圈，`group`（「数据库」）从不生效。要进「计算机」圈就得去挂靠（0111/0121/
   0123 的既定先例：入圈即去挂靠）。

## 决策

1. software 的 `group` 由「程序设计」改回「计算机」，与 cs408 同圈；software 本
   无 `parent`。
2. database 删除 `parent: software`，`group` 由「数据库」改为「计算机」；其
   `check.py` 的 parent 校验改为「不得声明 parent」。
3. 课程定位与出处档位不变：database 仍是软设第 9 章的实践课程（课程树文字指引，
   ADR 0098 模式），software 仍是软考大类应用（ADR 0118）。

## 后果

- 「计算机」圈三成员：cs408、software、database；「程序设计」圈回到三成员
  （gtkmm、linux、design-patterns）；software 的挂靠圈清空（0119 后果里的
  软设外圈只剩 c-gui-lab）。
- software 对 database 的挂靠关系解除；database 在导图上是计算机圈的平等成员。
