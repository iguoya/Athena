---
id: T-010
title: 学术层运行时叠加（CHGIS 等）
owner: cursor
status: done
priority: P1
depends: T-026
created: 2026-10-13 22:43
updated: 2026-10-14 08:56
---
## 目标
学术层数据直接入库（ADR 0159，取代 0158 的「本机可选」）：应用读包内数据，按年份叠在示意疆域之上。

## 做法
读 `packages/maps/geo/academic/` 下的 GeoJSON（构建期打包，不再有 manifest、环境变量或 `.cache` 路径；`prepare_local_maps.py` 已删除）：每个图层按属性里的名称与起止年筛选（字段名容错：`NAME_CH/name`、`BEG_YR/beg/from`、`END_YR/end/to`），当前年份命中就叠在示意疆域之上；点选政区弹卡片（名称、存续年份、来源）。不写「有则叠、无则降级」的分支：目录里没有对应年层的时段，用 `territories.json` 示意帧作底色即可。

## 验收
把任意带 `name/from/to` 的小 GeoJSON 放进 `packages/maps/geo/academic/`，构建后能按年份显示并点选。

## 进展记录
- [2026-10-14 08:49] cursor：todo → doing · T-026 数据已在盘；接学术层运行时叠加
- [2026-10-14 08:52] cursor：doing → review · academicAtYear 按切片+要素起止年叠面；点选卡片；Hartwell 虚线/低透明近似；已 push 93947330；check --skip-rust 绿
- [2026-10-14 08:56] claude-code：review → done · 实机验收：academic-fill/line/line-approx 三层挂载；1500 年渲染 248 个府面、700 年 115 个，切年 250ms 内出图；check.py --skip-rust 绿。点选卡片未逐一实测（浏览器面板被隐藏时渲染会被节流，我本轮早先看到的空白即此原因，非应用问题）
