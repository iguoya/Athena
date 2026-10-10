# ADR 0121：design-patterns 去挂靠入「程序设计」圈，以模式与程序组织为主，软考降为专题

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「以掌握设计模式 程序代码组织本身为主 教材尽量
  有所本 不要过分自由发挥 有权威材料做支撑」「通过软考知识赠品 或者说是专题 软考
  出题 尽量出原题」「将设计模式 移出 软考的 程序设计师 淡化软考对设计模式的影响
  设计模式 放到 程序设计分组下面」）
- 关系：修订 [ADR 0103](0103-practice-courses-as-attached-subapps.md) 决策 2 表格
  design-patterns 行的挂靠与定位（原文不改）；入圈即去挂靠沿
  [ADR 0111](0111-programming-group.md) 的 linux 先例；出处档位按
  [ADR 0089](0089-source-tiers-by-app-nature.md) 的判据重新归类；
  [ADR 0119](0119-detach-is-exclusive.md) 后果里「软设外圈只剩 database、
  design-patterns 与 c-gui-lab」随之变为 database 与 c-gui-lab

## 背景

1. ADR 0103 把 design-patterns 从素材坑转正为「软设第 7 章的实践课程」，`parent:
   software`。转正后的第一批内容按这个定位写：每个模式配「软考考点」，图谱首页、
   简介都以软设第 7 章开头。
2. tiger 明确了真实意图：这门课教的是**设计模式与程序代码组织本身**，软考只是附带
   收获。软考对内容的牵引要淡化：考试知识集中成一个专题，专题里的题尽量用真题原题。
3. 同时要求教材「有所本」：讲解以权威材料为依据，不自由发挥。可用的权威材料：
   GoF《Design Patterns: Elements of Reusable Object-Oriented Software》（1994）是
   23 个模式的原始出处；《软件设计师教程（第 5 版）》§7.3 按 GoF 体例（意图、结构、
   参与者、适用性）逐一转述了 23 个模式，OCR 全文已在 software 应用的
   `content/textbooks/swd5ed/` 里；Refactoring.Guru 是公认的图解教程。
4. 启动器机制（ADR 0092、0111）：挂靠节点画在挂靠者外一圈、不进领域圈。要出现在
   「程序设计」圈里，就得去掉 `parent`。

## 决策

1. **去挂靠入圈**：`subjects/design-patterns/app.json` 删除 `parent: software`，
   `group` 由「设计模式」改为「程序设计」，与 gtkmm、linux 同圈（领域圈成员即兄弟，
   ADR 0101，不画连线）。启动器零改动。
2. **定位**：以设计模式与程序代码组织为主线的学习应用。章节骨架是 UML 读图 →
   设计原则 → 创建型 → 结构型 → 行为型；讲解依据按「GoF 原著 → 软设教程 §7.3 →
   Refactoring.Guru」取材并逐节标注，不凭印象写意图与结构。
3. **软考降为专题**：新增「软考专题」一章，集中放真题原题（verbatim，年份与题号来自
   真实试卷页面，严禁凭记忆编造）与考法说明。模式讲解里已有的「软考考点」提示
   保留，但在界面上降级为可折叠的次要信息（ADR 0054：淡化，不删）。
4. **延伸层**：「模式的现状：批判、实证与 2026 视角」从 UML 章移到「现代工程的程序
   组织写法」章；「非面向对象世界的模式」「现代工程的程序组织写法」两章标为延伸层，
   图谱上与主线区分。知识点 id 不变。
5. **出处档位改为 `open`**（技术学习类）：本应用的学习成果不对应外部考试，按 0089
   的判据归 open——出处是默认习惯，不做仓库级门禁。软考专题的题例外：由本应用
   `scripts/check.py` 自己检查，专题里的每道题必须带 `verbatim` 出处与卷号题号。
6. **与 software 的关系降为内容指引**：软设第 7 章仍可以指引学习者来这里做模式实验，
   以课程树文字表达（ADR 0098 模式），无挂靠连线。

## 后果

- 「程序设计」圈三成员：gtkmm、linux、design-patterns；软设外圈的挂靠子应用减去
  design-patterns。
- 本应用 `check.py` 的 parent 校验改为「不得有 parent」，并新增软考专题的原题出处检查。
- 根 AGENTS.md、docs/REPOSITORY.md、README、docs/TEACHING.md 的应用清单同步；
  software 的 content-plan 中「第 7 章归 design-patterns」改为指引表述。
