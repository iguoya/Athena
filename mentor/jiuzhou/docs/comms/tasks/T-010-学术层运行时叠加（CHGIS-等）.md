---
id: T-010
title: 学术层运行时叠加（CHGIS 等）
owner: cursor
status: todo
priority: P1
depends: 
created: 2026-10-13 22:43
updated: 2026-10-13 22:43
---
## 目标
ADR 0158 的承诺：本机学术层优先，有则叠、无则静默降级。

## 做法
读 `.cache/maps/manifest.json`（`packages/maps/scripts/prepare_local_maps.py` 已写出）：每个 GeoJSON 图层按属性里的名称与起止年筛选（字段名容错：`NAME_CH/name`、`BEG_YR/beg/from`、`END_YR/end/to`），当前年份命中就叠在示意疆域之上；点选政区弹卡片（名称、存续年份、来源）。**无数据时静默降级，不报错、不弹提示。**

## 验收
把任意带 `name/from/to` 的小 GeoJSON 放进 `.cache/maps/academic/`，重启后能按年份显示并点选；删掉后界面无任何痕迹。

## 进展记录
