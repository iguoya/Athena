# Athena 代码生成规范

## 1. 目标

代码生成的目标是把 `resources/chapters.json` 中可机器验证的课程结构转换为：

- Blueprint/GResource 构建输入。
- 稳定章节和知识点 ID。
- C++ 章节类声明或声明片段。
- 演示函数注册表。
- 新章节的一次性实现骨架。

生成器不负责根据自然语言自动产出最终教学代码。`description` 可以作为 Codex 或开发者编写实现时的需求，但生成的实现必须经过构建、测试和人工审查。

## 2. 当前状态

仓库现有生成脚本：

```text
scripts/gen_chapters_xml.py
```

它在 Meson 配置阶段：

1. 读取 `resources/chapters.json`。
2. 收集并校验 `ui_resource` 指向的 Blueprint 文件。
3. 更新 `resources/app.gresource.xml`。
4. 通过标准输出告诉 Meson需要编译哪些 `.blp` 文件。

它目前不会：

- 生成章节类。
- 生成成员函数声明或实现骨架。
- 生成 `subchapter_demos` 注册表。
- 完整校验章节和方法 ID。

因此，本规范后面的 C++ 生成流程属于目标设计，落地时需要同步修改 Meson、测试和文档。

## 3. 推荐生成器接口

建议新增统一入口：

```text
scripts/generate_chapters.py
```

推荐命令：

```sh
# 更新可反复生成的文件
python3 scripts/generate_chapters.py generate

# 只比较结果，不写文件，供 CI 使用
python3 scripts/generate_chapters.py check

# 为新增章节创建不存在的人工实现骨架
python3 scripts/generate_chapters.py scaffold --chapter cpp.Reference
```

如果更喜欢选项式接口，也可以使用 `--check` 和 `--scaffold`，但仓库内必须保持一种稳定形式。

退出码：

- `0`：成功，或 `check` 未发现差异。
- 非 `0`：配置非法、文件缺失、输出不同步或生成失败。

## 4. 生成流程

统一入口按以下顺序工作：

```text
读取 chapters.json
        |
        v
JSON Schema 校验
        |
        v
语义校验（ID、C++ 名称、路径、重复项）
        |
        v
构建内部规范模型
        |
        +--> GResource/Blueprint 输入
        +--> chapter_ids.generated.hpp
        +--> demo_registry.generated.cpp
        +--> 可选章节声明
        +--> scaffold：仅创建不存在的人工文件
```

所有输出应先在内存或临时目录生成，校验全部成功后再写入目标位置，避免失败时只更新一部分文件。

## 5. 文件所有权

### 5.1 生成器所有

建议目录：

```text
generated/
├── chapter_ids.generated.hpp
├── chapter_declarations.generated.hpp
└── demo_registry.generated.cpp
```

也可以放入 Meson 构建目录。无论位置如何，都必须：

- 文件名包含 `.generated.`。
- 首部包含生成来源和禁止编辑提示。
- 可以被生成器完整覆盖。
- 不接受人工业务逻辑。

示例文件头：

```cpp
// Generated from resources/chapters.json by scripts/generate_chapters.py.
// DO NOT EDIT. Modify the JSON configuration or generator instead.
```

### 5.2 人工或 Codex 所有

建议目录：

```text
language/cpp/references.hpp
language/cpp/references.cpp
tests/cpp/references_test.cpp
```

这些文件：

- 包含函数实现、教学示例和测试。
- 生成器只能在文件不存在时通过 `scaffold` 创建。
- 文件存在时，即使内容为空，生成器也不得覆盖。
- 删除知识点时不自动删除对应实现；应报告孤立实现，交由开发者处理。

## 6. 推荐生成内容

### 6.1 稳定 ID

输入：

```json
{
  "name": "reference_basics",
  "title": "引用基础",
  "description": "理解引用是对象的别名以及引用必须初始化。"
}
```

生成：

```cpp
namespace athena::chapter_ids {

inline constexpr std::string_view cpp_reference_reference_basics =
    "cpp.Reference.reference_basics";

} // namespace athena::chapter_ids
```

### 6.2 演示注册表

注册表必须使用完整 ID：

```cpp
registry.add(
    "cpp.Reference.reference_basics",
    bind_demo<athena::cpp::Reference>(
        &athena::cpp::Reference::reference_basics));
```

函数签名在同一 schema 版本内保持统一。第一阶段建议继续使用：

```cpp
void method(std::ostream& output) const;
```

### 6.3 章节骨架

`scaffold --chapter cpp.Reference` 可以首次创建：

```cpp
#pragma once

#include <iosfwd>

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

对应 `.cpp` 可以生成明确的待实现函数，但下一次运行不得覆盖：

```cpp
#include "references.hpp"

namespace athena::cpp {

void Reference::reference_basics(std::ostream& output) const {
    // TODO: Implement the lesson described in chapters.json.
}

} // namespace athena::cpp
```

## 7. 确定性要求

为了使 Git diff 和 CI 稳定：

- 固定 UTF-8 和 `\n` 换行。
- 按配置中的分类顺序、章节 `order`、分组顺序和知识点顺序输出。
- 不写入当前时间、用户名、绝对路径或随机值。
- 相同输入必须逐字节产生相同输出。
- 只有内容变化时才替换文件，避免无意义的重新编译。
- 格式由模板或统一格式化工具控制。

## 8. 安全写入要求

- 生成路径必须解析并确认位于仓库或构建目录内。
- 拒绝 JSON 中的绝对路径和 `..` 跳转。
- 写文件前完成所有 schema 和语义校验。
- 使用临时文件后原子替换生成文件。
- `scaffold` 遇到已存在文件时报告 `skipped`，不得截断文件。
- 普通 `generate` 命令不得删除人工文件。
- 删除过时的生成文件前，必须确认目标带有生成器签名。

## 9. Meson 集成

推荐将职责分开：

- Meson 构建时可以自动生成完全由生成器所有的注册表和 ID 文件。
- 人工实现骨架只能通过显式 `scaffold` 命令创建，不能作为普通构建副作用。
- 构建必须依赖 `chapters.json`、schema、模板和生成器脚本。
- 生成输出优先位于 Meson 构建目录，避免污染源码树；需要提交并由 CI 检查的生成文件除外。

概念示例：

```meson
chapter_codegen = custom_target(
  'chapter-codegen',
  input: chapters_json,
  output: [
    'chapter_ids.generated.hpp',
    'demo_registry.generated.cpp',
  ],
  command: [python, generator, 'generate', '--input', '@INPUT@',
            '--output-dir', meson.current_build_dir()],
)
```

实际实现时必须根据脚本接口调整，不能直接复制概念示例并假设可运行。

现有 `gen_chapters_xml.py` 会写入源码树中的 `resources/app.gresource.xml`。重构时建议让统一生成器在构建目录生成 GResource XML，或明确把该文件视为需要提交并由 `check` 验证的生成产物。

## 10. Codex 编写成员函数的流程

当用户要求根据 `description` 实现章节时，Codex 应：

1. 读取 `AGENTS.md`、本规范和 `CHAPTER_SCHEMA.md`。
2. 定位完整演示 ID、章节类和方法名。
3. 确认生成声明与人工实现文件的所有权。
4. 只编辑人工实现和测试，不直接编辑 `.generated.*`。
5. 让输出具有明确、可重复的教学结果。
6. 添加覆盖主要语义和边界条件的测试。
7. 运行生成检查、Meson 构建和测试。
8. 如果 `description` 不足以决定教学行为，先给出合理假设；只有会显著改变课程目标时才请求用户选择。

## 11. CI 检查

完整生成器实现后，CI 至少检查：

```sh
python3 -m json.tool resources/chapters.json >/dev/null
python3 scripts/generate_chapters.py check
meson setup builddir
meson compile -C builddir
meson test -C builddir --print-errorlogs
```

`check` 必须覆盖：

- schema 和语义校验。
- 生成文件与当前 JSON 是否一致。
- 每个可运行知识点是否有注册项。
- 重复或孤立的完整 ID。
- 被 JSON 引用的 Blueprint 和源码文件是否存在。
