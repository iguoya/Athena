# chapters.json 配置规范

## 1. 文档状态

`resources/chapters.json` 当前采用“顶层对象按分类分组”的旧结构。本规范同时记录当前字段，并定义向稳定、可生成 C++ 代码的新结构迁移的目标。

在生成器和解析器完成迁移前，不应一次性把现有 JSON 改成目标结构。新增字段应保持向后兼容，并配套校验。

## 2. 当前结构

当前简化结构：

```json
{
  "cpp": [
    {
      "order": 2,
      "title": "引用",
      "source": "language/references/reference.hpp",
      "ui_resource": "resources/ui/chapters/empty_chapter.blp",
      "subchapters": [
        {
          "name": "",
          "items": [
            { "method": "basic", "title": "引用基础" }
          ]
        }
      ]
    }
  ]
}
```

当前字段：

| 字段 | 类型 | 必填 | 当前含义 |
|---|---|---:|---|
| 顶层键 | string | 是 | 分类 ID，例如 `cpp`、`da`、`dp` |
| `order` | integer | 是 | 分类内部的显示顺序，当前还被用作临时章节键 |
| `title` | string | 是 | 用户可见章节标题 |
| `ui_resource` | string | 是 | 仓库根目录相对的 Blueprint 文件路径 |
| `source` | string | 否 | 源码展示文件路径 |
| `subchapters` | array | 否 | 子分组列表 |
| `subchapters[].name` | string | 否 | 分组 ID；空字符串表示不显示分组标题 |
| `subchapters[].items` | array | 是 | 知识点列表 |
| `items[].method` | string | 是 | 当前知识点方法键 |
| `items[].title` | string | 是 | 用户可见知识点标题 |

当前 `method` 只在局部具有含义，无法单独保证全局唯一。运行时查找必须包含分类和章节上下文。

## 3. 目标结构

推荐逐步迁移为显式版本化结构：

```json
{
  "schema_version": 1,
  "categories": [
    {
      "id": "cpp",
      "title": "C++",
      "icon": "applications-development-symbolic",
      "namespace": "athena::cpp",
      "chapters": [
        {
          "id": "references",
          "order": 2,
          "title": "引用",
          "class": "ReferencesChapter",
          "source": "language/cpp/references.cpp",
          "ui_resource": "resources/ui/chapters/empty_chapter.blp",
          "subchapters": [
            {
              "id": "fundamentals",
              "title": "",
              "items": [
                {
                  "id": "basic",
                  "method": "basic",
                  "title": "引用基础",
                  "description": "讲解引用的声明、绑定和别名语义"
                },
                {
                  "id": "const_reference",
                  "method": "const_reference",
                  "title": "const 引用",
                  "description": "讲解 const 引用、临时对象和生命周期"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## 4. 目标字段定义

### 4.1 根对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `schema_version` | integer | 是 | 配置格式版本；不支持的版本必须报错 |
| `categories` | array | 是 | 分类数组，至少包含一个分类 |

### 4.2 分类

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `id` | string | 是 | 稳定分类 ID |
| `title` | string | 是 | 显示标题 |
| `icon` | string | 否 | GTK 图标名 |
| `namespace` | string | 条件必填 | 生成 C++ 类时使用的命名空间 |
| `chapters` | array | 是 | 章节数组 |

### 4.3 章节

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `id` | string | 是 | 分类内稳定且唯一的章节 ID |
| `order` | integer | 是 | 显示顺序，分类内不得重复 |
| `title` | string | 是 | 显示标题 |
| `class` | string | 条件必填 | 有可执行知识点时的 C++ 类名 |
| `source` | string | 否 | 源码展示路径 |
| `ui_resource` | string | 是 | Blueprint 文件路径 |
| `subchapters` | array | 否 | 子分组数组 |

### 4.4 子分组

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `id` | string | 是 | 章节内稳定的分组 ID |
| `title` | string | 否 | 显示标题；空字符串表示隐藏标题 |
| `items` | array | 是 | 知识点数组 |

分组只用于组织和显示，不进入默认演示 ID。若未来允许同一章节不同分组出现相同知识点 ID，应先升级 schema 版本并修改 ID 规则。

### 4.5 知识点

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `id` | string | 是 | 章节内稳定的知识点 ID |
| `method` | string | 是 | 对应 C++ 成员函数名 |
| `title` | string | 是 | 显示标题 |
| `description` | string | 否 | 教学目标和实现需求 |
| `source` | string | 否 | 可选的知识点专用源码路径 |

知识点完整 ID：

```text
<category.id>.<chapter.id>.<item.id>
```

例如：

```text
cpp.references.basic
```

## 5. 命名规则

### 5.1 JSON ID

分类、章节、分组和知识点 ID 使用：

```regex
^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$
```

允许：

```text
cpp
references
const_reference
smart_pointer
```

禁止：

```text
C++
const-reference
引用
01_basic
```

### 5.2 C++ 类名

`class` 使用 PascalCase，并以字母或下划线开头：

```regex
^[A-Za-z_][A-Za-z0-9_]*$
```

推荐以 `Chapter` 结尾，例如 `ReferencesChapter`。

### 5.3 C++ 方法名

`method` 使用合法的 C++ `snake_case` 标识符：

```regex
^[A-Za-z_][A-Za-z0-9_]*$
```

同时必须拒绝 C++ 关键字。为了避免尾部下划线式规避关键字，推荐把当前 `const_`、`return_` 迁移为 `const_reference`、`return_reference`。

### 5.4 标题

`title` 是显示文本，可以使用中文、空格和标点。程序逻辑不得依赖标题内容。

## 6. 路径规则

- 所有路径使用 `/`，并相对于仓库根目录。
- 禁止绝对路径和 `..` 路径跳转。
- `ui_resource` 必须以 `.blp` 结尾且文件存在。
- `source` 必须位于项目允许展示的源码目录内。
- 多个章节可以共享同一 Blueprint 模板。
- 不同 Blueprint 文件不能生成冲突的 GResource 输出名称。

## 7. 语义校验

仅通过 JSON 语法校验还不够。生成器必须检查：

- `schema_version` 是否受支持。
- 所有必填字段是否存在且类型正确。
- 分类 ID 全局唯一。
- 章节 ID 在分类内唯一。
- `order` 在分类内唯一且为正整数。
- 知识点 ID 和 `method` 在章节内唯一。
- 组合后的完整演示 ID 全局唯一。
- 类名、方法名和命名空间是合法 C++ 标识符且不是关键字。
- Blueprint 和源码路径符合规则。
- 有可运行知识点的章节必须提供 `class`。
- 生成注册表时，每个知识点都能解析到一个实现或明确标记为尚未实现。

校验错误必须给出 JSON 路径和稳定 ID，例如：

```text
chapters.json: categories[0].chapters[1].subchapters[0].items[2]:
duplicate demo id 'cpp.references.basic'
```

## 8. 兼容迁移建议

建议按以下顺序迁移现有配置：

1. 给现有章节增加 `id`，保留顶层分类对象结构。
2. 给分类元数据增加独立区域，或直接迁移到 `categories` 数组。
3. 给有知识点的章节增加 `class` 和 `namespace`。
4. 给知识点增加显式 `id`，暂时允许其默认等于 `method`。
5. 修改运行时使用完整复合 ID。
6. 最后启用 C++ 注册表和骨架生成。
