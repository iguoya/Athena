# 数学罗盘

数学学习导引：给五个数学学习应用（数学学习、Selinger 精读、Siefken 精读、SymPy 教程、Octave
手册）排一条先易后难的推荐路径，写清每一站的学习目的、掌握要点与取舍；两本线代书给出明确
选法；高数缺口如实写明。只指路，不教课、不判分、不建进度库（图谱/参考类，主仓库 ADR 0174）。

- 启动：`launcher open mathematics-compass`（`app.json` 声明，Tauri 2 + React 薄壳）。
- 验证：`python scripts/check.py`。
- 内容在 `content/guide.json`（字段含义见文件头 `_`）；规则与核对义务见 `AGENTS.md`。
