# Athena 大模型微调与部署 — 项目协作规则

本文档是 **`subjects/llm-finetune` 独立应用** 的项目级指令，不依赖任何其他应用即可完成
开发、构建、学习与实验全流程。

仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。启动器通过
`app.json` 把本应用当独立进程拉起（ADR 0032），那不是运行本应用的前提。

## 定位

- **学习应用**（主仓库 ADR 0120）：人工智能路线原理线的终点——数据准备、LoRA/QLoRA
  微调、量化、ollama/vLLM 本地推理、GPU 基础与服务化。目标：打开模型这个盒子，把它
  改成自己的、部署到自己手上。
- **边界**：本应用打开模型改参数，不做应用层（那是 llm-app 的主场）。
- **循序渐进**：先修是 deep-learning（训练与反向传播）与 llm-app（应用视角知道为什么
  要微调）。指引写在内容里，不引用对方路径或代码（ADR 0032）。
- **出处档位 open**（ADR 0089）：技术学习类；不凭印象伪造出处，AI 现场出题不计入掌握度。
- **学习方法原型（ADR 0113）**：主原型**真做校验**——每章把一个真实的小模型微调、量化、
  部署到本地跑通。
- **实验形态**：实验在本机 Python 子进程真跑；应用只执行白名单内的预设命令（ADR 0091
  决策 3 同规）。GPU 资源不足的实验给 CPU 降级路径并如实标注。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust），界面 React 18 + TypeScript + Vite。骨架阶段只有窗口与定位页；
  实验引擎随内容填充期落地，此后独立演进（ADR 0062）。
- **内容**：`content/course.json`（本目录唯一课表）。
- **进度**：SQLite，写入本应用自己的 `progress/learning.db`（随仓库走，ADR 0053），
  知识点 ID 前缀 `finetune.`。
- 端口 **1509**（strictPort）；进程/二进制 `athena-llm-finetune`。

## 内容与教学分层

- **内容驱动 UI**（ADR 0058）；骨架阶段课表节全部 `status: placeholder`。
- **随堂练习与考核**（ADR 0002）：完成度只由作答按正确率写入；题量以覆盖为准（ADR 0096）。
- **实验给骨架**（ADR 0003）：学员只补 `TODO`，不从零写整程序。

## 开发与验证

```sh
launcher open llm-finetune
python3 scripts/check.py          # 骨架阶段默认结构校验
python3 scripts/check.py --full   # 追加前端构建与 cargo check
```

环境变量 `ATHENA_LLM_FINETUNE_ROOT` 可强制指定应用根目录（含 `content/`）。
