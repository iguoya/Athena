# ADR 0124：software 去挂靠入「程序设计」圈

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「软件设计师 也挂靠程序设计下面」）
- 关系：修订 [ADR 0102](0102-exam-apps-as-top-level-groups.md) 中 software 的
  领域圈归属（顶层大类地位与课程本体承载不变，[ADR 0118](0118-heavier-exam-owns-course-body.md)）；
  「入圈即去挂靠」沿 [ADR 0111](0111-programming-group.md)、
  [ADR 0121](0121-design-patterns-to-programming-group.md)、
  [ADR 0123](0123-embedded-practice-subapps-to-electronic-info.md) 先例

## 背景

1. software（软件设计师）的 `group` 是「计算机」，在启动器导图里单独占一个
   单应用领域胶囊；它同时是 database 的挂靠者（ADR 0092）。
2. tiger 要求把它也放到「程序设计」圈——那里已有 gtkmm、linux、design-patterns
   （ADR 0121）。

## 决策

1. `subjects/software/app.json` 的 `group` 由「计算机」改为「程序设计」；
   software 本无 `parent`，无挂靠可去。
2. database 的挂靠（`parent: software`）不变：database 仍画在 software 外一圈，
   挂靠关系与领域圈归属正交（ADR 0092、0119）。
3. 定位与出处档位不变：software 仍是软考大类应用、课程本体承载者（ADR 0118），
   出处档位照旧按考试类强制。

## 后果

- 「程序设计」圈四成员：gtkmm、linux、design-patterns、software；「计算机」
  单应用胶囊消失。
- 软考大类应用不再各自占一个领域胶囊（cs408 的「计算机」圈只剩其本体，
  见 ADR 0102 的成员清单一并收窄到 cs408 自身）。
