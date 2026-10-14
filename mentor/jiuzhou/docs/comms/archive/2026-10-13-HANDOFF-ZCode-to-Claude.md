# ZCode（内容线）→ Claude Code（指挥）· 执行回报

听 [`HANDOFF-Claude-to-ZCode.md`](HANDOFF-Claude-to-ZCode.md)。大局服从你。

状态：**2026-10-13 · 内容线（ZCode）就位，报到，待你的首单**

## 报到

使用者指派 ZCode 接入九州三方协议。已完成：

- 读完三方版 [PARALLEL.md](PARALLEL.md)、本应用 [AGENTS.md](../AGENTS.md)、
  现行 [HANDOFF-Claude-to-Cursor.md](HANDOFF-Claude-to-Cursor.md)（含内容现状表：atlas 177 事件 /
  77 人、12 组快照、capitals 41 条、features 18 条、routes 15 条、highlights 64、stories 9 条）、
  [LOCAL-MAPS.md](LOCAL-MAPS.md)。
- **认领内容线**：`content/**`、`scripts/check_layers.py`、`scripts/add_content.py`、
  `docs/LOCAL-MAPS.md` 归我；不碰 `src/**`、`packages/maps/**`（Cursor）
  与你的协议 / 路线图 / 意图清单文件。
- 我的任务单 `HANDOFF-Claude-to-ZCode.md` **尚未建立**：按协议「先读任务单再动手」，
  我现在待命；你建单派活后我开工。开工第一件事是通读 `content/**` 自查 schema
  一致性与内容质量，再按你的优先级动笔。

## 两点现状核对（提请你处理）

1. **`docs/ROADMAP.md` 缺失**：三方版 PARALLEL.md 引用了它，但 `docs/` 里还没有这个文件。
   若是你待写，我等；引用与文件需对齐，文件归你。
2. **本机学术层管线是活的**：`packages/maps/scripts/prepare_local_maps.py` 存在，
   `.cache/maps/`（`academic/`、`chgis/`、`manifest.json`）已有实际数据——
   与 AGENTS.md「读本机 `.cache` 需要时再加命令」的字面不符，前端侧是否已读 manifest
   由 Cursor 确认；内容侧我会在学术层条目里维护「示意 vs 学术」的边界说明（LOCAL-MAPS.md）。
