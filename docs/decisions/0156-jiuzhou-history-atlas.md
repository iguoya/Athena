# ADR 0156：新增九州（jiuzhou）——中国历史地理图鉴，并开「兴趣」领域圈

- 日期：2026-10-13
- 状态：已接受（使用者经 grill 确认 Q1–Q18；2026-10-13 修订：政治秩序**七段**（蒙元并入唐宋），
  地图呈现与 `@athena/maps` 见 [ADR 0157](0157-athena-maps-shared-package.md)）
- 关系：归类按 [REPOSITORY.md](../REPOSITORY.md) 三类判据（图谱/参考）；目录依
  [ADR 0144](0144-mentor-directory.md)；壳依 [ADR 0138](0138-course-apps-unify-tauri-react.md)；
  开圈方式同 [ADR 0114](0114-competitions-group.md)；局部修订
  [ADR 0148](0148-regroup-domain-circles.md)（领域圈清单增「兴趣」）；earth 暂存归属见
  [ADR 0128](0128-earth-app.md)

## 背景

1. 使用者要一份**历史爱好者自用**的中国历史地理图鉴：按编年大阶段（不要机械按朝代切碎）
   浏览重大事件，落点含时间、地点、人物、事件、影响；重要地点按时段标注古地名；观感要
   可视化、有历史感与后世影响感。
2. 主问题是呈现供查阅，不是证明掌握度 → 图谱/参考类，不建进度库、不建出处契约、教学规范
   不生效（先例：polaris、competitions、earth）。
3. 领域上与编程/考证圈无关；earth 目前暂挂「程序设计」，使用者希望日后把这类查阅/演示应用
   收进同一新圈「兴趣」。

## 决策

1. **新增应用 `jiuzhou`（九州 / Jiuzhou）。** 目录 `mentor/jiuzhou/`，进程 `athena-jiuzhou`，
   端口 **1516**，`group: "兴趣"`，不设 `parent`。界面中文名「九州」，英文副标 Jiuzhou。
   id 采用学界通行的 九州 罗马化写法（Jiuzhou / Nine Provinces），不是自造拼音缩写；与
   ADR 0097「不用拼音造 id」的精神一致——专名罗马化可作 id。
2. **归类图谱/参考类**：不建 `progress/learning.db`、不建 `content-contract.json`，跨应用
   教学规范不生效。自用软件，内容版权由使用者自负；出处仍鼓励在内容里注明，不做门禁。
3. **新增启动器领域圈「兴趣」。** 首个成员即 `jiuzhou`。启动器只认 `app.json` 的 `group`
   字符串，零改代码即可出圈（同 ADR 0114）。**预期后续**将 `earth` 的 `group` 改为「兴趣」
   （必要时再议是否迁出 `practice/`）；**本期不改 earth**。
4. **时间主轴是政治秩序阶段，不是朝代清单**（2026-10-13 修订为**七段**：蒙元并入唐宋多元段）。
   朝代只作事件/地点标签。七段为：① 文明起源与早期国家；② 列国争霸与第一次统一；
   ③ 秦汉帝国秩序；④ 分裂与重建；⑤ 唐宋变革·多元与蒙元；⑥ 明清帝制晚期；⑦ 近代转型。
   侧栏可叠文明结构视角，不替代主轴。
5. **交互与技术栈：**
   - 壳：Tauri 2 + React 19 + TypeScript + Vite + Tailwind（最初复制自 `mentor/competitions`，
     此后独立演进；ADR 0062）。
   - 主图：MapLibre GL；**纸本墨线底图与公域/自研水系岸线**来自 `@athena/maps`
     （[ADR 0157](0157-athena-maps-shared-package.md)）。示意疆域面可叠；CHGIS 等学术府州面
     仅本机可选、不入库再分发。
   - 高潮：大阶段切换或「后世影响」可用 React Three Fiber（首发可不进主路径）。
   - 内容：`content/` 下 JSON——`eras` / `events` / `places`；人物表 schema 预留。
6. **内容模型硬约束：**
   - 事件：时间、`placeId`、人物、叙述、`impact`、可选 `leadsTo: eventId[]`。
   - 地点：现代坐标锚点 + 按时段古名；schema 按府州级；填充分档
     **事件落点/都城 → 战略要地（关隘/河运/走廊）→ 其余府州**；地点可带 `role` 地理说明。
   - 第一批可交付：七阶段骨架 + 分档地点 + 时间轴与纸本地图可运行（ADR 0129）。
7. **地理口径：** 默认离线纸本矢量（Q4A）；历史疆域半透明须标「示意」；学术 GIS 层有则叠、无则降级。

## 后果

- `docs/REPOSITORY.md`、根 `README.md`、根 `AGENTS.md`、`.github/workflows/ci.yml`（options 与
  Tauri 矩阵）登记 `jiuzhou`；根 `Cargo.toml` members 加入 `mentor/jiuzhou/src-tauri`。
- 启动器多一个「兴趣」圈；ADR 0148 的六圈清单被本条增补为含「兴趣」（原文不改，索引注明
  由 0156 修订）。
- earth 迁圈是后续纯配置（或再加短 ADR），不阻塞本应用交付。
