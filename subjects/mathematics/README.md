# 数学学习

数学学科的学习应用（Tauri 2 + React 前端，Python sidecar 引擎）：以「用数学认识、
改造现实」为目标、以研究生入学考试数学二为覆盖约束（ADR 0003、0007），按课表组织
章节与练习轨，实验与计算由本地 Python 引擎承担，进度记在 `progress/learning.db`。

- 启动：`launcher open mathematics`（`app.json` 声明；sidecar 虚拟环境由 dev
  准备步骤建立，见 `engine/`）。
- 验证：`python scripts/check.py`（内容契约、引擎自检、前端与 Rust 检查）。
- 规则与教学约束见 `AGENTS.md`，取舍记录见 `docs/decisions/`。
