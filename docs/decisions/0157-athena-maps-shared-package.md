# ADR 0157：历史地理呈现抽成 `packages/maps`（`@athena/maps`）

- 日期：2026-10-13
- 状态：已接受（使用者确认：Q1A 共享包、Q2A CHGIS 本机可选、Q3A→B 先公域矢量再可选政区面、
  Q4A 纸本墨线默认离线、Q5 见 [0156](0156-jiuzhou-history-atlas.md) 修订）；**学术层优先级与表述手段由
  [ADR 0158](0158-jiuzhou-local-academic-maps-expressiveness.md) 修订**（本机自用优先吃满学术包，
  不进 git）
- 例外于：[ADR 0135](0135-share-low-cost-build-layer-first.md)「不抽代码」；满足
  [ADR 0132](0132-defer-shared-layer.md) 二次使用条件（jiuzhou 首接，earth 预期接样式令牌）
- 衔接：[ADR 0137](0137-viz-shared-package.md)（`packages/` 纯呈现件先例）；
  [ADR 0156](0156-jiuzhou-history-atlas.md)（九州图鉴）

## 背景

1. 九州要以 MapLibre 做历史地理图鉴；earth 等同属「兴趣」查阅向的地理呈现。若各自手写河湖、
   岸线、纸本底图与走廊，会重复且气质漂移。
2. 中国历史政区正统成果是 CHGIS / Hartwell 等，**学术可用、禁止再分发**——不能把原始或派生
   GeoJSON 直接 commit 进公开仓库当默认依赖。
3. 使用者要「多应用充分利用地图/地理研究成果、丰富渲染背景」，并选定**纸本墨线、离线矢量**
   为默认气质（不用在线地形底图做默认）。

## 决策

1. **新建 `packages/maps/`，包名 `@athena/maps`。** 纯呈现与公域/自研示意矢量；不触及课表、
   进度、应用文案（与 0137 同界）。应用以 `workspace:*` 挂接；Vite `server.fs.allow` 放行包路径。
2. **包内默认可再分发的内容：**
   - MapLibre **纸本墨线** `StyleSpecification`（米黄底、水系、弱晕、无外网栅格）。
   - **自研示意** GeoJSON：大陆岸线粗框、黄河/长江/大运河折线、丝路—河西等走廊折线。
   - 样式令牌（色值常量）供 earth 等日后对齐纸本气质。
3. **CHGIS / Hartwell：** 提供 `scripts/fetch_chgis.py`（或包内同名脚本）把数据拉到
   `.cache/chgis/`（gitignore）；有则应用可叠「学术府州面」层并标注出处，无则静默降级到示意层。
   **禁止**把 CHGIS/Hartwell 衍生面默认入库。
4. **首批消费者：`mentor/jiuzhou`。** earth 本期只文档声明可接令牌，不强制改 3D 场景。
5. **准入纪律同 0137：** props/数据导入 only；二次应用才扩 API；不在包里写死某应用的事件模型。

## 后果

- `pnpm-workspace` 已含 `packages/*`，新增包即进工作区。
- 九州地图背景从空白色块升级为纸本 + 水系/岸线/走廊；府州点按分档渲染。
- 修订 ADR 0156：政治秩序主轴改为**七段**（蒙元并入唐宋多元段）；疆域面仍标示意，学术层可选。
