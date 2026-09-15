# apps/cpp 协作规则（C++ 教程）

本文档是 **C++ 教程这个学习应用**的规则。仓库级的通用规则（中文思考、跨应用教学规范、
Git 提交、验证入口、应用之间的边界）在 [`../../AGENTS.md`](../../AGENTS.md)，
那里写过的不在这里重复。

本应用是 `apps/` 下五个平级学习应用之一（ADR 0045），没有任何特权：仓库根既没有它的
源码，也没有它的脚本和文档。修改代码前先理解当前实现，不得把目标设计误认为已经落地的功能。

## 必读文档

开始设计或修改代码前，按任务范围阅读：

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
- `docs/CONTENT_REFERENCES.md`：外部 C++ 教程站点清单，仅供知识点覆盖范围和讲法对照，
  不作为章节结构或措辞来源。

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
- SQLite（掌握状态、AI 讲解缓存和应用设置的本地存储；使用系统自带 libsqlite3，不随包分发，数据在用户数据目录）

除非任务明确要求，不引入新的生产依赖，不更换 UI 技术栈，也不把项目改造成完整 MVC/MVP 框架。

## 学习内容

- Athena 是为快速渐进学习和掌握 C++ 而开发的自用软件平台，突出学练合一：把零散的代码知识点学习整合到统一框架中，方便运行验证、测试和自我修正；不以制作完整教程产品为目标。
- 学习内容必须从“学习 C++ 知识点”的角度组织和生成，是知识体系、概念语义、适用边界、
  常见误区和思维模型的主要载体；不得按现有源码的文件结构、类结构或函数实现顺序写成
  源码说明书，也不得通过总结现有实现反向决定应教授哪些知识。
- 所有章节都是同一种：可实验知识点由章节的课程类和成员函数承载，理论、原则和工程思想
  由该章原生学习页的大纲与教学过程承载。`content: article` 章节类型和 `chapter.document`
  字段已由 ADR 0012 废弃，Markdown 分类手册整条路线已由 ADR 0034 删除。
- 章节的核心闭环是“选择知识点 → 查看真实源码 → 运行对应成员函数 → 查看输出结果”。
- 一个课程类对应一个一级主题；一个 public 成员函数对应一个可独立运行的二级知识点。
- **学习内容一律由 GTK 控件承载，没有 Markdown 正文。** 原生学习场景自由使用 Blueprint、
  GTK 控件、图片/SVG、图表、流程图和合适的动态绘制来组织“预期—验证—反馈”，页面顺序和
  表现形式由教学目的决定。`resources/articles/` 下只剩这些页面引用的插图，不再有任何
  `.md`；`category.handbook_documents`、`chapter.overview_document`、`subchapter.teaches`
  和 `chapter.learning_units` 四个字段已由 ADR 0034 废弃，生成器会拒绝。
- **每章第一个标签就是「教学大纲」，不再有「本章导览」（ADR 0039 取代 ADR 0036）**。
  导览当初是为了解决"大纲太长、不知道该看哪里"，但它给出的四块内容大纲全都有，
  只是缩写了一遍——两份内容讲同一件事，迟早漂移。**正确的解法是把大纲写短，
  不是在它前面再加一份摘要。**
  大纲要自己承担"三十秒看清轻重缓急"这件事：主次与顺序放在最前，细节在后；
  **难度与掌握目标必须一眼可见**，靠的是那张按 `requires` 实时绘制的路线图
  ——配色给难度、节点文字给掌握目标、底部细条给当前熟练度，点节点直接跳转。
  **以图为主**：概念怎么串、哪节为哪节铺垫，画出来比列出来快；能由数据算出来的
  结构就画成活的。**能合并的节不要拆**：同一组东西不要既列一遍"风险"又列一遍
  "检查点"，那是把一份内容写成两份。
- **大纲与教学过程都用 GTK 控件表达，Markdown 是衍生物**（ADR 0033）：能由运行时
  数据算出来的（先修依赖、难度与掌握目标、实时熟练度）就画成活的并配上互动——点节点
  跳转、切换对照、逐步推进；不要写成文字让读者自己聚合，也不要做成会和数据漂移的
  图片。纯概念示意仍用静态 SVG。不同维度不能共用一套视觉编码。加视觉元素前先问
  "一句话能不能说得同样清楚"，把正文清单排成方框不算可视化。
- 教学实验应短小、聚焦且能直接观察结果；通常以 10–30 行方法体为参考，不为满足行数牺牲完整性和可读性。
- 内容优先覆盖 C++ 特有能力。与 C 语言高度重叠的基础内容只有在理解 C++ 语义确实需要时才加入。
- 源码框显示真实源文件内容，不在 UI 或 C++ 中维护另一份教学代码字符串。
- **本应用的三层落地**（仓库级 ADR 0028 的具体形态）：教学大纲就是每章 `.blp` 里的
  「教学大纲」标签，按一句题注加五节组织——痛点与来历、心智模型、讲什么与边界、
  判断与代价、落点；「讲什么与边界」按 ADR 0029 标出每个方向的难度档与掌握目标。
  大纲不写语法机制、代码示例和 API 细节，不绑定练习，鼓励用静态 SVG 把脉络画出来。
  教学过程是原生学习页，教学实验是课程类的 public 成员函数。
- **图文结合的具体做法**：首选**静态 SVG**（放 `resources/articles/<分类>/images/` 下，
  `.blp` 里按 `images/xxx.svg` 引用，页面用 `resource:///` 加载），零脚本、离线可用；
  结构化对照也可用 GTK 表格控件。该目录下的非 Markdown 文件由生成器整体打包进
  GResource；新增图要放进约定目录并跑一次资源生成检查。`mermaid` 等需要运行时 JS
  渲染的图暂不使用（要打包约 1 MB 的 JS 并引入额外运行时；确有必要时先提 ADR）。

## 架构原则

- 整个软件架构必须保持**层次化、模块化、低耦合**，这是所有其他架构规则的总纲：
  - **层次化**：配置层 → 校验/生成层 → 领域层（`ChapterCatalog`、`FunctionRegistry`、
    `SourceLocator`、`progress_stats` 等不依赖 GTK）→ 基础能力层（`content/`、`storage/`、
    `render/`）→ 演示实现层（`cplusplus/`、`practice/`）→ 表示层（`ui/`、`MainWindow`）。
    依赖只能自上而下，见 `docs/ARCHITECTURE.md` 第 5 节；下层不得持有窗口或 GTK 控件指针。
  - **模块化**：一个功能边界一个模块，独占自己的控件树、状态与回调；非 GTK 的执行/网络
    逻辑（`ExperimentRunner`、`AiService`）单独成模块并可脱离 GTK 用 Google Test 验证。
    新增页面行为放进对应模块，不得把控件树、后台线程或持久化细节堆回 `MainWindow`。
  - **低耦合**：模块间只通过稳定 ID 和明确数据对象协作，不共享零散 GTK 控件指针；
    页面之间不互相调用，跨页导航一律经 `MainWindow`；异步结果通过返回值或完成回调
    交回表示层，不反向调用 `MainWindow`、不在服务层直接更新 GTK。构造参数明显膨胀、
    出现跨模块双向调用或需要共享控件指针时，说明边界划错，应重新切分而不是加旁路。
- 面向对象设计遵循以下六条原则；它们是上一条总纲在类粒度上的落地，冲突时以本文件
  和 ADR 为准，不为教条式套用原则牺牲本项目"轻量协调层、不过早抽象"的取舍：
  - **单一职责（SRP）**：一个类只有一个变化原因。对话框、页面、服务按用途拆分，
    不把设置、历史、自测、渲染通道等塞进同一个类；单文件持续膨胀（经验阈值约
    500 行）应视为拆分信号。
  - **开闭（OCP）**：新增章节、知识点、标签类型、平台后端、AI 服务商时，通过配置、
    新增文件或新增接口实现完成，不改动既有协调代码和注册表手写映射。
  - **里氏替换（LSP）**：任何接口（如 `DocumentView`）的实现必须完整履行其契约，
    不弱化前置条件、不抛出契约外异常；派生只用于框架要求或稳定的纯接口。
  - **依赖倒置（DIP）**：依赖方向自上而下，领域/服务层不依赖 GTK 或 `MainWindow`；
    跨线程、跨平台、需脱离 GTK 测试的边界用抽象接口或回调隔离。单实现、单前端的
    协作方允许直接依赖具体类，但一旦出现第二实现或测试替身需求就必须补接口。
  - **接口隔离（ISP）**：对外接口保持最小；用细粒度 `function<>` 回调和小数据结构
    （`DialogTopic`、`ExperimentRequest`、`TabSpec` 之类）传参，不定义"胖监听接口"，
    不让调用方依赖用不到的方法。
  - **迪米特法则（LoD）**：模块只与直接协作者交谈；不通过持有的对象链式深入访问
    第三方状态，不为省事让下层反向穿透到窗口。
- 跨平台能力同样受上述层次和依赖方向约束。**三个平台都支持**（2026-09-15 打通
  Windows）。Windows 上有一处临时垫片 `compat/glib_final_type_shim.h`：glib 2.90
  把几个类型改用 `G_DECLARE_FINAL_TYPE`，而 MSYS2 现有的 glibmm 2.86 还按旧方式
  前置声明，垫片把 C++ 绑定那三个名字改掉以避开冲突（主仓库 ADR 0049）。MSYS2
  更新 glibmm 到 2.89+ 后删掉垫片即可。写新代码时继续避开 POSIX 专有写法
  （用 `std::numbers::pi` 而不是 `M_PI`，用 `LANGUAGE` 环境变量而不是
  `LC_MESSAGES`），  相关改动遵守：
  - 共享层、领域层、教学实现和页面业务逻辑不得包含 `__APPLE__`、Cocoa/WKWebView、
    `.app` 路径或 macOS 命令；平台差异只允许留在 `render/`、`platform/`、图标/打包
    适配层，或经已有抽象接口（例如 `DocumentView`）隔离。
  - **通用性优先：默认不写平台分支（ADR 0047）。** 想加 `#ifdef`、`.mm` 或按平台
    挑源文件之前，先回答三个问题：这条分支服务的业务是什么？有没有一条所有平台
    都走得通的路能达到同样效果？如果有，那条平台特有的路还剩多少价值？
    绝大多数情况下有通用解：菜单栏问 GTK 的 `gtk-shell-shows-menubar` 设置项，
    打开 URI 用 `Gio::AppInfo::launch_default_for_uri`，应用图标交给 `.app` 的
    `Info.plist` 与图标主题，教学内容一律走 GResource。
  - **教学内容只从 GResource 读**，运行期不按文件路径找任何随程序分发的东西；
    这样源码框显示的内容和实验跑的代码保证同版本。`ATHENA_SOURCE_ROOT` 只给
    测试目标用，生产代码不得出现——那是编译期绝对路径，装到别的机器上就失效。
  - `platform/` 下现在只有 `app_paths`（读一个环境变量）和 `menu_bar_platform`
    （问一句 GTK 设置），都不含条件编译。真要新增平台代码，得在 ADR 里说明
    为什么没有通用解。
  - Meson 必须按目标平台选择源码和系统依赖；不得为了 Linux 在共享代码里增加平台分支，
    也不得让 Linux 构建链接 `gtk4-macos`、Apple Framework 或 Objective-C++ 源文件。
  - AI 讲解的 `DocumentView` 必须在 macOS 与 Ubuntu 履行加载、字号、主题和外部
    链接契约；不得以平台特有 WebView 作为内容渲染旁路。
  - 新增或修改共享代码后，至少运行 Ubuntu 的无 GTK 核心测试和 Meson 构建；涉及页面、
    资源或平台后端时再运行 Ubuntu GTK 冒烟测试。发布物由各平台独立打包，不能把 macOS
    的 `.app`/DMG 规则套到 Linux。
- `resources/athena.json` 是项目配置的唯一数据源，当前承载分类、章节、分组和知识点元数据。
- UI 层只显示章节、收集用户操作并展示执行结果，不维护重复的章节注册信息。
- JSON 解析、元数据校验、演示函数注册和 GTK 界面协调应保持职责分离。
- 章节使用 `category.name`、`chapter.name` 和 `subchapter.name` 派生稳定查找键，例如 `cpp.Reference.reference_basics`。
- 不使用中文标题或数组位置作为程序内部永久标识；数组位置只决定显示顺序。
- `chapter.name` 是 C++ 类名，`subchapter.name` 是成员函数名；两者必须是机器可校验的 ASCII 标识符，禁止从中文标题自动推导。
- 配置契约先于解析器、注册表和生成器定义；不得为了兼容旧代码而扭曲 `athena.json`。
- 优先采用“数据模型 + 注册表 + 轻量协调层”，只有复杂度确实需要时才进一步引入 MVC/MVP。

## 代码生成规则

- 当前仓库使用 `scripts/generate_project.py` 统一实现项目校验、Blueprint/GResource 清单、`FunctionRegistry` 绑定和首次章节骨架生成。
- 生成器必须确定性输出：相同输入产生完全相同的文件内容和顺序。
- 自动生成文件必须带有 `DO NOT EDIT` 提示，并使用 `.generated.hpp`、`.generated.cpp` 或项目现有的 `.generated.cc` 后缀。
- 禁止直接修改自动生成文件；应修改 `athena.json`、生成模板或生成器。
- 生成器可以反复覆盖生成的注册表、ID 常量和声明文件。
- 生成器不得覆盖已经存在的人工实现文件、教学示例或测试。
- 首次创建成员函数实现骨架时采用“仅当文件不存在时创建”的策略。
- 一个章节的全部知识点实现默认合并到一个 `.hpp` 里（`Reference` 是参考实现），只有
  函数体确实必须分处不同编译单元时才例外拆 `.cpp`；详见 `docs/CHAPTER_CONFIG.md` 6.1——
  源码框按 `implementation.header` 展示整章代码，单文件才能保证切换知识点时展示内容一致。
- 自然语言 `description` 是教学需求，不应由普通模板生成器直接转换成未经审查的 C++ 实现；它可以作为 Codex 编写实现的输入。
- `scaffold` 只能显式运行，且只创建不存在的人工实现文件；不得把它加入普通构建副作用。

## C++ 编码规则

- 使用 RAII 表达资源所有权。
- 禁止拥有所有权的裸指针；GTK 提供的非拥有型控件指针除外，并应保持生命周期关系清晰。
- 项目代码和教学示例优先使用 `using namespace std;`，减少反复书写 `std::` 带来的视觉噪声；该偏好同样适用于本项目自己的头文件。
- `using namespace std;` 放在标准库 `#include` 之后；只有出现实际名称冲突或需要强调来源时才局部使用显式 `std::`。
- `std::move`、`std::forward`、`std::remove`（以及其他已知有跨头文件重载/ADL 冲突风险的标准库名字）始终显式加 `std::` 前缀，即使当前文件看不出冲突：`move`/`forward` 不加前缀属于编译器会警告的风险写法（`-Wunqualified-std-cast-call`），`remove` 在 `<cstdio>` 和 `<algorithm>` 之间存在同名歧义。这属于第 72 条"实际名称冲突"的具体例子，不是待清理的冗余前缀。
- 不要把已有的简洁标准库名称机械改回 `std::` 前缀，也不必改写为大量 `using std::name` 声明；清理 `std::` 冗余前缀时跳过上一条列出的例外名字。
- 默认使用 `const`、引用和明确的所有权语义。
- Athena 是独立桌面应用，项目类型和课程类直接使用类名，不增加与项目名或分类名重复的 `athena`、`athena::cpp` 顶层命名空间。
- 只在确有名称隔离需求时引入具备领域含义的命名空间；`.cpp` 内部辅助类型和函数优先放入匿名命名空间限制可见性。
- 具体课程类直接使用主题名，例如 `Reference`、`SmartPointer`；不要统一添加 `Chapter` 后缀。
- 作为可运行知识点的成员函数必须为 public，以便通用运行机制调用。
- JSON 字段访问必须处理缺失字段、类型错误、重复 ID 和非法 C++ 标识符。
- 错误信息应包含分类 ID、章节 ID 或方法 ID，便于定位配置。
- 新增章节演示时不得在 `mainwindow.cc` 中继续堆叠手写映射；应优先扩展独立注册表或生成流程。

## GTK 与 Blueprint 规则

- **自绘要用到 GTK 的合成能力，不要什么都自己在 Cairo 里算（ADR 0035）**。
  `Gtk::Snapshot` 不是"更强的 Cairo"，它没有路径 API：曲线、贝塞尔边、弧线、渐变
  仍然用 `append_cairo()` 拿到 `Cairo::Context` 照旧画。它的价值在 `push_*` 一侧
  ——透明度、虚化、交叉淡入、遮罩、圆角裁剪，以及 `translate`/`rotate`/`scale`
  变换栈。**视图需要对照切换、聚焦一条路径、逐步推进或选中层次时**，写自定义
  `Gtk::Widget` 子类 override `snapshot_vfunc()`；纯静态图形继续用 `DrawingArea`
  + `set_draw_func`，不做无收益的机械迁移。文本在 `Snapshot` 里用 `append_layout`。
  动画用 `add_tick_callback` 推进 0→1 的 progress（参考 `ui/pocket_cube_page.cc`），
  不引入动画框架、不用 `Glib::signal_timeout` 轮询。控件级的悬停/选中/展开过渡
  优先写在 `resources/style.css` 的 `transition` 里，不写进 C++。`GLArea` 和 shader
  暂不引入，确有具体场景需要时先提 ADR。
  注意 gtkmm 的 `Snapshot` 绑定比 C API 窄（只有八个 `append_*`，没有渐变和
  fill/stroke 节点），写的时候以 `gtkmm/snapshot.h` 为准。**但绑定没暴露不等于
  做不到、更不等于该放弃那个效果**：需要渐变或路径节点时用
  `snapshot->gobj()` 拿到 `GtkSnapshot*` 直接调 C API
  （`gtk_snapshot_append_linear_gradient` 等）。gtkmm 本来就是 C API 的薄封装，
  混用是正常做法，不是 hack。判据是这个效果对教学有没有价值，不是绑定方不方便。
- **界面布局默认用 `.blp` 描述，代码不是首选**。任何静态或半静态的控件树
  ——页面骨架、说明/图例面板、卡片模板、对话框结构、工具栏——都应写在
  `.blp` 里；重复出现的条目（列表项、卡片、图例行、节点）应做成一份 `.blp`
  模板，代码用 `Gtk::Builder` 按数据实例化多份，而不是在 C++ 里逐个
  `make_managed` 拼控件。
- 只有以下情况才允许用代码构建界面，且应尽量小：
  1. **局部动态调整**：给 `.blp` 里已声明的控件设文本、可见性、CSS class、
     信号，或往声明好的容器里塞按数据生成的子项；
  2. **结构本身由运行时数据决定**且无法用"模板 + 循环实例化"表达的容器
     （例如层数、连线关系都来自数据的图谱布局）；
  3. **`.blp` 表达不了的绘制**：`Gtk::DrawingArea` + Cairo 自绘、`Gtk::Snapshot`
     等——这类节点连同它必需的父容器可以留在代码里。
  选 2 或 3 时，在该文件顶部注释里写清为什么不用 `.blp`。
- 新增 `render/`、`ui/` 下的视图前先判断：能进 `.blp` 的部分有没有进 `.blp`。
- **既有欠账盘点**（下列都是纯代码构建、不是范例，改到时顺手往 `.blp` 收，
  不要照抄扩大）：
  - `render/chart_view`、`render/knowledge_graph_view`、`render/domain_graph_view`
    ——外壳和图例可进 `.blp`，Cairo 自绘的图形区（规则 3）留代码；
  - `ui/progress_page`、`ui/chapter_index_page`——页面骨架 + 卡片可做成 `.blp`
    模板；
  - `ui/settings_dialog`、`ui/about_dialog`、`ui/quiz_dialog`、
    `ui/ai_markdown_dialog`——对话框结构应写在 `.blp`，代码只填内容和信号。
  - 已经合规的参考：`resources/ui/window.blp`、`resources/ui/chapters/*.blp`
    （章节页 = `.blp` 模板 + `code_chapter_page.cc` 只做协调）。
- 加新 `.blp` 的接线：`meson.build` 加一个 `blueprint-compiler compile` 的
  `custom_target`，编译产物 `.ui` 由 `scripts/project_generator/resources.py`
  写进 GResource 清单——两处都要改，参考 `window.blp` 的现有写法。
- 不在窗口类中实现教学业务逻辑。
- GResource 路径必须由配置和构建生成流程保持一致。
- 共享 Blueprint 模板时，不得假设不同分类的 `order` 全局唯一。
- Builder、页面缓存和初始化状态使用完整章节 ID 作为键。

## macOS 发行规则

- macOS 可携带包统一通过 `scripts/package_macos.py` 生成，不手工复制单个可执行文件作为 Release。
- `dist/` 是本地生成目录，不提交 `.app` 或 DMG；GitHub Release 只上传标签构建产生的 DMG。
- `meson.build`、`Info.plist` 和 Git 标签必须使用一致的语义化版本号；版本以 `meson.build` 为单一来源，`package_macos.py` 默认读取它并拒绝不一致的 `--version`。
- 每次发版在 `CHANGELOG.md` 记录该版本的显著变化。
- 当前包只允许描述为 ad-hoc 签名、未公证版本；完成 Developer ID 和 notarization 前不得宣称已通过 Gatekeeper 正式发行验证。
- 修改打包器、macOS 模板或发行工作流后，应至少生成并启动一次本机架构的 `.app`，并验证 DMG 校验和与应用签名结构。

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
python3 apps/cpp/scripts/check.py
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
