---
id: T-101
title: gtkmm 前十章审查：译文忠实度与术语
owner: zcode
status: done
priority: P1
depends: 
created: 2026-10-17 17:52
updated: 2026-10-17 18:11
---

## 目标
审查前十章**译文**对官方原文的忠实度、术语一致性与表达质量，找出误译、漏译、过度意译、术语不统一。

## 做法
1. 原文基准：`guide/gtkmm/upstream/gtkmm-documentation`（DocBook）；章节快照 `guide/gtkmm/content/chapters/<章>/<节>.json`，`blocks[].zh` 是译文，`code` 块译文恒为空属正常。
2. 术语表：`guide/gtkmm/content/vocab.json`；对照检查译文是否按表用词、同一英文术语前后是否译法一致。
3. 逐章抽查（每章至少读完全部 `blocks`，不能只抽开头）：误译（含技术含义反了）、漏译（`zh` 为空但状态不是 pending）、增删信息、中英文混杂不当、API 名/类名被误译、与代码块内容不符的叙述。
4. 特别注意 `translated` 与 `pending` 状态是否与实际译完度相符（curriculum 里 changes-gtkmm3/4、misc、container、listmodel 标 pending 但已有大量 zh，说明各自完成度）。
5. 可用脚本 `guide/gtkmm/scripts/check.py`（只读运行）核对一致性，但结论要靠你自己读文本。

## 验收
`comms/gtkmm-review/artifacts/zcode/report.md` 存在，覆盖 10 章，每章至少有结论一行；P0/P1 发现全部带证据。完成后 `status T-101 review`，note 写报告路径与 P0/P1 条数。
共同约束：
- **只读审查**，不改 `guide/gtkmm/` 下任何文件，不提交 git。只在自己的 `comms/gtkmm-review/artifacts/<你的名字>/report.md` 写报告。
- 先读 `guide/gtkmm/AGENTS.md`、`guide/gtkmm/docs/decisions/` 全部 ADR 和根 `AGENTS.md`「跨应用教学规范」，以它们为尺子，不以个人偏好为尺子。
- 范围 = 课表 `guide/gtkmm/content/curriculum.json` 中 `order` 1–10 的章（chapter-introduction、chapter-installation、chapter-basics、changes-gtkmm3、changes-gtkmm4、chapter-button-widget、chapter-range-widgets、chapter-misc-widgets、chapter-container-widgets、chapter-listmodel）。
- 每条发现必须带**证据**（文件路径 + 块序号/行号 + 原文摘录）、**严重度**（P0 误导学习者 / P1 明显缺陷 / P2 可改进）和**建议改法**。没有证据的猜测不要写。证据不足就写「待查」。
- 不要重划结构、改章名、改 id（根 AGENTS.md「内容工作宁缺毋滥」）；结构性建议单列在报告末尾「结构建议」，由 leader 裁决。
- 报告要简洁：总体结论 3~5 句 + 按严重度排序的发现表 + 结构建议。不写八股。


## 进展记录
- [2026-10-17 17:54] zcode：todo → doing
- [2026-10-17 18:08] zcode：doing → review · 报告：comms/gtkmm-review/artifacts/zcode/report.md（P0×3、P1×13、P2×10，10 章全覆盖）。check.py 只读运行全绿；英中对照底稿在 artifacts/zcode/dump/。P0：gtkmm4 二进制兼容译反、entry leave 信号段被替换、scrollbar 段整段自造。系统性问题：widget 四种译法混用、sync_upstream 剥标签吞正文尖括号实体（全书 31 段）、zh 系统性丢链接、heading/figure 译文口径三方不一致（已单列结构建议待 leader 裁决）。
- [2026-10-17 18:11] claude-code：review → done · leader 验收：关键发现已抽样核实
