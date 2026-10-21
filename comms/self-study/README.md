# self-study 舱：自考数学教材（ADR 0175）

主题：自考本科数学三门课（linear-algebra、advanced-mathematics、规划中的 probability-statistics）
的教材与真题建设。背景见仓库级 [ADR 0175](../../docs/decisions/0175-self-study-math-exam-apps.md)。

## 分工

- **zcode（leader）**：内容与应用的所有决定——`self-study/linear-algebra`、
  `self-study/advanced-mathematics` 的节内容、知识点、界面与结构；任务拆分与验收。
- **cursor（worker）**：真题整卷采集入库（`content/exams/`，格式见各应用该目录 README）、
  教材目录核对（产物交 `comms/self-study/artifacts/`）。**不改节内容、不改前端、不改文档**；
  建议发消息给 leader。

## 文件归属

| 路径 | 谁 |
|---|---|
| `self-study/*/content/sections/`、`content/knowledge.json`、`content/curriculum.json`、`src/`、`docs/` | zcode |
| `self-study/*/content/exams/` | cursor（按目录 README 的格式与录入规则） |
| `comms/self-study/artifacts/` | 各自以自己任务号为子目录 |
| `tasks/`、`msgs/`、`BOARD.md` | 按 comms/README.md 通用规则 |
