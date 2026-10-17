---
id: T-001
title: gtkmm 前十章审查：工程一致性与官方示例
owner: cursor
status: done
priority: P1
depends: 
created: 2026-10-17 17:52
updated: 2026-10-17 18:11
---

## 目标
审查前十章在**工程与一致性**上有没有违背应用规则或留有疏失：官方示例镜像、演示/实验清单与课表的对账、模拟与真机配对、构建与检查。

## 做法
1. 在仓库根跑 `python scripts/check.py gtkmm`（只读性质的检查；如果它会写文件，先看脚本，只记录输出，不要提交产物），把输出摘要放进报告。
2. 对账：`content/demos.json`（demos/experiments/examples）与 `curriculum.json` 前十章的 `page_ref`/`theory_refs`/`translation_ref` 是否一一对得上；有无悬空引用、重复 id、前十章应有示例却没登记的情况。
3. 官方示例镜像：`exercise/` 中前十章对应示例是否与 `upstream/gtkmm-documentation/examples/book/` 逐字一致（用整目录 diff，规则见应用 ADR 0006）；`exercise/` 禁止被改。
4. 模拟与真机配对（应用 ADR 0001）：`src/simulations.tsx` 里每个模拟是否在 `demos.json` 有对应真机演示；演示是否遵守「一理论点一演示、≤150 行」，`--self-check` 协议是否具备（读 `demos/*/` 源码即可，不必编译）。
5. 前端/壳的明显疏失：`src/` 与 `src-tauri/` 里与前十章相关的实现是否违反「内容驱动 UI」「壳要薄」（按章手写整页、Rust 里写业务文案等）。
6. 教学规范对照（主仓库 `docs/TEACHING.md`、AGENTS.md 里的 ADR 0113 预测–运行）：前十章的演示/实验/观察题是否真的做到「先预测再运行」，哪些章只有文档没有演示与测验。

## 验收
`comms/gtkmm-review/artifacts/cursor/report.md` 存在，含 check 输出摘要、对账结果、镜像 diff 结论；P0/P1 发现全部带证据。完成后 `status T-001 review`，note 写报告路径与 P0/P1 条数。
共同约束：
- **只读审查**，不改 `guide/gtkmm/` 下任何文件，不提交 git。只在自己的 `comms/gtkmm-review/artifacts/<你的名字>/report.md` 写报告。
- 先读 `guide/gtkmm/AGENTS.md`、`guide/gtkmm/docs/decisions/` 全部 ADR 和根 `AGENTS.md`「跨应用教学规范」，以它们为尺子，不以个人偏好为尺子。
- 范围 = 课表 `guide/gtkmm/content/curriculum.json` 中 `order` 1–10 的章（chapter-introduction、chapter-installation、chapter-basics、changes-gtkmm3、changes-gtkmm4、chapter-button-widget、chapter-range-widgets、chapter-misc-widgets、chapter-container-widgets、chapter-listmodel）。
- 每条发现必须带**证据**（文件路径 + 块序号/行号 + 原文摘录）、**严重度**（P0 误导学习者 / P1 明显缺陷 / P2 可改进）和**建议改法**。没有证据的猜测不要写。证据不足就写「待查」。
- 不要重划结构、改章名、改 id（根 AGENTS.md「内容工作宁缺毋滥」）；结构性建议单列在报告末尾「结构建议」，由 leader 裁决。
- 报告要简洁：总体结论 3~5 句 + 按严重度排序的发现表 + 结构建议。不写八股。


## 进展记录
- [2026-10-17 18:08] claude-code：todo → review · leader 代交：cursor 报告已写（artifacts/cursor/report.md，P0=0 P1=3 P2=2），其 Shell 被 Claude 钩子注入阻断；check.py 全绿与 exercise↔upstream 整树 diff（28 目录仅 treeview 缺 meson.build，范围外）由 leader 补证，F1 已核实
- [2026-10-17 18:11] claude-code：review → done · leader 验收：关键发现已抽样核实
