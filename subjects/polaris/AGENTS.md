# 北极星 · 项目协作规则

## 定位

北极星是其他学习应用的**路线图与指南针**（ADR 0012）：让人先看见计算机、电子信息两门学科的
全局、主次和去向，再决定进哪一个应用练细节。它培养的是技术工程师的大局意识——必要性、能
掌握什么能力、能交出哪一类技术产出——不是又一本教程，也不是课程播放器、招聘聚合器或启动器。
课程图对照 ACM CS2023、ACM/IEEE CE2016、OSSU、工程教育认证等公开标准校准，**不以个人经验或
岗位口味裁课**。具体语法、寄存器和操作步骤属于下游应用，不在这里展开。界面与启动器上的名字是
**北极星**；目录、`id` 与二进制都是 `polaris`（`athena-polaris`）。

两层结构（ADR 0016）：**底盘**（`maps`，知识本身，节点 id 全局唯一）与**路线**（`routes`，从
某个角度走过底盘的顺序，只引用节点 id、不复制节点）。**软硬结合是主线**：`hw-sw-interface`
一张图把「软件看见的硬件、硬件承诺给软件的东西」按六份跨层契约讲清楚。

不要在未另行决定前加入学习进度、知识掌握度、岗位匹配分数、账号、网络同步，或启动其他 Athena
应用；节点可以用 `app` 指出下游学习应用，只指路、不启动。界面按 ADR 0013 / 0015 / 0016 把
表达深度、可视化与交互当作一等目标，允许为读图推翻当前页面；**内容正确是底线**——不为构图
发明先修、不改嫁 id、只增不删（ADR 0054）。

## 技术与目录

- **壳与视图**：Tauri 2 + React 19 + TypeScript（Vite 8），样式 Tailwind 4，动效 Motion；
  图面以 SVG + DOM 承载（ADR 0015）。Rust 端只做壳：`tauri-plugin-single-instance` 保证
  **运行时只有一个北极星窗口**，`tauri-plugin-opener` 让出处链接在系统浏览器里打开。
- **开发**：`app.json` 的 `dev` 块跑 `npm run tauri:dev`（端口 1470），前端由 Vite 热更新。
- `content/polaris.json` 是路线图的唯一内容来源，前端用 `@content` 别名直接导入，**不复制**、
  不得把节点、边、路线或来源硬编码进代码；`content/sources/catalog.json` 保存来源目录。
- **内容契约只在 `scripts/contract.py` 里**（ADR 0015 决策 2）：运行时不校验。新增规则只改这一
  个文件，并在 `scripts/test_contract.py` 里配一个会真失败的反例。
- `src/content/`：类型、目录索引、确定性布局（`layoutColumns`，列 = 阶段或路线阶段）、路线辅助，
  都是与视图无关的纯 TypeScript 并带 Vitest 单测；`src/graph/`、`src/views/`、`src/panels/` 只读它们
  的输出，不自己推导。**开放地图的定义**（`OPEN_VIEW_KINDS`）在 `contract.py` 与
  `src/content/catalog.ts` 各有一份，有测试防止漂移。
- 主题：晴空 / 暖纸两套明亮主题，颜色只走 `src/styles.css` 里的 CSS 变量；不做暗色。
- `legacy-qt/`：旧 Qt 版，原样保留、不再构建；基线是 tag `pre-web-polaris`。等你在 macOS / Windows
  上验收了新界面，再单独一个提交删除（ADR 0015 决策 8）。
- `content/sources/reference/roadmaps/`：路线图对照原料（MIT / CC0，带许可证与 commit，见
  `MANIFEST.json`），由 `scripts/fetch_references.py` 下载。对照不进界面，也不被搬进节点正文。

## 内容模型

- 每张图有 `view_kind`：`academic`（课程图与实践主干）与 `codesign`（软硬接口）是**开放地图**，
  界面可打开、路线可引用；`career` / `engineering` / `target` 是**参考层**（共 13 张），留在内容
  里、一个节点也不删，但不开放、不被路线引用。
- 课程图（`graph_kind: course`）的节点必须有 `entry`、`verify` 和至少三章 `chapters`（章节掌握度按
  CS2013：熟悉 / 运用 / 评估，运用与评估必须标实践）。`theory` 是不建节点的理论科目，三段齐全。
- 每个节点必须写明 `stable_definition`、`engineering_role`、`practice`、`validation`、`volatility` 和至少
  一条 `source_refs`（至少一条**内容来源**：adapted / verbatim / quoted / authored；`see_also` 等只是
  补充说明）。开放地图的节点另须 `pitfall`、`priority`、`priority_reason`；`academic` 另须 `targets`；
  `codesign` 另须 `stage`、`contract`（timing / memory / bus / power / boot / verify）以及**同时**写清
  的 `hw_side` 与 `sw_side`——只写一侧的不属于软硬接口图。
- `requires` 只表达强先修，限同一张图内，且不得指向更高阶段；两端在不同图里的关系放顶层
  `cross_edges`。每条边都要有理由和出处；`enables` 是虚线来路，不写进目标节点的 `requires`。
- **路线**（`routes`）必须写 `lens`（direction / stack / artifact）、`balance`（software / balanced /
  hardware）、`audience`、**可检查的** `artifact`、有序 `stages`（每阶段有节点与 `checkpoint`）和
  `source_refs`。同一路线里强先修不得排在被依赖者之后。路线标题用**技术方向**，不用招聘岗位名，
  不暗示学完即可入职。
- 阶段解锁（ADR 0014）只在本次打开窗口里有效，不记进度。

## 内容边界

只写公开教材、公开文档和可复现仿真能支撑的能力。不写战斗部、突防、目标毁伤、推进剂配方或未
公开型号细节。有许可或非公开约束的对象（如 VxWorks、1553B、GJB 全文），在实操里用可获得的
对照物（FreeRTOS、CAN、公开的过程素养文章）落地，并标明岗位常见目标是什么。大模型只作地面侧
助力（试验复盘、文档检索、受控问答），写明人工确认与非模型备用路径，不得进入飞控闭环。

公开招聘只作**时效性技术需求样本**，用来确认主干上有 C/C++、MATLAB/Simulink、RTOS、总线、
组合导航、半实物、FPGA/DSP、软件工程化等；不得把岗位名称做成节点，也不得暗示学完即可入职。
跨领域约束收成两条必须同时成立的验收：**实时**（截止期、最大抖动、中断 / 总线时序）与
**高性能计算**（有界队列、吞吐、DMA / 缓存、端到端分段延迟）；精度、接口和可靠性验证附着在这
两条上。

**对照来源的使用规则**（ADR 0016 决策 7）：许可证允许再分发（MIT、CC0）的才拷贝入库并带许可证与
commit；保留版权（roadmap.sh）、带相同方式共享义务（CC BY-SA）、未声明许可证或 GPL 的，只记
链接。路线图类来源不是证据：路线与新节点的每一处内容仍要有自己的出处（教材、手册、课程标准）。

## 验证

```sh
cd subjects/polaris
python3 scripts/check.py              # 内容 JSON、原料覆盖、内容契约、前端构建与单测、Rust 侧
python3 scripts/check.py --skip-rust  # 只改了内容或前端时用，省掉 Rust 编译
```

检查器依次：解析内容 JSON → 原料覆盖 → 内容契约（`contract.py` 及其反例测试）→ 前端 `tsc -b` 与
`vite build` → Vitest（含全部视图的渲染冒烟）→ `cargo check`。界面的实际视觉与交互仍需在
macOS / Windows 上打开应用验收（ADR 0013）；构建通过不等于读图成立。
