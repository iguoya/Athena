# gtkmm-demo 舱：gtkmm 预测–运行演示补齐

起因：`comms/gtkmm-review` 审查指出第 3 章起只有第 6 章有「模拟 + 真机演示」，主原型「预测–运行」
（应用 AGENTS.md）在其余章落空。本舱按「先第 3 章，再第 9 章布局」的顺序逐个补演示。

分工同 `gtkmm-quiz`：leader（claude-code）写任务书、集成进 `guide/gtkmm/`（课表、`demos.json`、
`src/simulations.tsx`、`demos/`）、编译验收并提交；worker 只在 `artifacts/<名字>/` 里写草稿，
**不改 `guide/gtkmm/` 下任何文件、不提交 git**。样板：`guide/gtkmm/demos/buttons/`、
`guide/gtkmm/src/simulations.tsx`、课表第 6 章 `gtkmm.buttons.*`。
