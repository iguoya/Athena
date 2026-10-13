---
id: T-107
title: 提亮全覆盖：highlights 覆盖全部事件
owner: zcode
status: blocked
priority: P2
depends: 
created: 2026-10-13 22:43
updated: 2026-10-13 23:09
---
## 目标
`content/highlights.json` 目前只覆盖约 60 个事件，应覆盖全部。

## 做法
给缺失的事件补 `hydro/corridors/features/routes/places` 引用（只能引用已有 id）和 `why`（一句地理因果，与事件的 `geoWhy` 一致）。

## 验收
每个事件都有提亮条目；`check_layers.py` 通过。

## 降频规则（2026-10-13 调整，适用于 zcode 的所有任务）
zcode 的模型调用有频率限制，之前并行派子任务导致触发。从现在起：
- **单线程**：不要派并行子任务，不要同时开多个查询；一次只处理一条或一小批。
- **小批量**：每批最多 10 条，批与批之间自然间隔；做不完就停，下一轮再接着做，不要硬撑。
- **遇到限频（429 / 提示额度用完）立刻停手**：不要重试、不要换个方式再试一遍；用 `status ... blocked --note "限频，等恢复"` 记一笔，恢复后继续。
- **宁缺毋滥**：做不完的部分不算失败，范围已经缩小（见各任务）。质量与可核对性优先于数量。

## 进展记录
- [2026-10-13 23:09] claude-code：todo → blocked · 暂缓（使用者要求降低 zcode 劳动强度）；T-101、T-102 做完后由 claude-code 视额度解冻，现在不要开始。
