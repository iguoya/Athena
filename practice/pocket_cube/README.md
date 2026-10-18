# 2 阶魔方（旧版）

> 旧版，供参考。会求解、分章讲解的新应用见 [`programming/pocket-cube-solver`](../../programming/pocket-cube-solver)（仓库 ADR 0169）。

GTK4 / gtkmm 的 2 阶魔方练习应用（Meson 构建）：3D 视图与拓扑图展开已实现，
打乱与求解算法在开发中（见 `AGENTS.md`）。

- 启动：`launcher open pocket-cube`（`app.json` 声明）。
- 验证：`python scripts/check.py`。
- 项目应用不建进度库、不受教学规范约束（ADR 0060）。
