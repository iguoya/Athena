# Athena 项目协作规则

本文档是 Athena 仓库中 Codex 及其他代码代理的项目级指令。修改代码前先理解当前实现，不得把目标设计误认为已经落地的功能。

## 必读文档

开始设计或修改代码前，按任务范围阅读：

- `docs/ARCHITECTURE.md`：系统边界、依赖方向和目标架构。
- `docs/CHAPTER_SCHEMA.md`：`resources/athena.json` 的字段、标识符和校验规则。
- `docs/CODE_GENERATION.md`：代码生成流程、文件所有权和 Meson 集成约束。

若实现与文档不一致，先指出差异；修复代码或更新文档时，保持二者同步。

## 项目技术栈

- C++20
- GTK4 / gtkmm 4
- GtkSourceView 5（源码语法高亮与行号）
- MD4C / md4c-html（文章章节的 Markdown 解析与 HTML 转换）
- macOS WKWebView（文章目录、正文、字号和主题控制；不保留 GTK 文章回退）
- Meson
- Blueprint UI
- nlohmann/json

除非任务明确要求，不引入新的生产依赖，不更换 UI 技术栈，也不把项目改造成完整 MVC/MVP 框架。

## 项目定位与学习内容

- Athena 是供个人学习、练习和验证 C++ 知识点的桌面实验工具，不以制作完整教程产品为目标。
- 章节内容分为 `code` 和 `article`：可实验知识点使用代码闭环，理论、原则和工程思想使用 Markdown 阅读页。
- `code` 章节的核心闭环是“选择知识点 → 查看真实源码 → 运行对应成员函数 → 查看输出结果”。
- 一个 `code` 课程类对应一个一级主题；一个 public 成员函数对应一个可独立运行的二级知识点。
- `article` 章节不生成课程类、成员函数、运行按钮或结果区，正文统一放在 `resources/articles/`；共享层转换为 HTML，平台 ArticleView 后端负责显示。
- Markdown 的 H1–H3 会生成左侧目录，应使用简短的短语式标题；解释性或描述性的完整句子放在标题后的正文中，不通过扩宽目录或缩小字号适配冗长标题。
- 教学实验应短小、聚焦且能直接观察结果；通常以 10–30 行方法体为参考，不为满足行数牺牲完整性和可读性。
- 内容优先覆盖 C++ 特有能力。与 C 语言高度重叠的基础内容只有在理解 C++ 语义确实需要时才加入。
- 源码框显示真实源文件内容，不在 UI 或 C++ 中维护另一份教学代码字符串。

## 架构原则

- `resources/athena.json` 是项目配置的唯一数据源，当前承载分类、章节、分组和知识点元数据。
- UI 层只显示章节、收集用户操作并展示执行结果，不维护重复的章节注册信息。
- JSON 解析、元数据校验、演示函数注册和 GTK 界面协调应保持职责分离。
- `code` 章节使用 `category.name`、`chapter.name` 和 `subchapter.name` 派生稳定查找键，例如 `cpp.Reference.reference_basics`。
- 不使用中文标题或数组位置作为程序内部永久标识；数组位置只决定显示顺序。
- `code` 章节的 `chapter.name` 是 C++ 类名，`subchapter.name` 是成员函数名；两者必须是机器可校验的 ASCII 标识符，禁止从中文标题自动推导。`article` 的 `chapter.name` 只作为稳定页面名。
- Schema 先于解析器、注册表和生成器定义；不得为了兼容旧代码而扭曲 `athena.json`。
- 优先采用“数据模型 + 注册表 + 轻量协调层”，只有复杂度确实需要时才进一步引入 MVC/MVP。

## 代码生成规则

- 当前仓库使用 `scripts/generate_project.py` 统一实现项目校验、Blueprint/GResource 清单、`FunctionRegistry` 绑定和首次章节骨架生成。
- 生成器必须确定性输出：相同输入产生完全相同的文件内容和顺序。
- 自动生成文件必须带有 `DO NOT EDIT` 提示，并使用 `.generated.hpp`、`.generated.cpp` 或项目现有的 `.generated.cc` 后缀。
- 禁止直接修改自动生成文件；应修改 `athena.json`、生成模板或生成器。
- 生成器可以反复覆盖生成的注册表、ID 常量和声明文件。
- 生成器不得覆盖已经存在的人工实现文件、教学示例或测试。
- 首次创建成员函数实现骨架时采用“仅当文件不存在时创建”的策略。
- 自然语言 `description` 是教学需求，不应由普通模板生成器直接转换成未经审查的 C++ 实现；它可以作为 Codex 编写实现的输入。
- `scaffold` 只能显式运行，且只创建不存在的人工实现文件；不得把它加入普通构建副作用。

## C++ 编码规则

- 使用 RAII 表达资源所有权。
- 禁止拥有所有权的裸指针；GTK 提供的非拥有型控件指针除外，并应保持生命周期关系清晰。
- 项目代码和教学示例优先使用 `using namespace std;`，减少反复书写 `std::` 带来的视觉噪声；该偏好同样适用于本项目自己的头文件。
- `using namespace std;` 放在标准库 `#include` 之后；只有出现实际名称冲突或需要强调来源时才局部使用显式 `std::`。
- 不要把已有的简洁标准库名称机械改回 `std::` 前缀，也不必改写为大量 `using std::name` 声明。
- 默认使用 `const`、引用和明确的所有权语义。
- Athena 是独立桌面应用，项目类型和课程类直接使用类名，不增加与项目名或分类名重复的 `athena`、`athena::cpp` 顶层命名空间。
- 只在确有名称隔离需求时引入具备领域含义的命名空间；`.cpp` 内部辅助类型和函数优先放入匿名命名空间限制可见性。
- 具体课程类直接使用主题名，例如 `Reference`、`SmartPointer`；不要统一添加 `Chapter` 后缀。
- 作为可运行知识点的成员函数必须为 public，以便通用运行机制调用。
- JSON 字段访问必须处理缺失字段、类型错误、重复 ID 和非法 C++ 标识符。
- 错误信息应包含分类 ID、章节 ID 或方法 ID，便于定位配置。
- 新增章节演示时不得在 `mainwindow.cc` 中继续堆叠手写映射；应优先扩展独立注册表或生成流程。

## GTK 与 Blueprint 规则

- 界面结构优先写在 `.blp` 文件中，C++ 只负责动态内容、信号和状态协调。
- 不在窗口类中实现教学业务逻辑。
- GResource 路径必须由配置和构建生成流程保持一致。
- 共享 Blueprint 模板时，不得假设不同分类的 `order` 全局唯一。
- Builder、页面缓存和初始化状态使用完整章节 ID 作为键。

## macOS 发行规则

- macOS 可携带包统一通过 `scripts/package_macos.py` 生成，不手工复制单个可执行文件作为 Release。
- `dist/` 是本地生成目录，不提交 `.app` 或 DMG；GitHub Release 只上传标签构建产生的 DMG。
- `meson.build`、`Info.plist` 和 Git 标签必须使用一致的语义化版本号。
- 当前包只允许描述为 ad-hoc 签名、未公证版本；完成 Developer ID 和 notarization 前不得宣称已通过 Gatekeeper 正式发行验证。
- 修改打包器、macOS 模板或发行工作流后，应至少生成并启动一次本机架构的 `.app`，并验证 DMG 校验和与应用签名结构。

## 修改流程

1. 阅读相关文档和现有实现。
2. 明确改动属于配置、生成器、生成代码、人工实现还是 UI。
3. 先更新 schema/校验，再依赖新增字段。
4. 修改 `athena.json` 后运行 JSON 和资源生成检查。
5. 构建并测试受影响部分。
6. 如果行为或架构边界发生变化，同步更新 `docs/`。

## Git 提交规则

- 完成一个独立知识点或可验证阶段后，主动创建一次提交，不等待多个无关阶段累积。
- 提交前运行与该阶段风险相称的构建或检查，确保提交本身处于可用状态。
- 每个提交只表达一个明确主题；配置、运行时代码、教学骨架和界面等不同阶段应尽量拆分。
- 不为了追求很小的提交而拆散必须同步生效的 schema、解析器和构建规则。
- 提交信息应简明说明该阶段的实际成果，便于以后定位、回退和比较。

## 验证要求

本地与 CI 统一通过同一入口执行验证：

```sh
scripts/check.sh
```

脚本依次执行以下步骤；默认构建目录为 `builddir`，可用 `--build-dir` 与
`--buildtype` 覆盖（CI 使用 `--build-dir build --buildtype debugoptimized`）：

```sh
python3 -m json.tool resources/athena.json >/dev/null
python3 scripts/generate_project.py --project-root . --config resources/athena.json check
meson setup builddir --reconfigure   # 构建目录不存在时改为 meson setup builddir
meson compile -C builddir
meson test -C builddir --print-errorlogs
```

统一生成器的 `check` 必须通过；GResource XML 和函数注册表只生成到构建目录，
因此检查工作区时不应出现由正常构建造成的生成文件改动。

## 代码评审重点

- 检查 JSON 方法 ID 与注册表键是否完全一致。
- 检查分类之间是否因相同 `order` 或方法名发生键冲突。
- 检查生成器是否可能覆盖人工代码。
- 检查新增元数据是否在 schema、解析器和文档中同步。
- 检查 UI 是否重复维护 `athena.json` 已经提供的数据。
- 检查源文件展示是否依赖不可移植的编译期绝对路径。
