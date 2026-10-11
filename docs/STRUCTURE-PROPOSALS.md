# 结构规范化提案（处置记录）

> 本文是 2026-10-08 发版 v9.0.0 时对仓库做的一次全量结构侦查的清单与处置记录。
> 使用者已批示「一次性打扫干净」，各条处置如下；涉及语义重划的（如目录改名、
> ADR 迁移）仍维持「先立 ADR 再动手」的规矩，没有借打扫之名实施。

## 背景

v9.0.0 周期仓库从 8 个目录涨到 14 个应用（subjects 11 + practice 3），发版矩阵
从 2 个应用扩到 6 个。这次侦查（CI 覆盖、文档同步、根目录杂物、应用一致性矩阵、
规模分布）发现的问题里，能直接修的已随手修掉，剩下的是**需要拍板的结构性决定**。

## 已直接修复（本次发版窗口，均已提交）

- `docs/REPOSITORY.md` 与实际同步：结构树补 `gtkmm/`、`nas_admin/`、`c-gui-lab/`，
  `c/` 改 `machine/`，北极星技术栈随 ADR 0015 更新；名字表补 `math-tools`、`gtkmm`，
  拾阶进程名如实写 `lumi`。
- 根 `README.md` 应用表从 6 个补全到 14 个，注明分类判据出处。
- ADR 索引补上缺失的 0082 / 0087 / 0088，0081 行补记发布矩阵扩容。
- `gtkmm`、`mathematics` 补此前缺失的 `README.md`；`archive/computer/README.md`
  从 0 字节补成一段说明。
- 根目录清理：`__pycache__/`（源文件从未入库的孤儿 .pyc）、空目录 `dist-driver/`。
- CI 覆盖缺口（六个应用无任何 CI job）：由并行会话在 `fe30cf7` 补齐，含 pnpm 分支。

## 提案处置（2026-10-08 批示「一次性打扫干净」后）

### P1 目录名与 id 的连字符统一 —— **已落地（选项 a）**

例外写进 `REPOSITORY.md` 名字段：目录名允许下划线历史遗留（`nas_admin`、
`pocket_cube`），id 与进程名一律连字符，新目录起名跟 id 一致。目录不改名。

### P2 ascent 的 ADR 位置 —— **已落地（选项 b）**

`subjects/ascent/adr/README.md` 补一段历史档声明：编号体系独立于仓库级
`docs/decisions/`，不改号、不迁移、不重排（ADR 0066「不趋同」原则）。

### P3 拾阶的 Lumi 命名 —— **维持现状**

品牌与更新通道（latest.json、`Lumi_*.exe`）全部绑定此名，是产品决定而非仓库
规范问题；名字表已如实记录例外。

### P4 driver 迁移前的本地残留进度库 —— **已归档入库**

迁 PG 前最后一个本地快照（`learning.db`，495KB，10-02 同步版）从
`subjects/driver/progress/` 移入 `archive/driver-progress-pre-pg/` 并进版本库，
应用目录不再有误导性残留；空的 `progress/points/` 目录链清除。中心 PG 仍是
权威数据源（ADR 0074）。

### P5 ascent 根目录的中文启动脚本 —— **已删除**

`启动 Lumi（开发版）.cmd` 的功能就是 `app.json` 的 `dev` 块已有的内容，
按 ADR 0046 走 launcher 启动。

### P6 仓库级 ADR 编号缺失段的出处说明 —— **已落地**

索引头部补一段：缺号产生于本目录按 ADR 0045/0061 建立之前，当时的决策或散见
各应用文档、或未落成文；编号保留空位，不回填、不重排。

### P7 归档双轨制的边界 —— **已落地**

规则写进 `REPOSITORY.md`：历史按「离它最近的归档位」放，仓库级历史进根
`archive/`，应用自己的历史档进应用内 `archive/`。

---

# 草拟中的提案（ADR 0134 草稿层，落 ADR 前需复看）

## V1 可视化公共组件——同技术体系共用的"帧序列回放 + 模拟"件（草拟 2026-10-11；**已落 ADR 0137**）

### 主张

模拟器与步进回放对章节理论讲解有直接帮助，且已在多个应用里重复出现。把其中
**与课程内容无关的通用部分**做成同技术体系共用的公共组件；具体概念的模拟器
（如「clicked 信号的旅程」）仍归所属应用。

**大原则（tiger 2026-10-11）：同类功能只留一份实现。** 多个应用里重复出现同一份
模拟/回放代码是不对的，维护成本由此而来；必须抽出来公用。

### 现状（2026-10-11 实测）

- `trace-player.ts`：algorithms、cs408、data-structures、design-patterns、linux、
  organization 六个应用各一份，**每份 185 行，与 data-structures 的版本相差 8 行**。
  它消费真实进程打印的 `#ds-trace {...}` 快照行并逐帧回放，不在前端复刻算法真相。
- 同一概念两套框架实现：进程状态图在 software（React，`viz/process-states.tsx`，
  101 行）和 embedded（Vue，`viz/ProcessStates.vue`，126 行）各写了一遍。
- software 的 `viz/` 有 9 个组件（进程状态、甘特图、页面置换、信号量、流水线等），
  自带一份 `common.tsx`；其他应用若要同类图只能重写。
- gtkmm 的 `simulations.tsx`：手写 `setTimeout` 脚本逐步点亮节点。表现形式与
  trace-player 相同（逐帧点亮），**区别只在帧的来源**：脚本 vs 真实进程输出。
- 不在本提案范围：五个应用的 `main.ts` 都是 2357 行、互相近乎整份拷贝。那是阅读/
  测验应用代码，属 0135 的 C 档，这里只记事实，不碰。

### 与现行规则的关系（已裁定：乙）

- 0135 决策 5 写明「不抽代码」；C 档把「阅读/测验/复习等应用代码」划为暂缓。
- 0132 暂缓的理由是「课程结构未定型，抽出的 schema 会固化未定形状」。可视化件
  的抽象面是「帧序列 + 播放控制 + 绘制」，不涉及 schema、内容块、进度，该理由
  不直接适用；且已有六份实证拷贝，不是凭想象抽象。
- **裁定（tiger 2026-10-11）：作为 C 档的明示例外，现在就做，不等 B 档。**
  例外的边界写死：仅限「不触及 schema / 内容块 / 进度库的纯呈现件」；其余 C 档
  内容（阅读器、测验、复习、进度表）维持暂缓，不得以本例外为先例。

### 设计

三层，依赖方向自下而上：

1. **core**（纯 TypeScript，不依赖任何框架）：帧模型、播放控制器
   （播放/暂停/单步/跳转/倍速）、**帧源适配器**——
   (a) 解析真实进程输出（现有 `#ds-trace` 行；gtkmm 协议里的 `signal` 事件）；
   (b) 脚本帧（手写模拟器用）。回放器对帧来源无感，因此模拟器可以渐进地从
   「脚本」换成「真机轨迹」，界面不用改。
2. **bindings**：React 薄封装；Vue 薄封装待有两个以上 Vue 使用方再做，不预建。
3. **概念组件库**（节点、箭头、时间轴、甘特、状态机等）：只收**已有两个应用
   在用**的；单应用独有的留在原地。

准入纪律：

- **props-only**：不 import 任何应用的 content-contract、进度库、文案。
- **二次使用才升入**：第一个使用方的组件先留在应用内，第二个应用确实要用时再抽，
  接口由两个真实使用方定形。
- 初始只收 `trace-player`（已有六份）；其余按上一条陆续收。

### 交付位置与挂接方式（因裁定为乙，不再走「检查副本一致」的过渡）

- **位置：仓库根 `packages/viz/`**，纯 TypeScript 源码包，不预编译（Vite 直接消费源码）。
  不建 `shared/`（0131 的位置仍不执行）；`packages/` 目前只为本例外而设。
- **挂接：各应用 `package.json` 写 `"@athena/viz": "link:../../packages/viz"`**
  （0136 已统一 pnpm，用其符号链接协议；改包源码即时生效，不依赖 B 档工作区）。
  B 档工作区建好后改写为 `workspace:*`，**应用侧的 import 路径不变**。
- **已知要验证的坑**：Vite 默认不放行工作区之外的文件，需要把 `packages/viz`
  加进 `server.fs.allow`；符号链接解析、`tsc` 路径、`tauri dev` 与 `tauri build`
  是否都吃得下，要在一个应用上实测。照 0136 的做法：**先在一个应用上跑通
  `install → dev → build → tauri dev`，再批量**。试点建议用 data-structures。
- **防回流检查**：`scripts/check.py` 加一条——应用内出现与公共包同名/同内容的
  拷贝（如 `trace-player.ts`）即报错，保证「只留一份」不会被悄悄破坏。
- **与 0135 决策 5 的关系**：该条「不建 `shared/`，不抽代码」对本例外松一格——只开
  `packages/viz/` 这一处，其余不变。

### 牵动面

- 六个应用的 `trace-player.ts`；`scripts/check.py` 新增一条跨应用检查。
- 不涉及 `id`、目录名、挂靠关系，不涉及进度库和内容契约。
- 异构栈（gtkmm 的 CMake 实验等）不受影响；gtkmm 的**前端**是 Tauri + React，
  属同技术体系，可以是使用方。
- 与 gtkmm 子项目方案的衔接：真机演示的 `signal` 事件作为帧源，
  即可让「预测信号顺序」用真实序列判分。

### 待拍板

已定：归 C 档明示例外（乙）；原则「同类功能只留一份实现」。
仍待确认：

1. 位置与挂接方式：`packages/viz` + `file:` 依赖，如上。
2. 试点应用：data-structures（trace-player 的原型出处）。
3. 首批收录范围：只收 `trace-player`，还是同时评估 software 的 `viz/`
   与 embedded 重复的进程状态图。
4. 落 ADR 时需同步的文件现在有他人未提交改动（见下），要等其空出来。

### 落 ADR 时的连带改动（均为他人未提交中的文件，暂不动）

`AGENTS.md`（「通用应用代码的抽象待……再议」一句）、`docs/REPOSITORY.md`、
`docs/decisions/README.md`（索引行）、`scripts/check.py`（防回流检查）。

---

## V2 课程/讲解/演示类应用统一为 Tauri 2 + React（草拟 2026-10-11；**未落 ADR**）

### 主张

使用者（tiger 2026-10-11）：所有课程类、讲解类、演示类应用采用一致的技术底层——
**Tauri 2 + React**——并共用构建规范与依赖规范；不符合的全部改造，**先易后难**。
纯实践类（`practice/`）自由发挥，不强求。

使用者在同一段话里先后提到过 Electron + React，已澄清：**选 Tauri**。理由：25 个课程与
图谱应用已是 Tauri，改 Electron 要重写每个应用的 `src-tauri` 壳和启动器托盘/自启动
（刚在 ADR 0127 迁到 Tauri）；实践类 c-gui-lab 的 Electron 不受约束，保持原样。

### 适用范围（按判据，不查清单）

「课程/讲解/演示类」= 学习应用 + 图谱/参考类（REPOSITORY.md 的前两类），即以讲解或演示为目的、
会被启动器当课程应用打开的那批。`practice/` 与素材坑不在内。

### 现状（2026-10-11 实测，26 个 Tauri 应用 + 3 个非 Web 栈）

| 前端 | 应用 | 备注 |
|---|---|---|
| Tauri + React（已符合） | ascent、database、deep-learning、gtkmm、llm-app、llm-finetune、machine-learning、network、os、python、software、polaris | 12 个，不动 |
| Tauri + 原生 TS | algorithms、cs408、data-structures、linux、organization | **同一套壳复制五份**：`main.ts` 各约 2357 行，两两只差约 22 行；cs408/linux/organization 内容仍是空骨架 |
| Tauri + 原生 TS | design-patterns | 自有壳 `main.ts` 约 2700 行 + `fill-code.ts`，内容约 1.4 MB，最完善 |
| Tauri + 原生 TS | mathematics | 自有壳，与上面五份壳相差约 4000 行；另有 `engine/`、`prototypes/` |
| Tauri + 原生 TS | competitions | 约 460 行，赛历 |
| Tauri + Vue | firmware、microcontroller、rtos | 各约 50 行的空壳，**没有内容要迁** |
| Tauri + Vue | math-tools（约 1100 行）、embedded（约 2200 行，含 `db.ts`、`content.ts`） | 有实质代码 |
| Qt6/QML + CMake | machine | QML 20 个文件约 1800 行 + C++ 壳约 250 行；课表、题库、实验、汇编素材都是 JSON/文件，与 Qt 无关 |
| Meson + GTK | c-plus-plus | **暂缓**（使用者定） |
| Flutter | driver | **暂缓**（使用者定） |

即：25 个 Tauri 课程/图谱应用里，12 个已是 React，13 个要改；另有 machine 一个要换栈；
c-plus-plus 与 driver 本轮不动。

### 与现行规则的关系

- **ADR 0133**：它的默认栈（Tauri 2 + React）从「新应用的默认」升为「课程/讲解/演示类的
  强制」；准入 (a)(b)(c) 里保留 gtkmm（教 GTK）、c-plus-plus、driver、c-gui-lab、pocket_cube；
  **machine 退出准入表**（它的 Qt 本来就记为「不得效仿的历史例外」）。math-tools 与 embedded
  系的 Vue 此前从未被准入，只是没人管，现在明确不再允许。
- **ADR 0135 / 0136**：A 档（版本对齐）与 pnpm 统一已落；本提案把 **B 档**（pnpm 工作区 +
  `catalog:` 统一版本 + 共享 tsconfig/vite 基础配置）提前，因为「统一的构建规范和依赖规范」
  正是 B 档的内容。B 档按 0135 要求另立 ADR，且先在一个应用上跑通 `install → dev → build →
  tauri dev` 再批量。
- **ADR 0132**（schema 与内容抽象暂缓）：**不碰**。本提案只换**前端框架**，课表格式、
  `content-contract.json`、进度库 schema、知识点前缀一律不动，不借机抽象公共 schema。
- **ADR 0137**（`packages/viz`）：与本提案正交且互相受益。模拟器核心已是无框架 TS；
  统一到 React 之后，只需补一层 React 绑定，Vue 绑定那条「待两个 Vue 使用方」不再有意义。
- **ADR 0129 / 0054 精神**：改造期间 `id` 不改嫁、内容与进度库零改动，改框架不借机改内容。

### 关键设计决定（需要拍板，见「待拍板」）

原生 TS 那五份壳怎么迁。两条路：

- **甲（建议）**：把壳**保持自己的内容格式**，只把呈现层从手写 DOM 改成 React 组件。
  先拿内容最轻的 linux 做出 React 版壳，验证后复制到另四个（现状就是复制五份，迁完仍是
  五份，但框架一致）。不动 schema，符合 0132。
- **乙**：改用某个已有 React 应用（如 software、os）的壳，把五个应用的内容格式转成它的格式。
  等于启动 schema 统一，与 0132 冲突，成本最高，**不建议**。

### 迁移顺序（先易后难）

每一波一个独立提交系列，每个应用单独提交；波与波之间可以暂停。

| 波 | 对象 | 做法 | 难度依据 |
|---|---|---|---|
| 0 | 前置 | 打 tag `pre-react-unify`；B 档工作区在一个应用上试点（建议先用已符合的 os 或 network） | 0135 要求先试点后批量 |
| 1 | firmware、microcontroller、rtos | 直接按 React 模板重建壳；无内容可迁 | 各约 50 行空壳 |
| 2 | competitions、math-tools | 重写前端，数据文件原样保留 | 460 / 1100 行 |
| 3 | embedded | 重写前端，`db.ts`、`content.ts` 的行为对照移植 | 2200 行，有读写逻辑 |
| 4 | linux（试点）→ organization、cs408 → algorithms、data-structures | 甲方案；先在 linux 做出 React 壳 | 五份同源壳；前三个内容是空骨架，风险最低 |
| 5 | machine | Qt/QML → Tauri + React；见下一节 | 教案是 QML 组件，要逐个重写为 React 组件 |
| 6 | design-patterns、mathematics | 各自的壳单独移植 | 内容与交互最重，放最后 |

### machine 迁移要点

- **不变**：`id`、目录名、`machine.` 知识点前缀、`content/` 下全部 JSON 与素材、`labs/`、
  `scripts/lab.py`、汇编素材 `content/asm/`、学习方法原型（预测–运行 + 机制模拟）。
- **重写**：`qml/pages/`（图谱、大纲）、`qml/components/`（章卡片、节点、内存条、对照、
  随堂考核）、`qml/lessons/*.qml` 的教案（逐节重写为 React 组件，保留动画语义）。
- **删除**：`CMakeLists.txt` 的 Qt 部分、`src/` 的 C++ 壳、CI 与 `app.json` 里的 Qt 步骤、
  macOS 打包里的 Qt 部分。热加载由 Vite HMR 取代。
- **要处理**：machine 自己的 ADR 0042「教案用 QML 写」需要新 ADR 取代；`playground/` 的
  LVGL 小程序本来就是「不是图谱入口」的旁路，建议原地保留、不随迁移处理（待拍板）。
- 迁移前打 `pre-machine-react` tag（machine 已有 `pre-machine-reorg`，不复用）。

### 验收口径（每个应用）

1. `pnpm typecheck`、`pnpm build`、`tauri dev` 能跑，`scripts/check.py <id>` 通过；
2. `content/` 与 `progress/` 的 git diff 为空（machine 之外）；
3. 同一页面迁移前后截图对照，布局与交互没有退化；
4. 禁止遗留：应用内不再有 `.vue`、手写 DOM 壳或 QML；
5. `scripts/check.py` 加一条跨应用检查——课程/讲解/演示类应用的前端必须是 React，
   例外只能列在带理由的豁免表里（初始：c-plus-plus、driver，标「暂缓」，不是准入）。

### 牵动面

- 13 个 Tauri 应用的前端 + machine 的整套壳；`scripts/check.py`（新增检查、豁免表）。
- 需要同步的文档：根 `AGENTS.md` 与 `docs/REPOSITORY.md` 的技术栈措辞、`docs/ENGINEERING.md`、
  各被迁应用的 `AGENTS.md` 技术栈节与目录表、CI 里 machine 的 Qt 步骤。
- 需要新 ADR：仓库级一篇（强制统一 + 修订 0133 准入表 + 提前 B 档，注明与 0132 的关系）；
  machine 一篇（取代 ADR 0042）。
- 不涉及 `id`、目录名、挂靠关系、进度库、内容契约。

### 风险

- **工作量**：design-patterns 与 mathematics 的壳最重，机械移植也要数天；放最后做，
  前面几波的经验用来估时。
- **行为漂移**：手写 DOM 改 React 容易丢交互细节（键盘、滚动位置、焦点）。靠验收口径第 3 条
  的截图对照与逐页清单兜底。
- **machine 的实验链路**：`lab.py` 与应用的衔接（原来由 C++ 壳触发）需要在 Tauri 侧重新接，
  这是 machine 迁移里最不确定的一块，应先做可行性小验证再排期。
- **并行代理冲突**：被迁应用在迁移期间应由单一代理负责，避免和其他会话的内容改动撞车
  （参见 AGENTS.md「多个代理并行」）。

### 待拍板

1. 原生 TS 五份壳走**甲**（只换呈现层，推荐）还是乙？
2. machine 的 `playground/`（LVGL）原地保留，还是随迁移删除？
3. 波 4 里的试点应用用 linux（内容空骨架、风险最低，推荐）还是 data-structures（内容更全、更能暴露问题）？
4. B 档试点应用用 os 还是 network，或另选？
5. 草稿定稿后，仓库级 ADR 与 machine ADR 的编号：落库时按「选号到落库一次完成」处理。
