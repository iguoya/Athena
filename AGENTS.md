# Athena 项目协作规则

本文档是 Athena 仓库中 Codex 及其他代码代理的项目级指令。修改代码前先理解当前实现，不得把目标设计误认为已经落地的功能。

## 必读文档

开始设计或修改代码前，按任务范围阅读：

- `docs/ARCHITECTURE.md`：系统边界、依赖方向和目标架构。
- `docs/CHAPTER_SCHEMA.md`：`resources/chapters.json` 的字段、标识符和校验规则。
- `docs/CODE_GENERATION.md`：代码生成流程、文件所有权和 Meson 集成约束。

若实现与文档不一致，先指出差异；修复代码或更新文档时，保持二者同步。

## 项目技术栈

- C++17
- GTK4 / gtkmm 4
- Meson
- Blueprint UI
- nlohmann/json

除非任务明确要求，不引入新的生产依赖，不更换 UI 技术栈，也不把项目改造成完整 MVC/MVP 框架。

## 架构原则

- `resources/chapters.json` 是分类、章节、分组和知识点元数据的唯一数据源。
- UI 层只显示章节、收集用户操作并展示执行结果，不维护重复的章节注册信息。
- JSON 解析、元数据校验、演示函数注册和 GTK 界面协调应保持职责分离。
- 使用稳定的复合 ID 标识知识点，目标格式为 `category.chapter.method`。
- 不使用中文标题、数组位置或 `order` 作为程序内部永久标识。
- `order` 只负责显示顺序；标题只负责界面显示。
- C++ 类名和成员函数名必须由机器可校验的 ASCII 标识符明确指定，禁止从中文标题自动推导。
- 优先采用“数据模型 + 注册表 + 轻量协调层”，只有复杂度确实需要时才进一步引入 MVC/MVP。

## 代码生成规则

- 当前仓库只实现了 Blueprint/GResource 清单生成；完整的 C++ 章节类和注册表生成仍是目标能力。
- 生成器必须确定性输出：相同输入产生完全相同的文件内容和顺序。
- 自动生成文件必须带有 `DO NOT EDIT` 提示，并使用 `.generated.hpp` 或 `.generated.cpp` 后缀。
- 禁止直接修改自动生成文件；应修改 `chapters.json`、生成模板或生成器。
- 生成器可以反复覆盖生成的注册表、ID 常量和声明文件。
- 生成器不得覆盖已经存在的人工实现文件、教学示例或测试。
- 首次创建成员函数实现骨架时采用“仅当文件不存在时创建”的策略。
- 自然语言 `content`/`description` 是教学需求，不应由普通模板生成器直接转换成未经审查的 C++ 实现；它可以作为 Codex 编写实现的输入。
- 在 C++ 生成器落地前，不得在构建规则或文档中假装相关命令已经可用。

## C++ 编码规则

- 使用 RAII 表达资源所有权。
- 禁止拥有所有权的裸指针；GTK 提供的非拥有型控件指针除外，并应保持生命周期关系清晰。
- 头文件中禁止 `using namespace`，也不要把常用标准库类型导入全局命名空间。
- 默认使用 `const`、引用和明确的所有权语义。
- 公共类型放入 `athena` 命名空间；章节实现使用相应子命名空间，例如 `athena::cpp`。
- JSON 字段访问必须处理缺失字段、类型错误、重复 ID 和非法 C++ 标识符。
- 错误信息应包含分类 ID、章节 ID 或方法 ID，便于定位配置。
- 新增章节演示时不得在 `mainwindow.cc` 中继续堆叠手写映射；应优先扩展独立注册表或生成流程。

## GTK 与 Blueprint 规则

- 界面结构优先写在 `.blp` 文件中，C++ 只负责动态内容、信号和状态协调。
- 不在窗口类中实现教学业务逻辑。
- GResource 路径必须由配置和构建生成流程保持一致。
- 共享 Blueprint 模板时，不得假设不同分类的 `order` 全局唯一。
- Builder、页面缓存和初始化状态使用完整章节 ID 作为键。

## 修改流程

1. 阅读相关文档和现有实现。
2. 明确改动属于配置、生成器、生成代码、人工实现还是 UI。
3. 先更新 schema/校验，再依赖新增字段。
4. 修改 `chapters.json` 后运行 JSON 和资源生成检查。
5. 构建并测试受影响部分。
6. 如果行为或架构边界发生变化，同步更新 `docs/`。

## 验证要求

现阶段至少执行：

```sh
python3 -m json.tool resources/chapters.json >/dev/null
meson setup builddir --reconfigure
meson compile -C builddir
meson test -C builddir --print-errorlogs
```

如果构建目录尚不存在，使用：

```sh
meson setup builddir
meson compile -C builddir
```

未来加入统一章节生成器后，还必须提供并运行 `--check` 模式，使 CI 能发现配置与生成文件不同步，但在该命令真正实现前不要把它列为必过命令。

## 代码评审重点

- 检查 JSON 方法 ID 与注册表键是否完全一致。
- 检查分类之间是否因相同 `order` 或方法名发生键冲突。
- 检查生成器是否可能覆盖人工代码。
- 检查新增元数据是否在 schema、解析器和文档中同步。
- 检查 UI 是否重复维护 `chapters.json` 已经提供的数据。
- 检查源文件展示是否依赖不可移植的编译期绝对路径。
