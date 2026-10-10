# Athena 深度学习与 PyTorch — 项目协作规则

本文档是 **`subjects/deep-learning` 独立应用** 的项目级指令，不依赖任何其他应用即可
完成开发、构建、学习与实验全流程。

仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。启动器通过
`app.json` 把本应用当独立进程拉起（ADR 0032），那不是运行本应用的前提。

## 定位

- **学习应用**（主仓库 ADR 0120）：人工智能路线原理线的主干——张量与自动微分、训练
  循环、CNN/RNN、**注意力与 Transformer**、预训练-微调范式，PyTorch 实战。它是大模型
  的底层地基。
- **循序渐进**：向前承接 machine-learning（经典模型直觉）；向后通 llm-finetune（打开
  大模型的盒子）；llm-app 从本应用拿走 Transformer 与预训练-微调范式的概念底座。指引
  写在内容里，不引用对方路径或代码（ADR 0032）。
- **出处档位 open**（ADR 0089）：技术学习类；不凭印象伪造出处，AI 现场出题不计入掌握度。
- **学习方法原型（ADR 0113）**：主原型**预测–运行**——训练曲线、梯度流、注意力的权重
  分布先预测再单步揭示；辅**机制模拟**。
- **实验形态**：实验在本机 Python 子进程真跑；应用只执行白名单内的预设命令（ADR 0091
  决策 3 同规）。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust），界面 React 18 + TypeScript + Vite。骨架阶段只有窗口与定位页；
  实验引擎随内容填充期落地，此后独立演进（ADR 0062）。
- **内容**：`content/course.json`（本目录唯一课表）。
- **进度**：SQLite，写入本应用自己的 `progress/learning.db`（随仓库走，ADR 0053），
  知识点 ID 前缀 `dl.`。
- 端口 **1507**（strictPort）；进程/二进制 `athena-deep-learning`。

## 内容与教学分层

- **内容驱动 UI**（ADR 0058）；骨架阶段课表节全部 `status: placeholder`。
- **随堂练习与考核**（ADR 0002）：完成度只由作答按正确率写入；题量以覆盖为准（ADR 0096）。
- **实验给骨架**（ADR 0003）：学员只补 `TODO`，不从零写整程序。

## 开发与验证

```sh
launcher open deep-learning
python3 scripts/check.py          # 骨架阶段默认结构校验
python3 scripts/check.py --full   # 追加前端构建与 cargo check
```

环境变量 `ATHENA_DEEP_LEARNING_ROOT` 可强制指定应用根目录（含 `content/`）。
