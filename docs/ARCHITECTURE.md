# Athena 架构说明

## 1. 项目目标

Athena 是一个使用 GTK4、gtkmm、GtkSourceView 5、MD4C、Meson 和 Blueprint 构建的 C++ 学习桌面应用。GtkSourceView 负责只读源码框的 C++ 语法高亮和行号显示；MD4C 把文章章节的 Markdown 转换为原生 GTK 富文本。课程结构由 `resources/chapters.json` 驱动，用户既可以运行可实验的知识点，也可以阅读不适合用单次运行结果解释的理论、原则和工程思想。

项目采用轻量分层和注册表，不以完整 MVC/MVP 为当前目标。核心问题是让课程配置、C++ 演示实现和 GTK 界面之间具有稳定、可校验的连接。

## 2. 当前实现

当前数据流如下：

```text
resources/chapters.json
        |
        +--> scripts/gen_chapters_xml.py
        |        |
        |        +--> resources/app.gresource.xml
        |        +--> Meson Blueprint 编译目标
        |        +--> resources/articles/**/*.md 资源
        |
        +--> GResource: /app/data/chapters.json
                 |
                 +--> MainWindow::load_chapter_metadata()
                          |
                          +--> 分类侧栏和章节标签
                          +--> code: 源码、知识点列表和运行结果
                          |          +--> 手写 subchapter_demos 注册表
                          +--> article: Markdown 阅读页和标题目录
```

已有的优点：

- 章节菜单和 Blueprint 资源主要由 JSON 驱动。
- 多个章节可以共享 `empty_chapter.blp`。
- `code` 与 `article` 章节由同一份 JSON 选择不同默认页面。
- 文章作为 GResource 随应用打包，并可在开发期从源码树回退读取。
- 每个知识点可以独立运行并显示结果。
- Meson 配置阶段会校验配置引用的 Blueprint 文件是否存在。

当前的主要问题：

- `MainWindow` 同时承担 JSON 解析、模型存储、动态 UI 创建、演示查找和执行结果展示，职责过多。
- JSON 中的 `method` 与 `mainwindow.cc` 手写注册表键缺少统一规则。例如 JSON 的 `basic` 与注册表的 `reference_basic` 不能直接匹配。
- `order` 被用作页面名和加载状态键；不同分类拥有相同 `order` 时可能冲突。
- 分类标题和图标仍在 C++ 中手写，尚未完全数据驱动。
- 源码展示依赖 `ATHENA_SOURCE_ROOT` 编译期绝对路径，安装后的可移植性不足。
- 目前只生成 GResource 清单，不生成章节类、成员函数声明或演示注册表。

## 3. 目标架构

目标流程：

```text
                       +------------------------+
                       | resources/chapters.json|
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
  | ChapterCatalog       |<--------+--------->| Demo implementations |
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

`resources/chapters.json` 保存：

- 分类、章节和知识点的稳定 `name`。
- 数组表达的显示顺序，以及显示标题和描述。
- 通用 Blueprint、特殊界面覆盖和各层图标。
- 由 `name` 直接表达的命名空间、C++ 类名和成员函数名。
- 知识点视觉分组等运行时元数据。
- 章节内容类型 `code` / `article`；文章章节同时保存 Markdown 文档路径。

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

建议逐步引入以下不依赖 GTK 的类型：

- `ChapterCatalog`：加载并查询分类、章节和知识点元数据。
- `ChapterId` / `DemoId`：构造和校验稳定复合 ID。
- `DemoRegistry`：由 ID 查找可执行演示。
- `DemoResult`：承载标准输出、错误或状态。

这些类型可以使用普通 C++ 单元测试验证，不需要启动 GTK。

### 3.4 演示实现层

每个 `code` 章节类负责一个主题，成员函数负责一个可运行知识点。例如：

```cpp
namespace athena::cpp {

class Reference final {
public:
    void reference_basics(std::ostream& output) const;
    void const_reference(std::ostream& output) const;
    void pass_by_reference(std::ostream& output) const;
    void return_by_reference(std::ostream& output) const;
};

} // namespace athena::cpp
```

初期可以继续使用统一签名：

```cpp
void method(std::ostream& output) const;
```

当演示需要输入、结构化错误或状态时，再统一迁移为 `DemoContext` 和 `DemoResult`，不要让每个 JSON 条目定义任意 C++ 签名。

`article` 章节不生成章节类和演示注册项。它的正文属于文档资源，由 Markdown 渲染器转换为 `Gtk::TextBuffer` 的文本和样式标签。

### 3.5 表示层

GTK/Blueprint 层负责：

- 为 `code` 显示分类、章节、说明、源码和执行结果。
- 为 `article` 显示 Markdown 正文和可跳转目录；标题由正文的一级标题提供，不重复显示章节头，也不显示运行按钮与结果区。
- 把用户操作转换为稳定 `DemoId`。
- 调用 `DemoRegistry`，但不感知具体章节类。

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
GTK UI -> ChapterCatalog / DemoRegistry -> Demo implementations
Generator -> JSON schema and templates
Meson -> Generator outputs
```

禁止：

- 演示实现依赖 `MainWindow`。
- 领域模型包含 GTK 控件指针。
- UI 代码复制章节标题或方法映射。
- 生成文件反向成为配置的唯一来源。

## 6. 渐进式改造顺序

1. 为现有 JSON 增加稳定分类/章节 ID，并完成校验。
2. 将知识点注册表从 `mainwindow.cc` 抽成 `DemoRegistry`，统一复合 ID。
3. 将 JSON 解析和查询抽成 `ChapterCatalog`。
4. 生成 ID 常量和注册表，消除手写映射。
5. 支持安全的一次性章节实现骨架生成。
6. 解决源代码展示的安装后资源策略。
7. 只有当窗口协调仍然明显复杂时，再考虑正式 Presenter/View 接口。

## 7. MVC/MVP 决策

当前没有必要引入完整 MVC 或 MVP。GTK 控件本身已经承担 View，`ChapterCatalog` 是数据模型，`MainWindow` 可以暂时承担轻量协调职责。优先解决稳定 ID、注册表生成、配置校验和职责拆分，这些问题比增加模式类层次更直接。

如果未来出现以下情况，可以引入 Presenter：

- 同一课程模型需要支持多个前端。
- 大量 UI 行为需要无 GTK 单元测试。
- 窗口类仍包含复杂的导航、过滤、运行状态和错误恢复逻辑。
