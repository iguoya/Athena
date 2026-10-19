# pocket-cube-solver 舱：二阶魔方教材整改

起因：10.0.0 发版后对 `programming/pocket-cube-solver` 做教材审查，发现三个缺口：

1. 题库有明显的猜题捷径：29 题里 20 题答案在第 2 个位置，26 题正确项是最长的选项。
2. 应用声明的辅原型是「预测–运行」，可 29 题全是概念选择题，没有一道让读者先猜一个状态再看回放。
3. 每章只有「讲解 + 打开程序 + 选择题」，没有给读者动手改一处、先猜后看的小实验（ADR 0059、TEACHING 的学习闭环）。

分工同 `gtkmm-demo`：leader（claude-code）写任务书、改 `programming/pocket-cube-solver/` 下的壳与内容、编译验收并提交；
worker（cursor）**只在 `artifacts/cursor/` 里写草稿和证据，不改 `programming/` 下任何文件、不提交 git**。
内容的取舍标尺见该应用 `AGENTS.md` 与仓库 ADR 0129：宁缺毋滥，已有 `id` 不改嫁。
