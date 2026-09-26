# subjects/cpp 协作规则（C++ 教程）

本文档是 **C++ 教程这个学习应用**的规则。仓库级的通用规则（中文思考、跨应用教学规范、
Git 提交、验证入口、应用之间的边界）在 [`../../AGENTS.md`](../../AGENTS.md)，
那里写过的不在这里重复。
「学习内容」和四节工程规则只留要点，完整原文在 `docs/CONTENT_RULES.md` 与
`docs/ENGINEERING_RULES.md`（主仓库 ADR 0061）。

本应用是 `subjects/` 下的平级学习应用之一（ADR 0045），没有任何特权：仓库根既没有它的
源码，也没有它的脚本和文档。修改代码前先理解当前实现，不得把目标设计误认为已经落地的功能。
界面标题是「C++ 教程」。窗口进程和发行包文件名是 `athena-cpp`。发行副本的用户数据
在 `athena-cpp` 目录；旧目录 `Athena` 若还在且新目录没有，启动时改名过去。

## 必读文档

开始设计或修改代码前，按任务范围阅读：

- `docs/CONTENT_RULES.md`、`docs/ENGINEERING_RULES.md`：本文件「学习内容」「架构原则」
  「代码生成规则」「C++ 编码规则」「GTK 与 Blueprint 规则」五节的完整原文；本文件只留要点。
- `docs/ARCHITECTURE.md`：系统边界、依赖方向和目标架构。
- `docs/CHAPTER_CONFIG.md`：`resources/athena.json` 的字段、标识符和校验规则。
- `docs/CODE_GENERATION.md`：代码生成流程、文件所有权和 Meson 集成约束。
- `docs/decisions/`：本应用的架构决策记录（ADR）；影响仓库结构或多个应用的决策
  记在仓库级 `../../docs/decisions/`。影响架构边界或不可逆方向的新决策应先新增 ADR
  再动代码。
- `docs/LESSON_AUTHORING.md`：写学习页时怎么为一节选择表达手段——按知识类型、
  能否实验、掌握目标来判断，以及可复用的内容块组件（`ui/lesson_blocks.h`）。
  它是**范式不是模子**：`type_semantics` 的节结构由那些知识点的性质决定，
  照抄它的目录只会抄到形状。
- `docs/CODE_ROLES.md`：借政府组织结构理解代码组织的思维模型与它的边界，说明本文件
  这些规则背后的取舍；属于背景观念，冲突时以本文件和 ADR 为准。
- `docs/CONTENT_REFERENCES.md`：**内容来源与查证规则**（ADR 0054）。教学内容一律
  有据可依，不得凭记忆发挥；来源分两级，定义与边界以一级规范性材料
  （cppreference、ISO 草案、Core Guidelines、Microsoft Learn）为准，中文教程站
  只作讲法对照。要防的是抄，不是查。

若实现与文档不一致，先指出差异；修复代码或更新文档时，保持二者同步。

## 项目技术栈

- C++20
- GTK4 / gtkmm 4
- GtkSourceView 5（源码语法高亮与行号）
- MD4C（把 AI 实时返回的 Markdown 讲解解析成结构化 `DocModel`；学习内容本身不用 Markdown）
- GTK `DocumentView`（渲染 AI 讲解对话框里的 Markdown；不使用 WebView。学习内容
  本身由 `.blp` 控件树承载，不经此路径）
- 界面使用 GTK 内建样式与自定义 `style.css`，不依赖 libadwaita
- Meson
- Blueprint UI
- nlohmann/json
- SQLite（掌握状态、AI 讲解缓存和应用设置的本地存储；使用系统自带 libsqlite3，不随包分发）。
  库在 `progress/learning.db`，**随仓库走**（主仓库 ADR 0053）：路径由启动器通过
  `ATHENA_CPP_ROOT` 传入，`platform/app_paths` 的 `own_app_root()` 读它，拿不到
  （发行包）就退回用户数据目录。这不放松「教学内容只从 GResource 读」——内容必须与
  二进制同版本，进度是使用者自己的东西。

除非任务明确要求，不引入新的生产依赖，不更换 UI 技术栈，也不把项目改造成完整 MVC/MVP 框架。

## 学习内容

完整原文见 [docs/CONTENT_RULES.md](docs/CONTENT_RULES.md)。

- 自用的学练合一软件，不以完整教程产品为目标。学习内容从「学习 C++ 知识点」的角度组织，
  不按源码的文件、类或函数顺序写成源码说明书，**不从现有实现反推该教什么**。
- 所有章节都是同一种：可实验知识点由课程类与成员函数承载，理论与工程思想由原生学习页的
  大纲与教学过程承载（`content: article`、`chapter.document` 已由 ADR 0012 废弃，Markdown
  手册路线已由 ADR 0034 删除）。核心闭环：选择知识点 → 查看真实源码 → 运行对应成员函数 →
  查看输出。一个课程类对应一个一级主题，一个 public 成员函数对应一个可独立运行的二级知识点。
- **学习内容一律由 GTK 控件承载，没有 Markdown 正文**。`resources/articles/` 下只剩插图；
  `category.handbook_documents`、`chapter.overview_document`、`subchapter.teaches`、
  `chapter.learning_units` 已由 ADR 0034 废弃，生成器会拒绝。
- **每章第一个标签是「教学大纲」，没有「本章导览」**（ADR 0039 取代 ADR 0036）：把大纲写短，主次与顺序在前；
  难度与掌握目标靠按 `requires` 实时绘制的路线图一眼可见；以图为主；能合并的节不要拆。
- **大纲与教学过程用 GTK 控件表达**（ADR 0033）：能由运行时数据算出来的画成活的并配互动，
  纯概念示意仍用静态 SVG；不同维度不共用视觉编码；一句话能说清就不加图。
- **本应用的三层落地**（仓库级 ADR 0028 的具体形态）：大纲是每章 `.blp` 的「教学大纲」标签（一句题注加五节：痛点与来历、
  心智模型、讲什么与边界、判断与代价、落点；「讲什么与边界」按 ADR 0029 标出难度档与掌握目标），不写语法机制、代码示例和 API 细节；教学过程是
  原生学习页；教学实验是课程类的 public 成员函数，通常 10–30 行。
- **两条实验路径并存**（ADR 0053）：只读实验（课程类成员函数，展示真实源码）与骨架案例
  （`resources/cases/<case>/`，挂在知识点的 `labs[]` 上，学员就地编辑、本机编译运行）。可实操
  的知识点默认一对一配一个骨架案例；验收标准是不改一行就能编译运行（字段见
  `docs/CHAPTER_CONFIG.md` 7.2）；编译诊断完整展示不截断。
- 优先覆盖 C++ 特有能力；与 C 重叠的基础只在理解 C++ 语义确有必要时加入。**受众**是有两三年
  经验的初中级开发者：不讲编程通识，C++ 特有语义要讲透，也不过分拔高。
- **所有教学内容与习题有据可依**（ADR 0054，规则见 `docs/CONTENT_REFERENCES.md`）：一级规范性
  材料定语义，中文教程站只作讲法对照；`source_refs` 指到 `resources/sources/catalog.json`。
  计入掌握度的题目必须有出处，AI 现场出题不计入；自造题写明理由，一节内不得过半。
- **本应用只负责 C++ 语言这一个领域**：别的领域在这里只能是首页学科图谱上的一个节点（按
  `app_id` 启动那个独立应用，ADR 0032 第 5 条），不得在 `athena.json` 里为它开分类、列章节（`da`、`dp` 两次空目录
  表的反例见原文）。判断边界看教的是什么，不看用什么语言写。
- 源码框显示真实源文件，不在 UI 或 C++ 中维护另一份教学代码字符串。
- 图文：首选静态 SVG（`resources/articles/<分类>/images/`），放约定目录并跑资源生成检查；
  `mermaid` 等运行时 JS 渲染的图不用，确有必要先提 ADR。

## 架构原则

完整原文见 [docs/ENGINEERING_RULES.md](docs/ENGINEERING_RULES.md)。

- **层次化、模块化、低耦合是总纲。** 依赖只能自上而下：配置层 → 校验/生成层 → 领域层（不依赖
  GTK）→ 基础能力层（`content/`、`storage/`、`render/`）→ 演示实现层（`cplusplus/`、
  `practice/`）→ 表示层（`ui/`、`MainWindow`），见 `docs/ARCHITECTURE.md` 第 5 节。下层不得持有
  窗口或 GTK 控件指针。
- 一个功能边界一个模块，独占自己的控件树、状态与回调；非 GTK 的执行/网络逻辑单独成模块，
  能脱离 GTK 用 Google Test 验证；不把控件树、后台线程或持久化堆回 `MainWindow`。
- 模块间只通过稳定 ID 和数据对象协作；页面之间不互相调用，跨页导航经 `MainWindow`；异步结果
  经回调交回表示层，服务层不直接更新 GTK。构造参数膨胀、双向调用、共享控件指针，说明边界
  划错了，重新切分而不是加旁路。
- SOLID 与迪米特法则是总纲在类粒度的落地，不教条套用：单文件约 500 行是拆分信号；新增章节、
  知识点、平台后端、AI 服务商走配置或新增文件；出现第二实现或测试替身才补接口；用细粒度
  `function<>` 回调，不定义胖监听接口。
- **三个平台都支持**（Windows 2026-09-15 打通；临时垫片 `compat/glib_final_type_shim.h`，
  MSYS2 的 glibmm 到 2.89+ 后删，主仓库 ADR 0049）。**默认不写平台分支**（ADR 0047）：共享层、领域层、教学实现和
  页面逻辑不出现 `__APPLE__`、Cocoa/WKWebView、`.app` 路径或 macOS 命令；菜单栏问 GTK 设置，
  打开 URI 用 `Gio::AppInfo::launch_default_for_uri`；避开 POSIX 专有写法。Meson 按目标平台选
  源码和依赖，Linux 构建不链接 `gtk4-macos`、Apple Framework 或 Objective-C++。
- **教学内容只从 GResource 读**：运行期不按文件路径找随程序分发的东西；`ATHENA_SOURCE_ROOT`
  只给测试目标用，生产代码不得出现。`platform/` 下新增平台代码要在 ADR 里说明为什么没有通用解。
- AI 讲解的 `DocumentView` 在 macOS 与 Ubuntu 都要履行加载、字号、主题和外部链接契约，不以平台
  WebView 旁路。改共享代码后至少跑 Ubuntu 无 GTK 核心测试和 Meson 构建；涉及页面、资源或平台
  后端再跑 GTK 冒烟测试。
- **`resources/athena.json` 是配置的唯一数据源**：UI 不重复维护章节注册信息；JSON 解析、元数据
  校验、函数注册和 GTK 协调职责分离。配置契约先于解析器、注册表和生成器，不为兼容旧代码扭曲它。
- **稳定 ID**：由 `category.name`、`chapter.name`、`subchapter.name` 派生查找键（如
  `cpp.Reference.reference_basics`）；不用中文标题或数组位置作永久标识。`chapter.name` 是 C++
  类名，`subchapter.name` 是成员函数名，都是可校验的 ASCII 标识符。
- 优先「数据模型 + 注册表 + 轻量协调层」，复杂度确实需要时才引入 MVC/MVP。

## 代码生成规则

完整原文见 [docs/ENGINEERING_RULES.md](docs/ENGINEERING_RULES.md)，流程见 `docs/CODE_GENERATION.md`。

- `scripts/generate_project.py` 统一实现项目校验、Blueprint/GResource 清单、`FunctionRegistry`
  绑定和首次章节骨架生成；输出确定性。
- 生成文件带 `DO NOT EDIT` 与 `.generated.*` 后缀，**禁止直接修改**，改 `athena.json`、模板或
  生成器。生成器不覆盖人工实现、教学示例或测试；骨架只在文件不存在时创建；`scaffold` 只显式
  运行，不加进普通构建。
- 一个章节的知识点实现默认合并到一个 `.hpp`（`docs/CHAPTER_CONFIG.md` 6.1）。
- `description` 是教学需求，不由模板生成器直接转成未经审查的 C++ 实现。

## C++ 编码规则

完整原文见 [docs/ENGINEERING_RULES.md](docs/ENGINEERING_RULES.md)。

- RAII 表达所有权；禁止拥有所有权的裸指针（GTK 非拥有型控件指针除外）；默认 `const`、引用和
  明确的所有权语义。
- 项目代码与教学示例用 `using namespace std;`（放在标准库 `#include` 之后）。`std::move`、
  `std::forward`、`std::remove` 等有冲突风险的名字**始终显式加 `std::`**，清理冗余前缀时跳过它们；
  其余不机械改回 `std::`，也不改成大量 `using std::name`。
- 不加 `athena`、`athena::cpp` 顶层命名空间，确有隔离需求才引入领域命名空间；`.cpp` 内部辅助
  放匿名命名空间。课程类直接用主题名（`Reference`、`SmartPointer`），不加 `Chapter` 后缀；作为
  知识点的成员函数必须 public。
- JSON 字段访问处理缺失、类型错误、重复 ID 和非法标识符；错误信息带分类、章节或方法 ID。
- 新增章节演示不在 `mainwindow.cc` 里堆手写映射，扩展注册表或生成流程。

## GTK 与 Blueprint 规则

完整原文（含既有欠账清单）见 [docs/ENGINEERING_RULES.md](docs/ENGINEERING_RULES.md)。

- **自绘用 GTK 的合成能力**（ADR 0035）：需要对照切换、聚焦、逐步推进时写自定义 `Gtk::Widget`
  并 override `snapshot_vfunc()`，路径仍用 `append_cairo()` 画；纯静态图形用 `DrawingArea`。
  动画用 `add_tick_callback`，控件过渡写在 `style.css`；`GLArea` 与 shader 先提 ADR。gtkmm 绑定
  没暴露的用 `snapshot->gobj()` 调 C API——判据是教学价值，不是绑定方不方便。
- **界面布局默认用 `.blp` 描述，代码不是首选**；重复条目做成一份 `.blp` 模板，由 `Gtk::Builder`
  按数据实例化。
- 只有以下情况才允许用代码构建界面，且应尽量小：
  1. **局部动态调整**：给 `.blp` 里已声明的控件设文本、可见性、CSS class、信号，或往声明好的
     容器里塞按数据生成的子项；
  2. **结构本身由运行时数据决定**，且无法用「模板 + 循环实例化」表达的容器；
  3. **`.blp` 表达不了的绘制**：`DrawingArea` + Cairo、`Gtk::Snapshot` 等。

  选 2 或 3 时，在该文件顶部注释里写清为什么不用 `.blp`。
- 既有纯代码构建的视图是欠账，不是范例，改到时顺手收进 `.blp`；合规参考是
  `resources/ui/window.blp` 与 `resources/ui/chapters/*.blp`。
- 加新 `.blp` 要改两处：`meson.build` 的 `blueprint-compiler compile` target，以及
  `scripts/project_generator/resources.py` 的 GResource 清单。
- 窗口类不实现教学业务逻辑；GResource 路径由配置和生成流程保持一致；共享模板不假设不同分类的
  `order` 全局唯一；Builder、页面缓存和初始化状态用完整章节 ID 作键。

## macOS 发行规则

- macOS 可携带包统一通过 `scripts/package_macos.py` 生成，不手工复制单个可执行文件作为 Release。
- `dist/` 是本地生成目录，不提交 `.app` 或 DMG；GitHub Release 只上传标签构建产生的 DMG。
- `meson.build`、`Info.plist` 和 Git 标签必须使用一致的语义化版本号；版本以 `meson.build` 为单一来源，`package_macos.py` 默认读取它并拒绝不一致的 `--version`。
- 每次发版在 `CHANGELOG.md` 记录该版本的显著变化；**这一节就是 GitHub Release
  的正文**（由 `scripts/changelog_notes.py` 抽出）。若漏写，脚本会按上一标签
  至今的提交自动汇总补节（`--write`），仍应优先手写可读说明。
- 发版顺序：改 `meson.build` 版本 → 写 `CHANGELOG.md` 新节（或让脚本补）→
  提交 → `git tag -a vX.Y.Z`（附注里可写一句摘要）→ 推送提交与标签，等
  `.github/workflows/release.yml` 出包并建 Release。
- 当前包只允许描述为 ad-hoc 签名、未公证版本；完成 Developer ID 和 notarization 前不得宣称已通过 Gatekeeper 正式发行验证。
- 修改打包器、macOS 模板或发行工作流后，应至少生成并启动一次本机架构的 `.app`，并验证 DMG 校验和与应用签名结构。

## Windows 发行规则

- Windows 可携带包统一通过 `scripts/package_windows.py` 生成，不手工复制单个可执行文件作为 Release。
- `dist/` 是本地生成目录，不提交 zip 或 MSI；GitHub Release 只上传标签构建产生的
  `athena-cpp-VERSION-windows-x64.msi` 与 `.zip`。
- `meson.build` 和 Git 标签必须使用同一个 `MAJOR.MINOR.PATCH` 版本；打包器默认读取
  `meson.build` 并拒绝不一致的 `--version`。标签写作 `v7.0.0`，不要打成 `v7.0`。
- 发版说明与 macOS 同一套：以 `CHANGELOG.md` 对应节为准。
- 当前 MSI 未做 Authenticode 签名，对外描述必须如实。
- 修改打包器或发行工作流后，应至少在本机生成 zip 并启动一次 `athena-cpp.cmd`。

## 修改流程

1. 阅读相关文档和现有实现。
2. 明确改动属于配置、生成器、生成代码、人工实现还是 UI。
3. 先更新配置格式和校验，再依赖新增字段。
4. 修改 `athena.json` 后运行 JSON 和资源生成检查。
5. 构建并测试受影响部分。
6. 如果行为或架构边界发生变化，同步更新 `docs/`。

## 验证要求

本应用的检查入口：

```sh
python3 subjects/cpp/scripts/check.py
```

仓库根的 `python3 scripts/check.py cpp [参数...]` 会转发到它，CI 走的就是这条。
脚本依次执行以下步骤；默认构建目录为 `build`，可用 `--build-dir` 与
`--buildtype` 覆盖（CI 使用 `--build-dir build --buildtype debugoptimized`）：

```sh
python3 -m json.tool resources/athena.json >/dev/null
python3 scripts/generate_project.py --project-root . --config resources/athena.json check
meson setup build --reconfigure   # 构建目录不存在时改为 meson setup build
meson compile -C build
meson test -C build --print-errorlogs
```

统一生成器的 `check` 必须通过；GResource XML 和函数注册表只生成到构建目录，
因此检查工作区时不应出现由正常构建造成的生成文件改动。

## 代码评审重点

- 检查 JSON 方法 ID 与注册表键是否完全一致。
- 检查分类之间是否因相同 `order` 或方法名发生键冲突。
- 检查生成器是否可能覆盖人工代码。
- 检查新增元数据是否在配置格式、解析器和文档中同步。
- 检查 UI 是否重复维护 `athena.json` 已经提供的数据。
- 检查源文件展示是否依赖不可移植的编译期绝对路径。
- 检查学习内容的篇幅是否与难度、掌握目标匹配，以及有没有一份内容写成两份
  （ADR 0040）。
