# ADR 0013：Python 独占作者配置校验，C++ 只解码规范化运行时 Catalog

- 日期：2026-08-21
- 状态：已接受
- 依据提交：（本 ADR 先于对应实现提交）

## 背景

`resources/athena.json` 是项目配置的唯一数据源，但此前 Python 生成器和 C++
`ChapterCatalog::from_json()` 都直接解释这份作者配置。两套实现分别处理默认图标、
Blueprint 资源路径、源码继承、重复名称、分组引用和 `importance`，已经出现行为差异：

- 文档要求 C++ 类名和成员函数名不能是关键字，Python 只检查标识符正则；
- Python 拒绝废弃的顶层 `handbook_documents`，C++ 会静默忽略；
- Python 拒绝越界 `importance`，C++ 会把它夹到 0–5；
- 未知字段缺少统一策略，拼写错误可能被某一侧忽略。

Athena 的配置随应用一起构建，不支持在运行时加载任意外部作者配置，因此没有必要
长期维护两套等价的严格校验器。

## 决策

- `resources/athena.json` 继续作为唯一的**作者配置**；作者格式使用直白的
  `format_version` 版本号。仓库使用 Python 实现自己的字段与语义校验，不暗示
  存在另一套标准校验文件或工具。
- `scripts/project_generator/model.py` 是唯一严格的作者侧校验与规范化入口，负责：
  必填字段和类型、允许字段、废弃字段、C++ 关键字、唯一性、引用关系、路径存在性、
  默认值、稳定函数 ID、源码继承以及 UI 资源路径派生。
- 构建时从已验证的内部模型生成 `chapter_catalog.generated.json`，以
  `/app/data/chapter_catalog.json` 打包进 GResource。该文件是构建产物，不提交，
  带独立的 `catalog_version` 版本号。
- C++ `ChapterCatalog` 只解码这份受信任的规范化 Catalog，不再读取
  `/app/data/athena.json`，也不再重复作者语义校验、默认值计算、路径派生、引用解析
  或数值修正。
- C++ 仍保留 JSON 语法、`catalog_version` 和必需运行时字段的最小检查。这类失败表示
  构建产物损坏或生成器与二进制版本不匹配，不作为作者配置错误提示。
- 作者配置出现未知字段时一律报错，防止拼写错误被静默忽略；已废弃字段给出带迁移
  说明的专门错误。
- `format_version` 平时保持不变；只有维护者重新组织字段时，才同步修改这个数字、
  生成器和配置参考文档。`catalog_version` 由生成器和 C++ 解码器一起维护，内容
  作者不需要填写或修改。

## 后果

- 作者配置错误只需在 Python 负面测试中覆盖，错误信息可以直接指向
  `categories[i].chapters[j].subchapters[k]`；C++ 测试只覆盖规范化数据的解码、查询
  和损坏检测。
- 默认值和派生规则只实现一次，Python 生成的 Registry、GResource、Catalog 与骨架
  共享同一个内部模型，不再发生同一配置在构建期与运行时含义不同的问题。
- 运行时资源不再包含原始 `athena.json`。需要诊断作者配置时应运行统一的
  `scripts/check.sh` 或生成器 `check`，而不是让应用尝试容错修复。
- 如果未来要支持用户在运行时加载外部 Catalog，应另行设计不受信任输入边界；不能
  直接把当前受信任解码器当作外部配置校验器。
