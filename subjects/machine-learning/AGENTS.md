# Athena 机器学习基础 — 项目协作规则

本文档是 **`subjects/machine-learning` 独立应用** 的项目级指令，不依赖任何其他应用即可
完成开发、构建、学习与实验全流程。

仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。启动器通过
`app.json` 把本应用当独立进程拉起（ADR 0032），那不是运行本应用的前提。

## 定位

- **学习应用**（主仓库 ADR 0120）：人工智能课程路线原理线第一步——经典机器学习的
  直觉与实战：回归/分类/聚类、交叉验证、特征工程、sklearn 实战。目标是建立「从数据
  学规律」的直觉，为 deep-learning 铺路，不追求数学严谨性优先。
- **循序渐进**：承接本应用的是 python（工具链地基）；学完进 deep-learning（神经网络
  把这套直觉推深）。指引写在内容里，不引用对方路径或代码（ADR 0032）。
- **出处档位 open**（ADR 0089）：技术学习类，出处是默认习惯不做门禁；不凭印象伪造
  出处，AI 现场出题不计入掌握度。
- **学习方法原型（ADR 0113）**：主原型**机制模拟**——学习曲线、决策边界、交叉验证的
  折痕都摆出来先预测再看；辅**真做校验**：每章用 sklearn 在真实数据集上跑通一个完整
  建模流程。
- **实验形态**：实验在本机 Python 子进程真跑；应用只执行白名单内的预设命令（ADR 0091
  决策 3 同规）。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust），界面 React 18 + TypeScript + Vite。骨架阶段只有窗口与定位页；
  实验引擎随内容填充期落地，此后独立演进（ADR 0062）。
- **内容**：`content/course.json`（本目录唯一课表）。
- **进度**：SQLite，写入本应用自己的 `progress/learning.db`（随仓库走，ADR 0053），
  知识点 ID 前缀 `ml.`。
- 端口 **1506**（strictPort）；进程/二进制 `athena-machine-learning`。

## 内容与教学分层

- **内容驱动 UI**（ADR 0058）；骨架阶段课表节全部 `status: placeholder`。
- **随堂练习与考核**（ADR 0002）：完成度只由作答按正确率写入；题量以覆盖为准（ADR 0096）。
- **实验给骨架**（ADR 0003）：学员只补 `TODO`，不从零写整程序。

## 开发与验证

```sh
launcher open machine-learning
python3 scripts/check.py          # 骨架阶段默认结构校验
python3 scripts/check.py --full   # 追加前端构建与 cargo check
```

环境变量 `ATHENA_MACHINE_LEARNING_ROOT` 可强制指定应用根目录（含 `content/`）。
