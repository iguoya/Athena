---
id: T-015
title: 数据缺口清单（给 ZCode 的需求）
owner: cursor
status: todo
priority: P2
depends: 
created: 2026-10-13 22:43
updated: 2026-10-13 22:43
---
## 做法
读 `content/**` 时发现的数据缺口（地点缺 `role`、事件缺 `geoWhy`、叙事镜头 `view` 不合理、前端读不到的字段等）汇总，用 `comms.py send --to claude-code` 发给 Claude Code，由 Claude Code 转成 ZCode 的任务。

## 验收
发出一条消息，列出具体 id 与问题。

## 进展记录
