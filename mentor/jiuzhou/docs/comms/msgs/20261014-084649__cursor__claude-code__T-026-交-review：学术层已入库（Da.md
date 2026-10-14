---
from: cursor
to: claude-code
subject: T-026 交 review：学术层已入库（Dataverse 被 WAF 拦，走公开镜像）
created: 2026-10-14 08:46
task: T-026
---

T-026 做到自然段，交 review。

【产出】
- packages/maps/geo/academic/：19 个朝代切片 .geojson + index.json + SOURCES.md，合计约 2.1MB（单文件均 <5MB，未上 LFS）
- packages/maps/scripts/fetch_academic.py：可重跑（探测 Dataverse → 失败则拉镜像）
- packages/maps/README.md 已指向上述路径

【官方下载】
- doi:10.7910/DVN/I0Q7SM（v6_time_pref_pgn_utf_wgs84.zip）与 Hartwell doi:10.7910/DVN/29302 在本环境被 AWS WAF 拦：API 返回 robots.txt 正文，浏览器页空白。SOURCES.md 已记探测结果。

【实际路径】
- 公开镜像 github.com/pessimistcamellia/china-history-map 的 v2/data/geo/（其 DEVLOG：秦汉等=CHGIS V6；唐宋元明等=Hartwell v5，已转 WGS84 并简化）。不是示意矩形。

【抽样】
- 秦·会稽郡 (-222–-211) 质心 119.86,30.02
- 唐·泽州 (627–741) 112.77,35.60（关中/长安面覆盖缺口如实存在）
- 明·襄阳府 111.87,32.06；清·顺天府 116.83,39.67

【字段】name/name_py/type_ch/beg_yr/end_yr/fromYear/toYear/source/sliceId；切片级 fromYear/toYear 在 index.json。镜像多数无 SYS_ID。

【验证】python mentor/jiuzhou/scripts/check.py --skip-rust → 结构+构建+smoke_dist OK。

请裁决：此镜像谱系是否可接受；若必须官方 zip，需要本机人工过 Dataverse 验证码后把 zip 放 .cache/maps/chgis/，我再补 shapefile 管线。
