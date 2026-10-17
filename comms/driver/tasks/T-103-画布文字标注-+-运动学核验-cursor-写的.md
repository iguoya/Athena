---
id: T-103
title: 画布文字标注 + 运动学核验 cursor 写的参照迹象
owner: zcode
status: todo
priority: P1
depends: 
created: 2026-10-17 09:46
updated: 2026-10-17 09:46
---
## 目标（leader，来自 T-101 核对与我对 cursor 截图的观察）

zcode 在 T-101 里把草表锚定到真实尺寸后，补上两件尚未做的事：

1. **画布文字标注**：`FieldMapStep` 加可选 `labels`（位置 + 文字，向后兼容），控制线、库位线、道路边缘线、车库等直接标在图上，
   四项草表各步按需标注（不用每步都标，首见即标，后续步保留）。学员打开项目页应当一眼分清哪条是控制线、哪个是库。
2. **运动学核验**：用简单自行车模型（轴距 2.6、车长 4.5、车宽 1.7，沿用你写进 `field_map.dart` 的基准车）验证
   cursor 在 `subject2.json` 里写的「迹象」是否成立，重点两处：曲线第 2 步「左车头角沿着右边线走」「向左约一圈」；
   倒库第 3 步「后视镜壳刚过库口边线时车尾与库角的关系」。给出结论（成立/不成立/要改成什么说法），
   写进 `comms/driver/artifacts/T-103/` 并发消息给我，由 cursor 改正文，你不改 `subject2.json`。

## 约束

- 只动 `field_map.dart`、`field_sketches.dart`、对应测试、artifacts。
- 逐帧「不出线」测试保持；`python scripts/check.py driver` 退出码 0。

## 验收

1. 四项页面截图（附到 artifacts）可见文字标注。
2. 运动学核验结论清单。

## 进展记录
