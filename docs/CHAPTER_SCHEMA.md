# chapters.json 配置规范

## 1. 设计目标

`resources/chapters.json` 是 Athena 课程结构的权威来源。Schema 先于解析器、注册表和代码生成器定义；下游代码必须适配本规范，不能用现有实现反向限制配置结构。

配置表达三个核心层级：

```text
category                     课程分类、左侧导航、C++ 命名空间
└── chapter                  一级大章节、标签页、C++ 类
    └── subchapter           可运行知识点、成员函数
```

`group` 是章节内部可选的视觉分组，不增加代码层级。`description` 是教学概要，也可作为 Codex 编写实验代码时的需求输入。

## 2. 完整示例

```json
{
  "schema": 1,
  "defaults": {
    "chapter_ui": {
      "blueprint": "resources/ui/chapters/empty_chapter.blp"
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
          "source": "language/references/reference.hpp",
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
| `schema` | integer | 是 | Schema 版本；当前为 `1` |
| `defaults` | object | 是 | 通用界面和图标默认值 |
| `categories` | array | 是 | 有序课程分类列表 |

数组顺序就是界面顺序，不再保存冗余的 `order` 字段。

## 4. 默认值

### 4.1 `defaults.chapter_ui`

所有普通一级章节共享的 Blueprint 模板：

```json
{
  "chapter_ui": {
    "blueprint": "resources/ui/chapters/empty_chapter.blp"
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

章节页面模板的根控件统一使用 `chapter_page`，不在每章重复配置根控件 ID。

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
| `name` | string | 是 | 稳定分类名称，也是目标命名空间名称 |
| `title` | string | 是 | 左侧导航显示标题 |
| `description` | string | 是 | 分类学习范围概要 |
| `icon` | icon | 是 | 分类导航图标 |
| `chapters` | array | 是 | 有序一级章节列表 |

示例映射：

```text
category.name = cpp
    -> 左侧分类键 cpp
    -> C++ 命名空间 athena::cpp
```

分类 `name` 使用小写 ASCII `snake_case`：

```regex
^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$
```

## 6. 一级章节 `chapter`

一级章节是课程中的大概念，例如“引用”“RAII 与资源管理”“STL 容器”。每个一级章节对应一个标签页和一个同名 C++ 类。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 稳定章节名，也是 C++ 类名 |
| `title` | string | 是 | 标签页显示标题 |
| `description` | string | 是 | 整章概要 |
| `icon` | icon | 否 | 标签页图标；缺省时继承默认章节图标 |
| `ui` | object | 否 | 特殊 Blueprint 覆盖 |
| `source` | string | 否 | 代码框显示的源码路径 |
| `groups` | array | 否 | 知识点的视觉分组元数据 |
| `subchapters` | array | 是 | 有序可运行知识点列表，可以为空 |

映射示例：

```text
chapter.name = Reference
    -> 标签页的稳定名称 Reference
    -> C++ 类 athena::cpp::Reference
```

具体课程类直接使用主题名，例如 `Reference`、`RAII`、`STLContainer`，不添加统一的 `Chapter` 后缀。

章节名称必须是合法且非关键字的 C++ 类型标识符：

```regex
^[A-Za-z_][A-Za-z0-9_]*$
```

## 7. 二级知识点 `subchapter`

二级知识点是最小可运行教学单元，每项对应章节类的一个成员函数和界面中的一个运行入口。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 稳定知识点名，也是成员函数名 |
| `title` | string | 是 | 知识点显示标题 |
| `description` | string | 是 | 实验目标和内容概要 |
| `icon` | icon | 否 | 知识点图标；缺省时继承默认图标 |
| `group` | string | 否 | 所属视觉分组的 `name` |
| `source` | string | 否 | 该知识点专用的源码展示文件 |

映射示例：

```text
category.name = cpp
chapter.name = Reference
subchapter.name = basic

派生查找键：cpp.Reference.basic
C++ 目标：athena::cpp::Reference::basic(...)
```

不再同时保存 `id` 和 `method`。在当前一对一模型中，`name` 同时承担稳定局部名称和成员函数名，避免重复字段发生不一致。

知识点名称必须是合法且非关键字的 C++ 函数标识符：

```regex
^[A-Za-z_][A-Za-z0-9_]*$
```

## 8. 可选视觉分组 `group`

分组用于在同一标签页内组织知识点。例如 RAII 章节中的 `raii`、`smart_pointer` 和 `move`。分组不会生成额外 C++ 类或成员函数。

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

普通章节省略 `ui`，使用 `defaults.chapter_ui`。只有欢迎页、动画或需要特殊输入控件的章节才覆盖：

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
- Blueprint、源码和资源图标路径是否有效。
- 所有章节都有可解析图标：自身图标或默认图标。
- 所有知识点都有可解析图标：自身图标或默认图标。

错误信息应给出结构路径和派生键，例如：

```text
chapters.json categories[0].chapters[1].subchapters[2]:
duplicate subchapter name 'basic' in 'cpp.Reference'
```

## 14. 文件所有权

本文件只定义课程数据，不根据当前 `mainwindow.cc`、注册表或生成脚本的实现妥协。修改 schema 后，解析器、资源生成、UI 和代码生成应在后续步骤中统一适配。
