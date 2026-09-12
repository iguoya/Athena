# athena.json 配置格式与校验规则

## 1. 设计目标

`resources/athena.json` 是 Athena 项目结构的权威来源。配置契约先于解析器、注册表和代码生成器定义；下游代码必须适配本规范，不能用现有实现反向限制配置结构。

配置表达的章节结构：

```text
category                     课程分类、左侧导航
└── chapter                  一级大章节、标签页、对应同名 C++ 类
    └── subchapter           二级知识点、成员函数、可运行
```

`group` 是章节内部可选的视觉分组，不增加代码层级。`description` 是教学概要，也可作为 Codex 编写实验代码时的需求输入。

理论、原则、跨文件工程思想这类不适合用单次运行结果表达的内容，不对应独立的
章节标签页，而是写进所属章节原生学习页的教学大纲与教学过程（见第 6.2 节）。
ADR 0034 之前它们曾以 Markdown 分类手册的形式存在，该路线已整体删除。

## 2. 完整示例

```json
{
  "format_version": 1,
  "defaults": {
    "chapter_ui": {
      "code": {
        "blueprint": "resources/ui/chapters/empty_chapter.blp"
      }
    },
    "chapter_icon": {
      "type": "theme",
      "name": "view-grid-symbolic"
    },
    "subchapter_icon": {
      "type": "theme",
      "name": "media-playback-start-symbolic"
    }
  },
  "categories": [
    {
      "name": "cpp",
      "title": "C++",
      "description": "系统学习 C++ 语言和标准库。",
      "icon": {
        "type": "theme",
        "name": "applications-development-symbolic"
      },
      "chapters": [
        {
          "name": "Reference",
          "title": "引用",
          "description": "学习引用的基本语义和常见用法。",
          "icon": {
            "type": "theme",
            "name": "insert-link-symbolic"
          },
          "implementation": {
            "header": "cplusplus/references/reference.hpp"
          },
          "subchapters": [
            {
              "name": "basic",
              "title": "引用基础",
              "description": "理解引用是对象的别名以及引用必须初始化。"
            }
          ]
        }
      ]
    }
  ]
}
```

## 3. 根对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `format_version` | integer | 是 | 作者配置格式版本；当前为 `1` |
| `defaults` | object | 是 | 章节通用界面和图标默认值 |
| `categories` | array | 是 | 有序课程分类列表 |

配置里出现 `handbook_documents`（顶层或分类级）会被生成器判为错误，
而不是静默忽略。

`format_version` 只用于告诉生成器“这份文件按第几版规则读取”，当前固定写 `1`。
内容作者平时不需要改它；只有项目整体调整字段组织方式时，才由维护者同步修改
这个数字、生成器和本文档。生成器遇到自己不认识的数字会直接报错，不猜测格式。

每一层对象都只允许本规范表格列出的字段。未知字段一律报错，避免把
`description` 误写成 `descripton` 后被静默忽略；已经废弃的字段会给出专门的
迁移提示。

数组顺序就是界面顺序，不再保存冗余的 `order` 字段。

## 4. 默认值

### 4.1 `defaults.chapter_ui`

所有章节共享同一个默认 Blueprint：

```json
{
  "chapter_ui": {
    "code": {
      "blueprint": "resources/ui/chapters/empty_chapter.blp"
    }
  }
}
```

同一 BLP 可以为不同章节分别创建独立控件树和独立页面状态。章节只有在布局确实不同的时候才使用自己的 `ui` 覆盖（见第 10 节）。

Blueprint 编译及资源路径按约定派生：

```text
resources/ui/chapters/empty_chapter.blp
    -> empty_chapter.ui
    -> /app/chapters/empty_chapter.ui
```

默认页面模板的根控件统一使用 `chapter_page`，不在每章重复配置根控件 ID。

### 4.2 默认图标

```json
{
  "chapter_icon": {
    "type": "theme",
    "name": "view-grid-symbolic"
  },
  "subchapter_icon": {
    "type": "theme",
    "name": "media-playback-start-symbolic"
  }
}
```

章节或知识点没有自己的 `icon` 时继承对应默认值。图标回退由通用 UI 逻辑处理，禁止在 C++ 中按章节名手写图标映射。

## 5. 分类 `category`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 稳定分类名称，也是函数 ID 的分类部分 |
| `title` | string | 是 | 左侧导航显示标题 |
| `description` | string | 是 | 分类学习范围概要 |
| `icon` | icon | 是 | 分类导航图标 |
| `chapters` | array | 是 | 有序一级章节列表 |

示例映射：

```text
category.name = cpp
    -> 左侧分类键 cpp
    -> 函数 ID 的分类部分 cpp
```

分类 `name` 使用小写 ASCII `snake_case`：

```regex
^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$
```

## 6. 一级章节 `chapter`

一级章节是课程中的大概念，例如“引用”“RAII 与资源管理”“STL 容器”。每个一级章节对应一个标签页和一个同名 C++ 类；理论性、跨文件的工程思想类内容写进该章原生学习页的教学大纲与教学过程（见 6.2）。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 稳定章节名，也是 C++ 类名 |
| `title` | string | 是 | 标签页显示标题 |
| `description` | string | 是 | 整章概要 |
| `prerequisites` | array | 否 | 同分类前置章节的 `name` 列表；缺省为空，生成器校验引用存在、无重复、无自引用且整图无环；C++ 分类索引据此生成知识图谱 |
| `icon` | icon | 否 | 标签页图标；缺省时继承默认章节图标 |
| `ui` | object | 否 | 特殊 Blueprint 覆盖 |
| `source` | string | 否 | 代码框显示的源码路径 |
| `implementation` | object | 否 | 已有 C++ 实现的编译入口；存在时由构建生成函数注册表 |
| `groups` | array | 否 | 知识点的视觉分组元数据 |
| `subchapters` | array | 是 | 有序可运行知识点列表；没有可运行知识点（如仅作导航用途）时用空数组 |

映射示例：

```text
chapter.name = Reference
    -> 标签页的稳定名称 Reference
    -> C++ 类 Reference
```

具体代码课程类直接使用主题名，例如 `Reference`、`RAII`、`STLContainer`，不添加统一的 `Chapter` 后缀。由于课程类不再放入分类命名空间，所有章节的 `name` 必须在整个项目中唯一；生成器会检查跨分类的类名冲突。没有 `implementation` 的章节只显示课程框架，`name` 仍然占用一个全局类名位（不会真的生成类），保留这份唯一性检查是为了给未来真正实现时预留位置。

`prerequisites` 只表达“理解本章前建议先掌握哪些章节”，不表达文件依赖或 C++
`#include` 关系。数组元素必须使用同分类稳定 `chapter.name`；显示标题改名不影响关系。
C++ 分类索引按最长前置路径自上而下分层，箭头由前置章节指向后续章节。同层仍保持
`athena.json` 的声明顺序，避免为了减少连线交叉而悄悄改变课程顺序。

### 6.1 C++ 实现入口 `implementation`

已经具有可编译 C++ 类和成员函数的 `code` 章节声明：

```json
"implementation": {
  "header": "cplusplus/references/reference.hpp"
}
```

`header` 是仓库根目录相对路径，必须落在 `cplusplus/` 或 `practice/` 之一
下面——两者是平级目录，不是包含关系：`cplusplus/` 按 C++ 语言特性拆分
知识点（比如 `cplusplus/references/`），`practice/` 收纳自成一体的应用
实践项目（比如 `practice/pocket_cube/`），一个项目的状态、算法、界面
代码都收在自己的子目录里，不嵌进 `cplusplus/` 底下、也不分散到别的顶层
目录（如 `render/`）。构建期生成器据此包含类声明，并完全从现有字段派生绑定：

```text
category.name   -> 稳定函数 ID 的分类部分
chapter.name    -> 全局 C++ 类名
subchapter.name -> C++ 成员函数名
```

一个章节声明 `implementation` 后，其全部 `subchapters` 都会进入生成的
`FunctionRegistry`；缺少任何对应类或成员函数都会在编译阶段失败。未声明
`implementation` 的章节只显示课程框架，不进入注册表。`implementation.header`
同时作为章节级源码展示的缺省值，因此不需要再重复填写相同的 `source`。

**默认约定：一个章节的全部知识点实现合并到一个 `.hpp` 里，省略 `implementation.source`
和每个知识点的 `subchapter.source`。** 源码框展示的是 `implementation.header` 本身
（见上一段"同时作为章节级源码展示的缺省值"），单文件承载全部知识点意味着无论用户打开
哪一个知识点，源码框里都是这个章节完整、一致的代码——不会因为拆文件而看不到类声明，
也不会因为按知识点切换 `subchapter.source` 而在不同文件间跳变。`Reference` 章节是这个
默认约定的参考实现。

只有当函数体确实必须分处不同的独立编译单元时才例外使用 `.cpp`（教学演示代码几乎不会
遇到这种情况；当前所有已实现章节都是单文件 `.hpp`，下面只是格式示例）。这种情况下可以
额外指定首次创建的源文件：

```json
"implementation": {
  "header": "cplusplus/example_chapter/example_chapter.hpp",
  "source": "cplusplus/example_chapter/example_chapter.cpp"
}
```

省略 `implementation.source` 时，生成器从 `header` 路径派生同目录的 `.cpp`。
`scaffold` 只创建不存在的文件；已有教学实现不会被覆盖。一个章节确实要拆到多个源文件时，
应像 RAII 早期做法一样给每个知识点自己的 `subchapter.source` 指定实际文件——但这是
应当避免的特例，不是推荐路径，因为它必然导致上一段所说的"按知识点切换源码框内容"的
体验碎片化。`group.source`（分组共享源码文件）仍是配置格式支持的能力，但目前没有章节在用。

章节名称必须是合法且非关键字的 C++ 类型标识符：

```regex
^[A-Za-z_][A-Za-z0-9_]*$
```

### 6.2 教学大纲（在章节的 `.blp` 里）

章节的**教学大纲**不是配置字段，也不是文档：它是该章 Blueprint 里 Notebook 的一个
标签，标题就叫「教学大纲」，排在「简纲」（ADR 0036）之后，例如
`resources/ui/chapters/type_semantics_lesson.blp`。[ADR 0034](decisions/0034-remove-markdown-handbook.md)
删除了 Markdown 手册整条路线，`category.handbook_documents`、
`chapter.overview_document`、`subchapter.teaches` 和 `chapter.learning_units`
四个字段一并废弃，生成器 `check` 遇到它们会报错。

按 [ADR 0028](decisions/0028-outline-process-experiment-layering.md)，教学大纲在学习
内容三层分工里处于最上层，**只指引大方向**。它**不写**具体语法机制、代码示例、
API 用法细节，也不绑定练习或实验——细节由学习页的后续标签（教学过程）落实，
可观察的体验由成员函数（教学实验）提供。一章一份。

内容按 ADR 0028 第 6 节的范式组织，每章体例一致：开头一句题注（这一章承诺解决
什么），然后是**五个固定部分**：

| 部分 | 回答什么 |
|---|---|
| 痛点与来历 | 没有它之前现实工程里出什么事；何时、为解决什么被引入，后来怎么演进 |
| 心智模型 | 用什么结构去理解它，以及由它派生的 2–4 个贯穿全章的基本问题 |
| 讲什么与边界 | 本章覆盖哪些方向、讲到什么深度，哪些相邻内容留到后续 |
| 判断与代价 | 写代码时它让你做哪些选择，每个选择的代价与边界 |
| 落点 | 前置知识；它是后面哪些知识的地基；想深入时去哪查 |

五部分都要出现且不得为空，末尾保留「小结」。按
[ADR 0033](decisions/0033-live-visuals-and-interaction.md)，能由运行时数据算出来的
（先修依赖、难度与掌握目标、实时熟练度）要画成活的并配上互动，纯概念示意用
`resources/articles/<分类>/images/` 下的静态 SVG。参考实现见
`resources/ui/chapters/type_semantics_lesson.blp` 的「教学大纲」标签。

按 [ADR 0036](decisions/0036-lesson-brief.md)，大纲之前还有一个「简纲」标签：它是
大纲的压缩视图，只留标签、删掉解释，一屏看完，每条可点击跳回大纲或对应知识点。
简纲里的每一条都必须是大纲里已有的标题或标签，不得引入大纲没有的说法。

界面里的"说明文档"按钮不再跳转到任何静态文档：它复制章节标题、简介和全部知识点
信息到剪贴板并唤起本机 AI 助手（`ui/chapter_overview.h`），跟未配置
`implementation` 的章节保持骨架框架、不强行生造内容是同一个原则。

## 7. 二级知识点 `subchapter`

二级知识点只属于 `code` 章节，是最小可运行教学单元；每项对应章节类的一个成员函数和界面中的一个运行入口。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 稳定知识点名，也是成员函数名 |
| `title` | string | 是 | 知识点显示标题 |
| `description` | string | 是 | 实验目标和内容概要 |
| `difficulty` | integer | 否 | 知识点难度，0–5，见下 |
| `mastery_goal` | string | 否 | 掌握目标：`master` / `required` / `familiar`，见下 |
| `knowledge_type` | string | 否 | 知识类型：`concept` / `skill` / `strategy`，决定教学动作，见下 |
| `requires` | array | 否 | 先修知识点；同章写知识点名，跨章写完整函数 ID，见 7.1 |
| `icon` | icon | 否 | 知识点图标；缺省时继承默认图标 |
| `group` | string | 否 | 所属视觉分组的 `name` |
| `source` | string | 否 | 该知识点专用的源码展示文件 |

`difficulty` 和 `mastery_goal` 是**两个互相独立的维度**（ADR 0029），和 `title`、
`description` 一样在内容撰写时一次性给出，不是运行时数据；不要求该知识点已经写出
实现代码，骨架阶段也可以先评定。

- `difficulty` 回答“这个知识点本身有多难”。0 表示尚未评估，1–5 依次是入门、简单、
  中等、进阶、高级。**1–3 属于初中级**，是初学者应当拿下的范围；**4–5 属于高级**，
  初学者可以先跳过、以后回来补。
- `mastery_goal` 回答“学完本章要达到什么程度”。`master` 需要精通（反复使用，要能
  解释边界并写对）、`required` 必须掌握（能正确使用，并说明为什么这样选）、
  `familiar` 一般了解（知道它存在和适用场景，需要时能查）。缺省为空串（未评定）。

  评定看三件事，都不看它在代码里出现得多不多：

  1. **用错的代价**：写错会导致未定义行为、资源泄漏或数据损坏，还是只是不够优雅。
     代价越硬，要求越高——`virtual` 析构写不写在代码里出现次数很少，漏了却是 UB。
  2. **是不是地基**：后面多少内容要建立在它之上。`requires` 依赖图里被依赖得越广，
     它越该早学、学牢。
  3. **能不能靠工具兜底**：编译器能拦住的错误可以低一档，只能靠人判断的要高一档。

  按出现频率评级会给出错误信号：`if` 天天写但没什么可精通的，C 风格强制转换在真实
  代码里比 `static_cast` 还常见，却正是要教人避免的写法。
- `knowledge_type` 回答“这一节该用哪种教学动作”，取值 `concept` 概念、`skill`
  程序性技能、`strategy` 条件性策略。三类需要不同的教学设计，展开见
  [LEARNING_DESIGN](LEARNING_DESIGN.md) 的「按知识类型选择教学动作」。

这几项不互相推导：难度高不等于可以不掌握（移动语义就是必须掌握的难点），难度低也不
等于只需了解（`const` 正确性简单却要精通）。UI 把它们作为两个并排徽章只读展示在
知识点标题旁，用户不能修改。

**只给已经写出教学内容的章节评定，其他章节一律留空。** 内容还没写就先定级只是凭印象
猜，写进配置后反而要花力气推翻；评级应当是内容写作的产物，不是前提。

这些标注与通过完整 AI 自测成绩自动换算的“熟练度”是不同概念：熟练度是学习者的当前
状态，存在本地数据库中且不能手动修改；`difficulty` 与 `mastery_goal` 是内容作者
的标注，只存在 `athena.json` 里。

### 7.1 先修知识点 `requires`

`requires` 声明“学这一条之前应当先掌握哪些知识点”，是知识点级的依赖，比章节级
`prerequisites` 细一层。同一章内直接写知识点名，跨章写完整函数 ID：

```json
{ "name": "object_lifetime", "requires": ["initialization"] }
{ "name": "reference_return", "requires": ["cpp.TypeSemantics.object_lifetime"] }
```

生成器会把它统一展开成完整函数 ID，并连同标题一起写进运行时 Catalog，界面因此不必
反查。校验规则见第 9 节；其中**跨章依赖必须与章节 `prerequisites` 同向**这一条最容易
踩到：如果 A 章的知识点依赖 B 章，而 B 章的前置又是 A 章，学习者永远不可能先学到它，
这属于内容顺序自相矛盾，生成器会直接报错。

界面把先修显示为可点击的小标签，并按熟练度标出哪些还没学过，但**不禁用运行入口**——
自用平台上跳着学是常态，这里只需要让“卡住可能是因为哪一步没打牢”看得出来。

## 8. 可选视觉分组 `group`

分组用于在同一个 `code` 标签页内组织知识点，不会生成额外 C++ 类或成员函数。当前没有章节在用——RAII 之前用过 `raii`、`smart_pointer`、`move` 三个分组，后来判断意义不大而移除，改成每个知识点用自己的 `subchapter.source` 指向对应源文件，不再分组展示。分组机制本身还是配置格式支持的能力，需要时可以给新章节用。

```json
{
  "groups": [
    {
      "name": "smart_pointer",
      "title": "智能指针",
      "description": "使用标准智能指针表达资源所有权。",
      "icon": {
        "type": "theme",
        "name": "user-bookmarks-symbolic"
      }
    }
  ],
  "subchapters": [
    {
      "name": "unique",
      "title": "独占指针",
      "description": "学习 unique_ptr 的独占所有权。",
      "group": "smart_pointer"
    }
  ]
}
```

分组字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 章节内唯一的分组名称 |
| `title` | string | 是 | 分组显示标题 |
| `description` | string | 是 | 分组概要 |
| `icon` | icon | 否 | 分组图标 |
| `source` | string | 否 | 该分组知识点共享的源码展示文件 |

每个 `subchapter.group` 必须引用同一章节中已经声明的分组。

分组名已经承载的语义不必在子章节名中重复，例如 `smart_pointer` 分组下使用
`unique`、`shared`、`weak`，而不是 `unique_pointer`、`shared_pointer`。

源码框按以下优先级选择文件：

```text
subchapter.source -> group.source -> chapter.source
```

这样一个章节仍可对应一个类，同时把不同知识分组的成员函数实现拆到较短的 `.cpp` 文件中。

## 9. 图标 `icon`

GTK 主题图标：

```json
{
  "type": "theme",
  "name": "insert-link-symbolic"
}
```

项目资源图标：

```json
{
  "type": "resource",
  "path": "resources/icons/reference.svg"
}
```

约束：

- `type` 只能是 `theme` 或 `resource`。
- `theme` 必须提供非空 `name`。
- `resource` 必须提供仓库根目录相对 `path`，禁止绝对路径和 `..`。
- 资源图标必须由统一资源流程加入 GResource。

## 10. 特殊界面覆盖

普通章节省略 `ui`，使用 `defaults.chapter_ui.code`。只有欢迎页、动画或需要特殊输入控件的章节才覆盖：

```json
{
  "name": "Welcome",
  "title": "欢迎页面",
  "description": "介绍 Athena 的学习方式。",
  "ui": {
    "blueprint": "resources/ui/chapters/welcome.blp"
  },
  "subchapters": []
}
```

`ui.blueprint` 必须是仓库根目录相对路径、以 `.blp` 结尾且文件存在。

## 11. 描述字段

- `category.description`：整个课程分类的学习范围。
- `chapter.description`：标签页顶部的章节概要。
- `group.description`：视觉分组概要。
- `subchapter.description`：成员函数实验必须覆盖的教学内容。

`description` 应描述目标和边界，不包含生成器命令，也不粘贴完整实现代码。

学习内容的定义方向是“C++ 知识点 → 教学大纲 → 教学过程 → 辅助实验代码”。`description`
和学习页正文必须从学习者需要掌握的概念、语义规则、适用边界、常见误区及思维模型出发
撰写，而不是按当前 `.hpp`/`.cpp` 的组织和实现细节逐段解释源码。页面里的代码只作为
理解和验证知识点的例证；课程实现必须服务于已经确认的学习目标，不能反过来
把当前实现范围当作文档内容边界。使用 AI 或生成工具起草文档时，输入应是知识点元数据和
学习目标，生成结果必须人工审核，不得直接把源码摘要当作教学内容。

学习页不能只是连续陈述概念；对适合实验的知识点，应先提出需要理解、预测或判断的问题，
再由对应成员函数提供可观察的行为，让学习者比较“原有预期”和“实际结果”。代码也不能
脱离讲解独立堆叠技巧：每个教学实验都应能回答一个明确的知识问题。实验结果如果暴露了
原有解释的遗漏或边界，应回到教学过程修正并深化知识体系，形成“思想 → 行动 → 反馈 →
新的理解”的循环；不适合单次实验表达的理论内容由教学大纲与教学过程承担，不强行代码化。

如果未来需要严格列举学习目标，可以通过新的配置格式版本增加 `objectives`，当前版本不预先引入。

## 12. 路径和顺序

- 所有配置路径相对于仓库根目录。
- 使用 `/` 作为路径分隔符。
- 禁止绝对路径和 `..` 跳转。
- `categories`、`chapters`、`groups` 和 `subchapters` 的数组顺序就是显示顺序。
- 不从 `title` 推导任何路径或 C++ 名称。

## 13. 语义校验

`scripts/project_generator/model.py` 是作者配置的唯一严格校验器，必须检查：

- `format_version` 是否为受支持版本。
- 必填字段是否存在且类型正确。
- 分类 `name` 全局唯一。
- 章节 `name` 在分类内唯一。
- 知识点 `name` 在章节内唯一。
- 派生键 `category.chapter.subchapter` 全局唯一。
- C++ 名称是否合法且不是关键字。
- `group` 引用是否存在。
- 配置里是否残留 `handbook_documents`、`overview_document`、`teaches` 或
  `learning_units`（ADR 0034 已废弃，应报错）。
- 每层对象是否包含未知字段或已经废弃的字段。
- Blueprint、源码和资源图标路径是否有效。
- 所有章节都有可解析图标：自身图标或默认图标。
- 所有知识点都有可解析图标：自身图标或默认图标。
- 知识点 `difficulty` 若存在，必须是 0–5 的整数。
- 知识点 `mastery_goal` 若存在，必须是 `master`、`required`、`familiar` 之一。
- 知识点 `knowledge_type` 若存在，必须是 `concept`、`skill`、`strategy` 之一。
- 知识点 `requires` 的每一项都必须指向真实存在的知识点，不能自引用，整体不能成环；
  跨章依赖的目标章节必须是本章或本章的（传递）前置章节。

错误信息应给出结构路径和派生键，例如：

```text
athena.json categories[0].chapters[1].subchapters[2]:
duplicate subchapter name 'basic' in 'cpp.Reference'
```

构建期校验通过后，生成器会输出带独立 `catalog_version` 的规范化运行时 Catalog；
C++ 只解码该受信任产物，不再重复上述作者语义校验、默认值计算或错误修正。
`catalog_version` 是生成器与当前二进制之间的内部版本，不是作者需要填写的字段。

## 14. 文件所有权

本文件只定义项目课程数据，不根据当前 `mainwindow.cc`、注册表或生成脚本的实现妥协。修改配置格式后，解析器、资源生成、UI 和代码生成应在后续步骤中统一适配。
