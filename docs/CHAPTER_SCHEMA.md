# athena.json 配置规范

## 1. 设计目标

`resources/athena.json` 是 Athena 项目结构的权威来源。Schema 先于解析器、注册表和代码生成器定义；下游代码必须适配本规范，不能用现有实现反向限制配置结构。

配置表达两个章节形态：

```text
category                     课程分类、左侧导航
└── chapter                  一级大章节、标签页
    ├── content: code        C++ 类、可选 group、可运行 subchapter
    └── content: article     Markdown 文档、文章目录、无运行结果
```

`group` 是代码章节内部可选的视觉分组，不增加代码层级。`description` 是教学概要，也可作为 Codex 编写实验代码或文章时的需求输入。

## 2. 完整示例

```json
{
  "schema": 1,
  "defaults": {
    "content": "code",
    "chapter_ui": {
      "code": {
        "blueprint": "resources/ui/chapters/empty_chapter.blp"
      },
      "article": {
        "blueprint": "resources/ui/chapters/article_chapter.blp"
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
            "header": "language/references/reference.hpp"
          },
          "subchapters": [
            {
              "name": "basic",
              "title": "引用基础",
              "description": "理解引用是对象的别名以及引用必须初始化。"
            }
          ]
        },
        {
          "name": "ProgramOrganization",
          "title": "程序与源码组织",
          "description": "学习多文件 C++ 工程的组织原则。",
          "content": "article",
          "document": "resources/articles/cpp/program_organization.md",
          "subchapters": []
        }
      ]
    }
  ]
}
```

## 3. 根对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `schema` | integer | 是 | Schema 版本；当前为 `1` |
| `defaults` | object | 是 | 默认内容类型、两类通用界面和图标默认值 |
| `categories` | array | 是 | 有序课程分类列表 |

数组顺序就是界面顺序，不再保存冗余的 `order` 字段。

## 4. 默认值

### 4.1 `defaults.content` 与 `defaults.chapter_ui`

`defaults.content` 只能是 `code` 或 `article`，当前使用 `code`，因此已有可实验章节无需重复声明。两类章节分别共享默认 Blueprint：

```json
{
  "content": "code",
  "chapter_ui": {
    "code": {
      "blueprint": "resources/ui/chapters/empty_chapter.blp"
    },
    "article": {
      "blueprint": "resources/ui/chapters/article_chapter.blp"
    }
  }
}
```

同一 BLP 可以为不同章节分别创建独立控件树和独立页面状态。章节只有在布局确实不同的时候才使用自己的 `ui` 覆盖。

Blueprint 编译及资源路径按约定派生：

```text
resources/ui/chapters/empty_chapter.blp
    -> empty_chapter.ui
    -> /app/chapters/empty_chapter.ui
```

代码页面模板的根控件统一使用 `chapter_page`，文章页面模板统一使用 `article_page`，不在每章重复配置根控件 ID。

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

一级章节是课程中的大概念，例如“引用”“RAII 与资源管理”“STL 容器”和“程序与源码组织”。每个一级章节对应一个标签页；只有 `code` 章节对应同名 C++ 类。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 稳定章节名，也是 C++ 类名 |
| `title` | string | 是 | 标签页显示标题 |
| `description` | string | 是 | 整章概要 |
| `content` | string | 否 | `code` 或 `article`；缺省时继承 `defaults.content` |
| `document` | string | 条件 | `article` 默认页必填，指向 `resources/articles/` 下的 Markdown |
| `overview_document` | string | 否 | `code` 章节“本章总纲”按钮展示的静态理论讲解文档，指向 `resources/articles/` 下的 Markdown；未提供时按钮退回复制提示词到剪贴板并唤起本机 AI 助手 |
| `icon` | icon | 否 | 标签页图标；缺省时继承默认章节图标 |
| `ui` | object | 否 | 特殊 Blueprint 覆盖 |
| `source` | string | 否 | `code` 代码框显示的源码路径 |
| `implementation` | object | 否 | 已有 C++ 实现的 code 章节编译入口；存在时由构建生成函数注册表 |
| `groups` | array | 否 | `code` 知识点的视觉分组元数据 |
| `subchapters` | array | 是 | `code` 的有序可运行知识点列表；`article` 使用空数组 |

映射示例：

```text
content = code
chapter.name = Reference
    -> 标签页的稳定名称 Reference
    -> C++ 类 Reference
```

具体代码课程类直接使用主题名，例如 `Reference`、`RAII`、`STLContainer`，不添加统一的 `Chapter` 后缀。由于课程类不再放入分类命名空间，所有 `code` 章节的 `name` 必须在整个项目中唯一；生成器会检查跨分类的类名冲突。文章章节的 `name` 只是稳定页面名，例如 `ProgramOrganization`，不会生成同名类。

### 6.1 C++ 实现入口 `implementation`

已经具有可编译 C++ 类和成员函数的 `code` 章节声明：

```json
"implementation": {
  "header": "language/references/reference.hpp"
}
```

`header` 是仓库根目录相对路径。构建期生成器据此包含类声明，并完全从现有字段派生绑定：

```text
category.name   -> 稳定函数 ID 的分类部分
chapter.name    -> 全局 C++ 类名
subchapter.name -> C++ 成员函数名
```

一个章节声明 `implementation` 后，其全部 `subchapters` 都会进入生成的
`FunctionRegistry`；缺少任何对应类或成员函数都会在编译阶段失败。未声明
`implementation` 的章节只显示课程框架，不进入注册表。`implementation.header`
同时作为章节级源码展示的缺省值，因此不需要再重复填写相同的 `source`。

为普通章节运行 `generate_project.py scaffold` 时，可以额外指定首次创建的源文件：

```json
"implementation": {
  "header": "language/type_semantics/type_semantics.hpp",
  "source": "language/type_semantics/type_semantics.cpp"
}
```

省略 `implementation.source` 时，生成器从 `header` 路径派生同目录的 `.cpp`。
`scaffold` 只创建不存在的文件；已有教学实现不会被覆盖。一个章节拆为多个源文件时，
应像 RAII 一样给每个知识点自己的 `subchapter.source` 指定实际文件，并人工维护实现；
`group.source`（分组共享源码文件）仍是 schema 支持的能力，但目前没有章节在用。

章节名称必须是合法且非关键字的 C++ 类型标识符：

```regex
^[A-Za-z_][A-Za-z0-9_]*$
```

### 6.2 本章总纲 `overview_document`

`code` 章节可选提供 `overview_document`，指向一份人工撰写、静态存在于
`resources/articles/` 下的 Markdown 理论讲解文档：

```json
"overview_document": "resources/articles/cpp/reference_overview.md"
```

界面里"本章总纲"按钮点击后直接本地读取并渲染这份文档（跟 `article` 章节
同一套 md4c 转 HTML、WKWebView 排版），**不发起任何网络或 AI 调用**——内容
是撰写时一次性确定好、经人工审核过的，不是运行时现场生成的。撰写过程可以
用 AI 辅助起草，但草稿必须经人工审核后才能提交；这是"自然语言 description
不应由普通模板生成器直接转换成未经审查的实现"这条规则在文档内容上的
应用，只是这里的"实现"换成了理论讲解文档。

未提供 `overview_document` 的章节，"本章总纲"退回复制章节标题、简介和
全部知识点信息到剪贴板并唤起本机 AI 助手，跟未配置 `implementation` 的
章节保持骨架框架、不强行生造内容是同一个原则。

`overview_document` 复用 `document` 字段同样的路径校验和 GResource 打包
流程，但语义不同：`article` 章节的 `document` 是该页面的全部正文；`code`
章节的 `overview_document`只是补充性的理论文档，不影响 `code` 章节本身
的知识点列表、源码框和运行结果区。

### 6.3 `code` 与 `article` 的选择

- 能用短小源码和可观察输出验证的语法、语义或库能力使用 `code`。
- 理论、原则、设计取舍和跨文件工程思想，如果单次运行结果不足以说明内容，使用 `article`。
- `article` 可以包含 Markdown 代码块，但页面不提供运行按钮和结果区。
- Word 文档不属于当前 schema；需要时应通过新的文档转换层引入，而不是让运行时直接依赖办公文档格式。

文章示例：

```json
{
  "name": "ProgramOrganization",
  "title": "程序与源码组织",
  "description": "学习命名空间、翻译单元、ODR 和 Modules。",
  "content": "article",
  "document": "resources/articles/cpp/program_organization.md",
  "subchapters": []
}
```

## 7. 二级知识点 `subchapter`

二级知识点只属于 `code` 章节，是最小可运行教学单元；每项对应章节类的一个成员函数和界面中的一个运行入口。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 稳定知识点名，也是成员函数名 |
| `title` | string | 是 | 知识点显示标题 |
| `description` | string | 是 | 实验目标和内容概要 |
| `importance` | integer | 否 | 内容难度／重要度，0–5，见下 |
| `icon` | icon | 否 | 知识点图标；缺省时继承默认图标 |
| `group` | string | 否 | 所属视觉分组的 `name` |
| `source` | string | 否 | 该知识点专用的源码展示文件 |

`importance` 和 `title`、`description` 一样在内容撰写时一次性给出，不是运行时数据。
它表达的是内容作者基于教学与工程实践经验得出的客观难度判断，不要求该知识点
已经写出实现代码——即使还是骨架或占位，也可以先给出难度判断，
0 表示尚未评估，1–5 依次是简单、一般、正常、复杂、极难。UI 中只读展示在知识点
标题旁，用户不能修改；与用户自评的“熟练度”五星评分是两个独立概念，后者存在
本地数据库中，`importance` 只存在 `athena.json` 里。缺省为 `0`（未评）。

映射示例：

```text
category.name = cpp
chapter.name = Reference
subchapter.name = reference_basics

派生查找键：cpp.Reference.reference_basics
C++ 目标：Reference::reference_basics(...)
```

不再同时保存 `id` 和 `method`。在当前一对一模型中，`name` 同时承担稳定局部名称和成员函数名，避免重复字段发生不一致。

`name` 应优先使用能直接描述实验行为的完整 `snake_case` 短语，例如
`const_reference`、`pass_by_reference` 和 `return_by_reference`。不要仅为避开
C++ 关键字而使用 `const_`、`return_` 这类难以独立理解的名称。

命名不使用缩写：`ctor`、`dtor`、`ptr`、`seq`、`assoc`、`rw` 等一律写全为
`constructor_destructor`、`sequential_container` 这类完整语义短语。

知识点名称必须是合法且非关键字的 C++ 函数标识符：

```regex
^[A-Za-z_][A-Za-z0-9_]*$
```

## 8. 可选视觉分组 `group`

分组用于在同一个 `code` 标签页内组织知识点，不会生成额外 C++ 类或成员函数。当前没有章节在用——RAII 之前用过 `raii`、`smart_pointer`、`move` 三个分组，后来判断意义不大而移除，改成每个知识点用自己的 `subchapter.source` 指向对应源文件，不再分组展示。分组机制本身还是 schema 支持的能力，需要时可以给新章节用。

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

普通章节省略 `ui`，根据 `content` 使用 `defaults.chapter_ui.code` 或 `defaults.chapter_ui.article`。只有欢迎页、动画或需要特殊输入控件的章节才覆盖：

```json
{
  "name": "Welcome",
  "title": "欢迎页面",
  "description": "介绍 Athena 的学习方式。",
  "content": "article",
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
- `article.document`：不便通过单页实验表达的理论正文；可以使用标题、列表、引用和代码块。

`description` 应描述目标和边界，不包含生成器命令，也不粘贴完整实现代码。

如果未来需要严格列举学习目标，可以通过新 schema 版本增加 `objectives`，当前版本不预先引入。

## 12. 路径和顺序

- 所有配置路径相对于仓库根目录。
- 使用 `/` 作为路径分隔符。
- 禁止绝对路径和 `..` 跳转。
- `categories`、`chapters`、`groups` 和 `subchapters` 的数组顺序就是显示顺序。
- 不从 `title` 推导任何路径或 C++ 名称。

## 13. 语义校验

下游解析器和未来的校验器必须检查：

- `schema` 是否为受支持版本。
- 必填字段是否存在且类型正确。
- 分类 `name` 全局唯一。
- 章节 `name` 在分类内唯一。
- 知识点 `name` 在章节内唯一。
- 派生键 `category.chapter.subchapter` 全局唯一。
- C++ 名称是否合法且不是关键字。
- `group` 引用是否存在。
- `content` 是否只能是 `code` 或 `article`。
- 默认文章页是否提供 `document`，并位于 `resources/articles/`。
- Blueprint、源码、Markdown 和资源图标路径是否有效。
- 所有章节都有可解析图标：自身图标或默认图标。
- 所有知识点都有可解析图标：自身图标或默认图标。
- 知识点 `importance` 若存在，必须是 0–5 的整数。

错误信息应给出结构路径和派生键，例如：

```text
athena.json categories[0].chapters[1].subchapters[2]:
duplicate subchapter name 'basic' in 'cpp.Reference'
```

## 14. 文件所有权

本文件只定义项目课程数据，不根据当前 `mainwindow.cc`、注册表或生成脚本的实现妥协。修改 schema 后，解析器、资源生成、UI 和代码生成应在后续步骤中统一适配。
