# 北极星 · 项目协作规则

## 定位

北极星是其他学习应用的**路线图与指南针**（ADR 0012）：让人先看见计算机类、电子信息类、电气类、自动化类四个专业类（ADR 0021，弱电优先）的
全局、主次和去向，再决定进哪一个应用练细节。它培养的是技术工程师的大局意识——必要性、能
掌握什么能力、能交出哪一类技术产出——不是又一本教程，也不是课程播放器、招聘聚合器或启动器。
课程图对照 ACM CS2023、ACM/IEEE CE2016、OSSU、工程教育认证等公开标准校准，**不以个人经验或
岗位口味裁课**。具体语法、寄存器和操作步骤属于下游应用，不在这里展开。界面与启动器上的名字是
**北极星**；目录、`id` 与二进制都是 `polaris`（`athena-polaris`）。

两层结构（ADR 0016）：**底盘**（`maps`，知识本身，节点 id 全局唯一）与**路线**（`routes`，从
某个角度走过底盘的顺序，只引用节点 id、不复制节点）。**软硬结合是主线**：`hw-sw-interface`
一张图把「软件看见的硬件、硬件承诺给软件的东西」按六份跨层契约讲清楚。**不偏科**由能力域衡量（ADR 0018）：
路线的均衡度由它引用的节点的能力域算出，**通才阶梯**（`route.generalist-ladder`）保证十四个能力域一个不缺；每个专业类另有自己的主干阶梯（`route.<cs|ei|ee|auto>-ladder`），
方向类路线是在它之上选的纵深。

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
- 旧 Qt 版已删除（ADR 0015 决策 8），基线是 tag `pre-web-polaris`；需要时从 tag 取回。
- `content/sources/reference/roadmaps/`：路线图对照原料（MIT / CC0，带许可证与 commit，见
  `MANIFEST.json`），由 `scripts/fetch_references.py` 下载。对照不进界面，也不被搬进节点正文。

## 内容模型

- 每张图有 `view_kind`：`academic`（课程图与实践主干）、`codesign`（软硬接口）与 `frontier`（纵深与补全：
  数学地基与高端方向所需的知识）是**开放地图**，界面可打开、路线可引用；`career` / `engineering` / `target` 是**参考层**（共 13 张），留在内容
  里、一个节点也不删，但不开放、不被路线引用。
- 课程图（`graph_kind: course`）的节点必须有 `entry`、`verify` 和至少三章 `chapters`（章节掌握度按
  CS2013：熟悉 / 运用 / 评估，运用与评估必须标实践）。`theory` 是不建节点的理论科目，三段齐全。
  **所有开放地图的节点都必须有章节**（ADR 0019、0020，测试守着；新增节点时章节一并提交）：
  章节按学习顺序排，课内先修只指向排在前面的章，可选的 `ref` 必须是该节点自己引用过的来源，最后一章是做出来的验收。
- 每个节点必须写明 `stable_definition`、`engineering_role`、`practice`、`validation`、`volatility` 和至少
  一条 `source_refs`（至少一条**内容来源**：adapted / verbatim / quoted / authored；`see_also` 等只是
  补充说明）。开放地图的节点另须 `pitfall`、`priority`、`priority_reason`；`academic` 的 `targets` 不再必填，写了必须指向有效的目标图（ADR 0021 决策 6）；
  `codesign` 另须 `stage`、`contract`（timing / memory / bus / power / boot / verify）以及**同时**写清
  的 `hw_side` 与 `sw_side`——只写一侧的不属于软硬接口图。
- **专业类与弱电 / 强电**（ADR 0021）：开放地图与全部路线必须写 `discipline`（`cs`、`ei`、`ee`、`auto`，或跨专业的 `cross`）；
  电气类图（`electrical-engineering`）的每个节点必须写 `current`（`weak` 弱电、`strong` 强电、`both` 兼有）。弱电优先：该图弱电与兼有的节点多于强电，
  入门级不放强电。各专业类共用的知识（电路、信号与系统、反馈控制、电机控制）只有一个节点，其他专业类用跨图关联引用，不重复造节点。
- **评级**（ADR 0022、0023）：顶层 `rating_scheme` 定义七个维度（实用性、实践性、理论实用性、可验证性、学科核心骨干、市场需求度、技术发展前景），
  每个五级并写明判据；开放地图的每个节点与每条路线必须写 `ratings`（各维度的 `level` 与 `reason`）。实践性、可验证性、学科核心骨干
  由章节、验证方式、优先级与被依赖数按固定规则推导，**契约会重算**，改了内容就要重新生成评级；实用性、理论实用性、就业需求度是带依据的
  编辑评估（市场需求度与技术发展前景是评估日期当时的估计与判断，不是统计、不暗示录用、不是对个人的建议；`demand` 的 id 保持不变，只是显示名与口径放宽到产品与行业市场）。路线的 `ratings` 由其节点汇总，另有 `assessment`（推荐等级、优劣、
  推荐的后续方向）。评级只用来强调与比较，**不合成总分、不据此删节点或改优先级**；参考层不评级。
- 开放地图的每个节点必须有 `domain`（十四个能力域之一：foundations、programming、algorithms、systems、
  acceleration、security、assurance、embedded、architecture、digital、circuits、signals、control、power）；`frontier` 节点另须 `stage`。
- `requires` 只表达强先修，限同一张图内，且不得指向更高阶段；两端在不同图里的关系放顶层
  `cross_edges`。每条边都要有理由和出处；`enables` 是虚线来路，不写进目标节点的 `requires`。
- **路线**（`routes`）必须写 `lens`（direction / stack / artifact）、`balance`（software / balanced /
  hardware）、`audience`、**可检查的** `artifact`、有序 `stages`（每阶段有节点与 `checkpoint`）和
  `source_refs`，并写 `pitfalls`（该方向最常见的偏科与补法）。同一路线里强先修不得排在被依赖者之后。
  有真实招聘样本支撑的方向可写 `profile`（高端岗位的能力画像），必须带出处、写明是时效性样本、不构成录用承诺。
  通才阶梯覆盖全部能力域、每个 `frontier` 节点都被路线引用，是测试守着的不变量。
- 顶层 `principles` 是学习原则，每条带来自一手来源的出处；原则里的话必须能在引用的来源里找到依据。路线标题用**技术方向**，不用招聘岗位名，
  不暗示学完即可入职。
- 阶段只是列与标签：初级 / 中级 / 资深都默认可看、可点，不设解锁关卡（ADR 0017）。

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
