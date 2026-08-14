# CLAUDE.md — Athena 项目理解与协作约束

> 本文档记录本会话对 Athena 项目的理解、对话中形成的约定，以及对用户要求的归纳。
> 与 `AGENTS.md`（给 Codex 的项目级指令）互补；二者冲突时以 `AGENTS.md` 和 `docs/` 为准。

## 项目定位

Athena 是一个 **C++ 学习桌面应用**，本质是"草稿纸验算"工具——用于自我学习和知识点验证，**不是教程产品**。

由此推导出的取舍：

- 界面美观是次要的，核心是「切换知识点 → 看代码 → 运行验证」这条链路。
- 不追求完整的代码演示/教学排版，重点是可运行、可测试的知识点。
- 内容聚焦 **C++ 特有特性**，与 C 语言重叠的基础知识（原始指针等）主动淡化/删除，留待专门的 C 语言学习。

## 技术栈

- C++20、GTK4 / gtkmm4、GtkSourceView 5、MD4C、Meson、Blueprint、nlohmann/json
- 跨 Linux / macOS：已移除 libadwaita 依赖，界面用 GTK 内建样式 + 自定义 `style.css`

## 架构理解

- `resources/chapters.json` 是分类、章节、分组、知识点元数据的**唯一数据源**。
- 层级：`category → chapter`；`content: code` 继续细分为 `[可选 group] → subchapter`，`group` 只负责视觉组织，不生成额外代码层级。
- 章节只有 `code` 和 `article` 两种内容类型。`code` 的子章节对应可运行成员函数；`article` 从 `resources/articles/` 载入 Markdown，没有运行和结果概念。
- UI 只负责显示章节、收集操作、展示结果，不重复维护章节注册信息。
- 演示源码由运行时读取源文件显示，不在代码中手工复制字符串。
- `code` 与 `article` 分别共享自己的默认 Blueprint 模板并各自创建独立页面实例；只有欢迎页、动画或特殊交互章节才覆盖专用 BLP。
- 分类、章节、分组和子章节图标都来自 `chapters.json`，C++ 不按名称手写图标映射。

## 命名规则（对话中反复确立）

| 字段 | 规则 | 示例 |
|------|------|------|
| `chapter.name` | 稳定页面名；在 `code` 中也是 C++ 类名，PascalCase | `Reference`、`ProgramOrganization` |
| `subchapter.name` | 成员函数名，snake_case | `reference_basics`、`const_reference`、`move_semantics` |
| `title` / `description` | 中文描述 | `引用基础` |

- **避免缩写**：`ctor`/`dtor`/`ptr`/`seq`/`assoc`/`rw` 等一律写全（`constructor_destructor`、`sequential_container`）。
- **优先用完整语义短语避开关键字或标准库名冲突**：使用 `const_reference`、`return_by_reference`、`move_semantics`，避免只有尾缀下划线的 `const_`、`return_`、`move_`。确实无法自然扩展语义时，才使用尾缀下划线；禁止使用保留的前缀下划线形式。
- 分组名（`group.name`）承载语义时，子章节名不再重复该语义（如 `smart_pointer` 组下的 `unique`/`shared`/`weak`）。

## 用户的要求与偏好

1. **简洁不啰嗦**：命名简明扼要，去掉冗余信息（数字前缀、重复前缀、无意义后缀）。
2. **避免过度设计**：不轻易引入完整 MVC/MVP、注册表、工厂、自注册宏等框架机制；只有复杂度确实需要时才升级。优先"数据模型 + 轻量注册表 + 协调层"。
3. **数据驱动**：以 `chapters.json` 为单一数据源，不把元数据硬编码进 C++。
4. **淡化 C 语言重叠**：指针基础等 C 概念不纳入 C++ 学习，聚焦 C++ 特有的引用、RAII、智能指针、模板、移动语义等。
5. **运行时读源码**：源码框显示真实的 `.hpp` 文件内容，消除手工维护字符串副本。
6. **平衡粒度**：一个类对应一个主题，一个方法对应一个知识点，方法体约 10–30 行；知识点太少不硬拆，太多则合并。

## 技术约束

- 项目代码和教学示例（包括本项目头文件）优先使用 `using namespace std;`，减少 `std::` 前缀造成的视觉噪声；出现实际名称冲突时再显式限定。
- 用 RAII 表达资源所有权；默认 `const`、引用；不拥有所有权的裸指针仅限 GTK 控件。
- 源文件展示：开发期通过编译期注入的 `ATHENA_SOURCE_ROOT` 读磁盘文件；打包分发时应改为 GResource 嵌入。
- 演示类方法（成员函数）需为 public，以便注册表通过成员函数指针调用。

## 与 AGENTS.md 的关系

- `AGENTS.md` 是项目级规范（架构原则、代码生成规则、C++ 编码规则、验证要求），面向 Codex 等代码代理。
- 本文档补充 Claude 视角的**项目理解**和**用户偏好**，作为开发时的上下文指引。
- 实现若与 `docs/` 或 `AGENTS.md` 不一致，先指出差异，修复代码或更新文档保持同步。
