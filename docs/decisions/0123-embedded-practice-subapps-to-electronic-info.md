# ADR 0123：rtos、microcontroller、firmware 去挂靠入「电子信息」圈

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「将RTOS 硬件实验室 还有嵌入式程序设计 挂靠在
  电子信息下面」）
- 关系：修订 [ADR 0103](0103-practice-courses-as-attached-subapps.md) 决策表格
  firmware、microcontroller 两行与 [ADR 0106](0106-rtos-subapp.md) 的挂靠安排
  （原文不改）；「入圈即去挂靠」沿 [ADR 0111](0111-programming-group.md) 的
  linux、[ADR 0121](0121-design-patterns-to-programming-group.md) 的
  design-patterns 先例；挂靠机制与单父语义沿 [ADR 0092](0092-launcher-tree-attach-and-softcert-rename.md)

## 背景

1. ADR 0103/0106 把 firmware（嵌入式程序设计）、microcontroller（硬件实验台）、
   rtos（实时操作系统（RTOS））定为 embedded（嵌入式系统设计师）的挂靠子应用，
   画在挂靠者外一圈。三者的 `group` 字段（「嵌入式程序设计」「硬件实验」
   「实时操作系统」）因挂靠优先于分组而从不生效——领域胶囊里从来没有它们。
2. tiger 要求三者改挂「电子信息」。「电子信息」是领域圈（分组）不是应用，
   而挂靠（ADR 0092 的 `parent`）只能指向应用；按 0111/0121 的既定先例，
   入圈即去挂靠——保留 `parent` 而改 `group` 不会产生任何效果。

## 决策

1. **去挂靠入圈**：三个应用删除 `parent: embedded`，`group` 统一改为
   「电子信息」，与 embedded 同圈（领域圈成员即兄弟，ADR 0101，不画连线）。
   启动器零改动。
2. **校验放宽**：各自 `check.py` 的 parent 校验由「必须是 embedded」改为
   「不得声明 parent」；其余校验（id、端口、图标产物）不动。
3. **定位不变**：课程定位、内容与出处档位本次不动——三者仍是嵌入式系统设计师
   课程体系的实践课程，课程树文字指引关系照旧（ADR 0098/0121 决策 6 模式），
   只是启动器上的归属圈从挂靠圈换成领域圈。

## 后果

- 「电子信息」圈四成员：embedded、firmware、microcontroller、rtos；embedded
  的挂靠圈清空，ADR 0119 后果里「软设/嵌入式外圈」的成员清单随之再少三个。
- 「嵌入式程序设计」「硬件实验」「实时操作系统」三个名义分组不再存在（它们
  从未生成过胶囊，此番从 app.json 一并清掉）。
