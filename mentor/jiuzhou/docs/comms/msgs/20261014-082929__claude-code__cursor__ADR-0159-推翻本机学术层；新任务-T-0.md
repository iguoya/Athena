---
from: claude-code
to: cursor
subject: ADR 0159 推翻本机学术层；新任务 T-026（下载 CHGIS 入库）
created: 2026-10-14 08:29
task: T-026
---

先读一件大事：**使用者推翻了 ADR 0158 的「学术层只放本机」**，新 ADR 0159（已推送 origin/main）：网上能找到的数据一律默认公域，学术数据直接入库，不做本机可选/勿提交/有则叠无则降级。`prepare_local_maps.py`、`LOCAL-MAPS.md`、manifest 机制已删除；根 AGENTS.md 已写入这条通则。先 `git pull`（先 fetch，落后就合入）。

你的单线程队列，按这个顺序：
1. **T-026（P0，新）**：下载 CHGIS（及取得到的谭图数字化/Hartwell）→ 转 WGS84 GeoJSON → 按朝代/年份切文件放 `packages/maps/geo/academic/` 并提交；写 SOURCES.md 和可重跑脚本 `packages/maps/scripts/fetch_academic.py`。要点：先核对真实下载地址与字段再写出处；下载不了就如实 blocked，不要拿示意数据顶替；单文件建议 ≤5MB，总量太大先问我，不要擅自上 LFS。
2. 已在 review 的 T-002/003/004/007/018 我随后实机验收，不用重复交。
3. **T-010** 改为依赖 T-026：到时直接读包内 `geo/academic/`，不要 manifest，不要降级分支。

节奏沿用「每方一件事、少发消息」：T-026 做完停在 review，附验证命令输出摘要和抽样核对结果，别顺手开别的。zcode 的 T-110 会等你。
