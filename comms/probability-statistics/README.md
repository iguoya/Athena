# probability-statistics 舱

`self-study/probability-statistics`（概率论与数理统计（工），13174 / 02197）的立项协作舱，
依据 [ADR 0178](../../docs/decisions/0178-probability-statistics-self-study.md) 决策 5 开设。
应用壳与首批内容由 claude-code（leader，立项者）负责；教材与考纲核对、历年真题整卷采集
通过本舱派给 worker。

## 角色与文件归属

| 成员 | 角色 | 名下路径 |
|---|---|---|
| claude-code | leader，壳与首批内容 | `self-study/probability-statistics`、`docs/decisions/0178-*.md` |
| zcode | worker：教材考纲核对（T-9xx 派发） | `content/exams/`（真题整卷）、`artifacts/zcode/` |
| cursor | worker：真题整卷采集 | `content/exams/`（真题整卷）、`artifacts/cursor/` |

- worker 不改课表、知识点与节内容；只写自己名下的 `content/exams/` 与 `artifacts/<名>/`。
- 真题整卷格式见 `self-study/linear-algebra/content/exams/README.md`（先例）。
- 任务号段：claude-code 占 T-9xx，zcode T-0xx，cursor T-1xx。

## 已有材料

- `artifacts/zcode/SUGGESTIONS.md`：编写层建议（目录底稿、考纲边界、可视化清单、
  数值复核流程等），zcode 在立项前已备好，从 self-study 舱迁入。
