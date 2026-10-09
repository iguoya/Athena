# ADR 0093：取消实践面板，nas-admin 隐藏，魔方挂靠 C++

- 日期：2026-10-09
- 状态：已接受（tiger 直接指示）
- 关系：扩展 [ADR 0092](0092-launcher-tree-attach-and-softcert-rename.md) 的挂靠
  体系与面板归属规则；废止 [ADR 0083](0083-launcher-mind-map.md) 的「实践面板」
  分区；实现归启动器当前开发线

## 背景

tiger 指示（2026-10-09）：不要再有「实践面板」的概念；NAS 后台管理取消显示——
它不是桌面应用；PocketCube 2 阶魔方挂靠在 C++ 的子节点上。

现状核实：`pocket-cube` 是用 **C++** 演示与操作 2 阶魔方的项目，正是 C++ 学以
致用的实践出口；`nas-admin` 是跑在软路由（ImmortalWrt）上的 Flask-AppBuilder +
PostgreSQL **Web 服务端项目**，不是桌面应用——启动器按桌面应用给它一个图块
本就名不副实。ADR 0092 落地后实践面板只剩 nas-admin 一个应用，二分面板失去
存在理由。

## 决策

1. **取消实践面板。** 启动器只保留学习应用面板（思维导图）；应用清单仍是
   `subjects/` + `practice/` 两目录全量（ADR 0046 的发现机制不变），展示位置
   一律由 `group`（领域圈）与 `parent`（挂靠层级）声明驱动，不再按目录二分。
   ADR 0083 中「实践面板仍是网格」一句废止。
2. **`app.json` 新增可选字段 `hidden`**（布尔，缺省 false）：为 true 时启动器
   不显示该应用——不出现在任何面板、`list --json` 仍返回并带 `hidden` 标记
   （脚本与依赖方可见）；`open`/`stop` 与 dev 编排照常可用。隐藏是显示层的
   事，不是下线。
3. **`nas-admin` 设 `hidden: true`**：它是软路由上的 Web 服务端项目，不是桌面
   应用，启动器不再给它图块。它作为驾考进度仪表盘的宿主服务（ADR 0069）照常
   运行，`dev` 编排与部署脚本不受影响。
4. **`pocket-cube` 挂靠 cpp**（`pocket-cube.parent = "cpp"`，并补
   `group: "编程语言"`）：魔方是 C++ 学以致用的实践出口，与 c-gui-lab 挂靠
   softcert 同语义；思维导图上画在 cpp 外一圈。

## 后果

- 启动器 GUI 删除实践面板分区与 `practice` 独立状态通道，清单聚合与指纹逻辑
  相应简化；`hidden` 过滤在发现层做。
- 实践面板概念消失后，`practice/` 目录继续存在（ADR 0060 的意图分类不变），
  只是不再是展示分区。
- nas-admin 的入口改为直接访问其 Web 地址或命令行编排，启动器不再承担。
