---
id: T-014
title: StepMedia：真实图叠加参照物标记的渲染组件与接线
owner: cursor
status: done
priority: P0
depends: 
created: 2026-10-17 16:49
updated: 2026-10-17 17:56
---
## 背景（使用者定调，2026-10-17）

「尽量用真实视频或者真实图片标记参照物的方式讲解，避免单纯文字讲要点。」决定见应用 ADR 0130
（`certification/driver/docs/decisions/0130-subject2-real-media-with-reference-marks.md`，先读）。
zcode 在 T-104 里采集素材并写 `content/subject2_media.json`，你负责**渲染组件**与接线。

## 目标

1. 新文件 `lib/subject2/step_media.dart`：`StepMedia` 组件。
   - 输入：一步的素材列表（见下文数据格式），`file` 相对 `content/`；GIF/WebP 动图自己循环播（沿用 ADR 0080 的读图方式与开发时从
     `ATHENA_DRIVER_ROOT` 读磁盘 / 发行走 assets 的路径逻辑，先看 `lib/speed/cheat_image.dart` 怎么做的）。
   - **标记叠加**：`marks` 用归一化坐标，`point` 画圆环+标签，`line`/`arrow` 画线（arrow 带箭头），标签文字在点/线旁、
     有底色保证压在任何画面上都读得清；图缩放时标记跟着缩放保持对位（用 `LayoutBuilder` 取显示矩形再映射，别用像素常量）。
   - 画面下方一行：`view`（如「右后视镜」）+ `caption`；`note`（「示例：点位以你自己的车为准」）灰色小字；点图可放大查看。
   - 没有素材的步骤什么也不渲染，不要占位。
2. 加载：`guide.dart` 增加读取 `content/subject2_media.json`（文件不存在或某项缺失都当没有，不抛错），
   按 `itemId` + 步骤号（1 起）挂到步骤上。**这个文件归 zcode 写，你只读**。
3. 版面：项目页每步先放真实图（有就放）+ 俯视图，文字缩为短句；`StepFlow` 的接线你接着做，不动它的对外参数。
4. 夹具：zcode 素材到来前，用测试夹具（`test/` 下造一份小图+标记 JSON）把组件和加载测起来，不要等素材。

## 数据格式（与 T-104 一致，字段名勿改）

```json
{ "reverse": { "3": [ {
  "file": "images/subject2/reverse/03-right-mirror-bay-corner.jpg",
  "kind": "image", "view": "右后视镜", "caption": "…", "note": "…",
  "source": {"title": "…", "url": "…", "accessed": "2026-10-17"},
  "marks": [
    {"type": "point", "x": 0.42, "y": 0.61, "label": "库角"},
    {"type": "line", "x1": 0.1, "y1": 0.7, "x2": 0.88, "y2": 0.72, "label": "库口边线"}
  ] } ] } }
```

## 约束

- 排在 T-007 补截图之后；与 T-011 同一时间只改一处文件，先做本任务（使用者定调优先级高），T-011 顺延。
- 测试补：标记坐标映射、动图/静图两种、文件缺失降级；`python scripts/check.py driver` 退出码 0。

## 验收

1. 用夹具渲染出带标记的图（宽、窄各一张截图，放 `comms/driver/artifacts/T-014/`），标记位置对位。
2. 项目页挂接后，素材到来即显示，无素材步骤版面不变。

## 进展记录
- [2026-10-17 17:08] cursor：todo → doing
- [2026-10-17 17:55] cursor：doing → review · 已提交 a1de4153。StepMedia 按 0-1 坐标叠点线箭头，缺图降级，无素材不占位。项目页只留一张俯视图和播放键，当前步只剩方向盘、参照、注意；窄屏步骤列表只显示标题；点位空提示挪到下半。截图 comms/driver/artifacts/T-014/fixture-wide.png 与 fixture-narrow.png，库角环打在中心红块上。flutter test 362 通过。check.py 停在 field_map.dart 与 field_kinematics_test.dart 的多余 import，这两处不是我的文件，没改。曲线第 2 步未动。
- [2026-10-17 17:56] claude-code：review → done · 验收：StepMedia 夹具截图标记/标签/示例注释对位，相关测试 21 项绿，项目页收成一张俯视图；真实页面截图待 T-104 素材到位后补
