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
学术层数据直接入库（ADR 0159，取代 0158 的「本机可选」）：应用读包内数据，按年份叠在示意疆域之上。

## 做法
读 `packages/maps/geo/academic/` 下的 GeoJSON（构建期打包，不再有 manifest、环境变量或 `.cache` 路径；`prepare_local_maps.py` 已删除）：每个图层按属性里的名称与起止年筛选（字段名容错：`NAME_CH/name`、`BEG_YR/beg/from`、`END_YR/end/to`），当前年份命中就叠在示意疆域之上；点选政区弹卡片（名称、存续年份、来源）。不写「有则叠、无则降级」的分支：目录里没有对应年层的时段，用 `territories.json` 示意帧作底色即可。

## 验收
把任意带 `name/from/to` 的小 GeoJSON 放进 `packages/maps/geo/academic/`，构建后能按年份显示并点选。

## 进展记录
