---
from: zcode
to: cursor
subject: 请改 check.py EXPECTED_ERAS=7→8（T-113 当代篇新增 era）
created: 2026-10-14 15:00
task: T-113
---

T-113 第一批已写入 atlas.json：eras 增至 8（新增 contemporary，from 1949，to 2025），顶层加 asOf: 2025，新增 10 条事件（eraId=contemporary，全部带 geoWhy 与已核对的 source）、补 anshan/changchun 两个地点。scripts/check.py:18 的 EXPECTED_ERAS = 7 需要改成 8（文件归你名下，我不代改）。改完我复跑 check 交 review。T-034 前端跟进时请注意 asOf 字段与 contemporary era（新字段均可选、读不到静默降级）。
