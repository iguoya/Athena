# Athena 架构说明

## 1. 项目目标

Athena 是为快速渐进学习和掌握 C++ 而开发的自用软件平台，突出学练合一：把零散的代码知识点学习整合到统一框架中，方便运行验证和自我修正。项目使用 GTK4、gtkmm、GtkSourceView 5、MD4C、Meson 和 Blueprint 构建。GtkSourceView 负责只读源码框的 C++ 语法高亮和行号显示；MD4C/md4c-html 把文章章节的 Markdown 转换为 HTML。macOS 通过系统 WKWebView 和统一 CSS 完成文章排版；文章模式只保留 WebView 路径，不再维护 GtkTextView 降级渲染。项目结构由 `resources/athena.json` 驱动，用户既可以运行可实验的知识点，也可以阅读不适合用单次运行结果解释的理论、原则和工程思想。

项目采用轻量分层和注册表，不以完整 MVC/MVP 为当前目标。核心问题是让课程配置、C++ 演示实现和 GTK 界面之间具有稳定、可校验的连接。重要架构取舍的背景与后果记录在 `docs/decisions/` 的 ADR 中。

## 2. 当前实现

当前数据流如下：

```text
resources/athena.json
        |
        +--> scripts/generate_project.py --> project_generator/model.py 统一校验
        |        |
        |        +--> builddir/app.gresource.xml
        |        +--> Meson Blueprint 编译目标与文章资源
        |        +--> builddir/function_registry.generated.cc
        |        |             |
        |        |             +--> FunctionRegistry --> Reference / RAII
        |        +--> 显式 scaffold：只创建缺失的人工章节骨架
        |
        +--> GResource: /app/data/athena.json --> ChapterCatalog
                                                     |
        FunctionRegistry + ChapterCatalog ----------> MainWindow（界面协调）
                                                     |
                                                     +--> code 页面
                                                     +--> article 页面
```

已有的优点：

- 章节菜单和 Blueprint 资源主要由 JSON 驱动。
- 多个章节可以共享 `empty_chapter.blp`。
- `code` 与 `article` 章节由同一份 JSON 选择不同默认页面。
- 文章作为 GResource 随应用打包，并可在开发期从源码树回退读取。
- 文章 HTML 和 CSS 与平台显示控件分离；macOS 原生后端在同一个 HTML 页面中渲染目录、正文、字号控制和明暗主题，页内链接直接完成标题跳转。
- 文章 H1–H3 同时作为导航目录，标题保持简短，详细说明由标题后的正文承担。
- 每个知识点可以独立运行并显示结果。
- Meson 配置阶段会校验配置引用的 Blueprint 文件是否存在。
- 统一生成器会校验完整项目模型，并在临时工程中端到端测试四个子命令。
- GResource XML 和函数注册表均生成在构建目录，正常配置和构建不会改脏源码树。
- `athena.json` 引用的教学源码随 GResource 打包；开发时优先读取仓库文件，安装后自动使用内置源码。
- `ChapterCatalog` 和 `FunctionRegistry` 已与 GTK 解耦，可使用 Google Test 单独验证。
- `ContentLoader` 统一封装 GResource、开发期源码文件和 Markdown 文档读取。
- `SourceLocator` 按知识点成员函数名定位真实 C++ 定义范围；列表选择和运行按钮共用同一激活动作，使知识点行、说明、源码持久高亮和运行结果保持同步。
- `MainWindow` 将章节导航、文章页初始化、代码页初始化和知识点列表装配拆为独立方法。
- Meson 将 Catalog、内容加载、Markdown 转换、函数注册和课程实现统一编译为内部 `athena-core` 静态库，应用与核心测试共同链接该库。
- Reference 的 4 个知识点和 RAII 的 6 个知识点已接入注册表；未实现的知识点在界面中保持禁用。

当前的主要问题：

- `MainWindow` 仍负责动态 GTK 控件创建和页面协调；各页面职责已经拆分为独立方法，只有继续显著增长时才需要提取页面装配类。
- 注册表由 `athena.json` 生成；新章节可显式执行 `scaffold` 创建不会覆盖已有文件的首次实现骨架。
- 骨架生成只适合一个头文件与一个源文件的普通章节；RAII 这类按知识组拆分源文件的章节仍由开发者组织。
- Linux 尚未接入 WebKitGTK 6.0；当前没有 Linux 文章显示后端，也不提供 GtkTextView 回退。

## 3. 目标架构

目标流程：

```text
                       +------------------------+
                       | resources/athena.json  |
                       +-----------+------------+
                                   |
                       +-----------v------------+
                       | Schema + semantic check |
                       +-----------+------------+
                                   |
             +---------------------+---------------------+
             |                     |                     |
  +----------v-----------+ +-------v--------+ +----------v-----------+
  | Runtime chapter data | | Generated IDs | | Generated registry   |
  +----------+-----------+ +-------+--------+ +----------+-----------+
             |                     |                     |
  +----------v-----------+         |          +----------v-----------+
  | ChapterCatalog       |<--------+--------->| Function implementations |
  +----------+-----------+                    +----------+-----------+
             |                                           |
             +--------------------+----------------------+
                                  |
                       +----------v-----------+
                       | MainWindow/Presenter |
                       +----------+-----------+
                                  |
                       +----------v-----------+
                       | GTK/Blueprint views  |
                       +----------------------+
```

### 3.1 配置层

`resources/athena.json` 保存：

- 分类、章节和知识点的稳定 `name`。
- 数组表达的显示顺序，以及显示标题和描述。
- 通用 Blueprint、特殊界面覆盖和各层图标。
- 由 `name` 直接表达的函数 ID 分类、C++ 类名和成员函数名。
- 知识点视觉分组等运行时元数据。
- 章节内容类型 `code` / `article`；文章章节同时保存 Markdown 文档路径。
- 已实现 code 章节的 `implementation.header`；类名和函数名由章节与知识点的 `name` 派生，分类名只进入稳定函数 ID。

它不保存 C++ 函数体，也不负责表达 GTK 对象的运行时状态。

### 3.2 校验与生成层

生成器负责：

- 根据 JSON Schema 校验基本结构。
- 校验 ID 唯一性、C++ 标识符和资源文件存在性。
- 生成稳定的复合 ID。
- 生成演示注册表和必要的声明。
- 生成或更新 GResource 输入。
- 对新章节提供不会覆盖人工代码的实现骨架。

### 3.3 领域层

当前已经引入以下不依赖 GTK 的类型：

- `ChapterCatalog`：加载并查询分类、章节和知识点元数据。
- `make_function_id`：从分类、章节和知识点名称构造稳定复合 ID。
- `FunctionRegistry`：由 ID 查找可执行知识点函数。
- `SourceLocator`：在真实教学源码中定位成员函数定义范围，不依赖 GTK，可独立测试。

后续如果运行结果需要区分标准输出、错误和状态，再引入 `FunctionResult`；当前直接向
`ostream` 输出足以覆盖教学实验。

这些类型可以使用普通 C++ 单元测试验证，不需要启动 GTK。

源码按职责分组：`registry/` 放置项目配置的解析、校验、查询以及知识点函数注册；
`content/` 统一读取 GResource、Markdown 和教学源码；`render/` 放置 Markdown 到
HTML 的转换以及各平台 ArticleView 后端。目录归组不改变 `ChapterCatalog` 与
`FunctionRegistry` 的职责边界，二者只通过稳定 ID 协作。

### 3.4 演示实现层

每个 `code` 章节类负责一个主题，成员函数负责一个可运行知识点。例如：

```cpp
class Reference final {
public:
    void reference_basics(std::ostream& output) const;
    void const_reference(std::ostream& output) const;
    void pass_by_reference(std::ostream& output) const;
    void return_by_reference(std::ostream& output) const;
};
```

初期可以继续使用统一签名：

```cpp
void method(std::ostream& output) const;
```

当知识点函数需要输入、结构化错误或状态时，再统一迁移为 `FunctionContext` 和
`FunctionResult`，不要让每个 JSON 条目定义任意 C++ 签名。

`article` 章节不生成章节类和演示注册项。它的正文属于文档资源；共享渲染层使用 md4c-html 生成完整 HTML，注入标题锚点，并生成同页的文章目录与阅读工具栏。HTML 原生页内链接负责目录跳转，应用生成的受控脚本负责字号和明暗主题设置。平台 ArticleView 后端只负责加载 HTML 以及管理原生控件生命周期。

### 3.5 表示层

GTK/Blueprint 层负责：

- 为 `code` 显示分类、章节、说明、源码和执行结果。
- 为 `article` 显示 Markdown 正文和可跳转目录；macOS WKWebView 在一个 HTML 阅读页面中统一显示目录、正文、字号和明暗主题设置。标题由正文的一级标题提供，不重复显示章节头，也不显示运行按钮与结果区。
- 把用户操作转换为稳定函数 ID。
- 调用 `FunctionRegistry`，但不感知具体章节类。

`MainWindow` 最终应成为轻量协调者，不直接解析 JSON，也不包含每个章节的手写函数映射。

## 4. 标识符策略

可运行知识点的稳定查找键由 `code` 配置中的三个 `name` 派生，不在 JSON 中重复保存：

```text
<category.name>.<chapter.name>.<subchapter.name>
```

示例：

```text
cpp.Reference.reference_basics
cpp.Reference.const_reference
```

约束：

- 分类名和成员函数名使用 ASCII `snake_case`；章节名使用合法 C++ 类型名。
- 查找键不从显示标题推导。
- 调整数组顺序不会改变查找键。
- 注册表、日志、测试和 UI 事件统一使用完整查找键。

## 5. 依赖方向

允许的依赖方向：

```text
GTK UI -> ChapterCatalog / FunctionRegistry -> Function implementations
GTK UI -> ArticleView -> platform web view
Generator -> JSON schema and templates
Meson -> Generator outputs
```

禁止：

- 演示实现依赖 `MainWindow`。
- 领域模型包含 GTK 控件指针。
- UI 代码复制章节标题或方法映射。
- 生成文件反向成为配置的唯一来源。

## 6. 渐进式改造顺序

1. 已完成：稳定分类/章节/知识点名称及运行时语义校验。
2. 已完成：将注册表抽成 `FunctionRegistry`，统一复合 ID。
3. 已完成：将 JSON 解析和查询抽成 `ChapterCatalog`。
4. 已完成：为 ChapterCatalog、Markdown、FunctionRegistry 和 GTK 资源建立基础测试。
5. 已完成：从 `athena.json` 生成函数注册表，消除手写课程映射。
6. 生成稳定 ID 常量，供注册表、测试和诊断复用。
7. 支持安全的一次性章节实现骨架生成。
8. 解决源代码展示的安装后资源策略。
9. 在 Linux 上为 ArticleView 接入 WebKitGTK 6.0，复用现有 HTML、CSS、锚点和导航规则。
10. 只有当窗口协调仍然明显复杂时，再考虑正式 Presenter/View 接口。

## 7. MVC/MVP 决策

当前没有必要引入完整 MVC 或 MVP。GTK 控件本身已经承担 View，`ChapterCatalog` 是数据模型，`MainWindow` 可以暂时承担轻量协调职责。优先解决稳定 ID、注册表生成、配置校验和职责拆分，这些问题比增加模式类层次更直接。

如果未来出现以下情况，可以引入 Presenter：

- 同一课程模型需要支持多个前端。
- 大量 UI 行为需要无 GTK 单元测试。
- 窗口类仍包含复杂的导航、过滤、运行状态和错误恢复逻辑。
