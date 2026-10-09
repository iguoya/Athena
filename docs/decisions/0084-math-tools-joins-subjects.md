# ADR 0084：math-tools 从 `practice/` 迁入 `subjects/`，作为数学学习的配套工具

- 日期：2026-10-03
- 状态：已接受；注记（2026-10-10）：决策 3 的「声明 `related: ["mathematics"]`」
  已由 [ADR 0101](0101-domain-circle-siblings-no-links.md) 收回——兄弟关系由同一
  `group`「数学」表达，圈内不再画特意连线
- 修订：[ADR 0060](0060-subjects-and-practice.md) 对 `math-tools` 的归类。0060 的分法（按意图分
  `subjects/` 与 `practice/`）不变，原文不改
- 关系：延续 [ADR 0083](0083-launcher-mind-map.md)（启动器按 `group` / `related` 画关系）；
  构建隔离仍守 [ADR 0032](0032-independent-apps-launched-as-processes.md)、
  [ADR 0062](0062-apps-own-their-constraints.md)

## 背景

ADR 0060 按意图分：`subjects/` 是课程学科，`practice/` 是「做能跑的东西」的项目应用。`math-tools`
（矩阵实验室、函数绘图、练习纲要）最初放在 `practice/`：它不教会人什么、不建进度库、教学规范不生效。

但它实际是**数学学习的配套工具**：和 `mathematics` 同属一个领域，使用者想在启动器里把它和
数学学习放在一起、连起来。`practice/` 面板里的项目彼此独立，没有分组和关系可画（ADR 0083）。
`math-tools` 自己的 `AGENTS.md` 也写着：边界变化要先立 ADR 再动。

## 决策

1. **`practice/math-tools` 迁入 `subjects/math-tools`。** `id`、进程名 `athena-math-tools`、端口 1451、
   技术栈都不变；迁移用 `git mv`，历史保留。
2. **归类判据。** 根 `AGENTS.md` 的主问题是「要不要教会人什么、要不要证明学习者进步了」：`math-tools` 两样
   都不要，所以它**不是学习应用**，不建进度库、教学规范不生效；它只呈现和计算、供使用者随手用，
   归**图谱 / 参考类**（`polaris` 是同一类）。
3. **启动器里的位置。** 作为学习应用面板的一员，`group` 与 `mathematics` 同为「数学」，
   并在自己的 `app.json` 里声明 `related: ["mathematics"]`。
4. **不是先例。** `practice/` 里的项目仍按 0060 判断。一个工具要归 `subjects/`，须同时满足：
   它是某门课程学科的配套，且需要在启动器里和该学科关联。不满足就留在 `practice/`。
5. **边界不变。** `math-tools` 与 `mathematics` 没有代码、路径或配置上的引用（共用的只有规范），
   各自独立构建、独立运行。

## 后果

- `practice/` 面板只剩 `nas_admin`、`pocket_cube`。
- `math-tools` 里的文档把「实践应用」「`--root practice`」改成新的说法：`launcher open math-tools`。
- 根 `AGENTS.md` 与 `docs/REPOSITORY.md` 的目录说明同步，`CHANGELOG` 里的历史记录不改。
