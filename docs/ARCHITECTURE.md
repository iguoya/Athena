# Athena 当前架构

本文只描述当前实现、仍有效的边界和明确的缺口。开发入口见 [文档索引](README.md)，
教学设计见 [LEARNING_DESIGN](LEARNING_DESIGN.md)，决策背景见 [ADR 索引](decisions/README.md)。
旧架构快照和布局探索已进入 [历史归档](archive/README.md)，不作为现状说明。

## 1. 定位与当前阶段

Athena 是自用的 C++ 渐进学习平台：解释原理与用途，借助图示建立理解，穿插真实实验，
观察并解释结果，再迁移到实际代码。学习页应独立承担这段教学，手册与 AI 是可选补充。
它不以完整教程产品、通用内容编辑器或 IDE 为目标。

当前技术栈是 C++20、GTK4/gtkmm4、Blueprint、GtkSourceView 5、MD4C、nlohmann/json、
SQLite 和 Meson。macOS、Ubuntu 共用 GTK 内容渲染；没有 WebView 文章后端。

已具备配置生成、真实源码定位与执行、分类索引、手册、进度、自测及原生学习场景入口。
类型与表达式使用 `TypeSemanticsLessonPage`；其他语言章节主要使用标准代码页。
多媒体教案已按 ADR 0027 确定方向，完整讲解与可控动画仍需逐项落地，不能据此宣称已经实现。

## 2. 配置与构建数据流

```text
resources/athena.json
  → scripts/project_generator/model.py（唯一作者配置校验与规范化）
      → chapter_catalog.generated.json → ChapterCatalog（运行时只解码）
      → function_registry.generated.cc → FunctionRegistry
      → app.gresource.xml + Blueprint 编译输入 → 应用资源
      → 显式 scaffold（只创建不存在的人工实现文件）
```

- 稳定知识点 ID 为 `category.name.chapter.name.subchapter.name`；标题与数组位置不是身份。
- 配置定义导航、知识点元数据、实现与资源引用，不保存 GTK 状态、教学函数体或另一份正文。
- Catalog、注册表与资源清单只生成到构建目录。禁止手改生成文件，普通构建不产生教学骨架。
- 配置契约详见 [CHAPTER_CONFIG](CHAPTER_CONFIG.md)，生成与文件所有权详见
  [CODE_GENERATION](CODE_GENERATION.md)，此处不重复字段表。

## 3. 模块职责

| 边界 | 当前模块 | 负责什么 |
|---|---|---|
| 导航协调 | `MainWindow`、`ChapterPageStack` | 分类与章节切换、懒加载、跨页返回、模块生命周期 |
| 目录与统计数据 | `ChapterCatalog`、`KnowledgeGraph`、`progress_stats` | 查询元数据、前置依赖与统计计算，不依赖 GTK |
| 注册与课程实现 | `FunctionRegistry`、`language/` | 通过稳定 ID 执行真实 C++ 成员函数 |
| 内容能力 | `ContentLoader`、`SourceLocator`、`DocModel` | 读取资源/源码、定位函数、将 Markdown 解析成结构化块 |
| 页面 | `ui/` 各 Page/Dialog | 独占对应控件树、页面状态和用户操作 |
| 呈现 | `DocumentView`、`render/` 图表 | 文档块与图表呈现，不决定课程或评分规则 |
| 后台服务 | `ExperimentRunner`、`AiService` | 执行与请求，返回普通数据，不直接更新 GTK 控件 |
| 持久化 | `LearningStore` | 熟练度、AI 讲解缓存与设置；不持有 UI |
| 综合实践 | `practice/pocket_cube/`、`PocketCubePage` | 魔方状态、操作与可视化；状态模型可独立测试 |

`ExperimentRunner` 通过 GLib 主循环交付结果；“不更新 GTK 控件”不等于完全不依赖 GLib。
`athena-core` 是应用与核心测试共用的内部静态库；具体源码归属以 `meson.build` 为准。

## 4. 学习与运行路径

### 学习页面

- `TypeSemanticsLessonPage`：Blueprint 组织原生学习内容，模块填充预测单元与图解。
  页面顺序不来自 Markdown 标题。后续补齐讲解与多媒体，见教案规范。
- `CodeChapterPage`：保留的标准知识点列表，提供实验、AI 讲解与自测等动作。
- `WorkbenchPage`：旧式 Markdown 分节工作台，仍有代码和配置支持；属于兼容能力，
  当前课程配置未启用它，不作为新学习页模板。
- `HandbookPage`：按分类拼接 `handbook_documents`，经 `DocModel → DocumentView`
  显示。`overview_document` 提供可选回查入口，不决定学习页布局或必修内容。

### 真实实验

```text
学习页 → ExperimentSelection + 导航回调 → MainWindow
       → ExperimentPage → ExperimentDock → ExperimentRunner → FunctionRegistry
                                             ↓
                                     ExperimentResult → 主线程显示
```

专注实验位于主窗口 Stack，当前验证工作台为源码与运行观察分栏；不是独立实验对话框。
同一时刻只运行一个实验，不排队；运行中禁止把旧结果切换写入另一个知识点。
返回行为由 MainWindow 保存来源页并协调。学习页不持有实验页内部控件。

教学成员函数向 `ostream` 输出，源码框展示真实文件：开发期优先仓库源码，安装后使用
GResource 内置副本。函数定位不依赖安装机器上的编译期绝对路径。
编译失败案例尚未成为交互执行能力，作者注释和打印说明不能当作编译诊断。

### AI 与学习记录

`LearningDialogs` 装配设置、自测、讲解模块；AI 请求和解码由 `AiService` 负责，
界面负责异步交接。服务商配置与缓存细节看对应实现，不在架构文档固定模型名称。

当前熟练度规则仍按完整 AI 自测正确率乘 5 向下取整，最新一次完整成绩覆盖旧值；
5 星在现有统计中计为已掌握。这是当前实现口径，不等同于长期掌握的证明，本次文档整理不改评分。
运行历史与隐藏笔记已退出运行时；旧数据库的历史表/列保留，不读写、不做破坏性迁移。

## 5. 依赖与协作约束

- 页面使用领域数据、内容、服务和存储；这些模块不得反向依赖 MainWindow 或持有 GTK 控件。
- 页面之间不互相调用；跨页导航通过稳定 ID、小数据对象和回调交给 MainWindow。
- 领域模型与服务结果不携带页面控件；异步回调须遵守持有者生命周期和主线程更新约束。
- 静态与半静态控件树用 Blueprint，重复条目优先用模板；代码负责数据、状态和信号。
  动态图形放入独立呈现模块，语义状态与绘制分离；不为每个场景建立一套执行器。
- 新的专属页面可能需要增加页面装配分支；不借机恢复手写课程注册表。只有实际复用需求
  出现时才增加接口或工厂，不为了模式而引入完整 MVC/MVP。
- 共享业务代码没有平台分支；平台差异限制在已有适配与打包边界。Ubuntu 不链接 Apple Framework。
- 手册、学习页、实验可有不同表达，但语义条件一致；不以现有函数数量反推应教授的知识。

拆分模块前的简短检查见 [CODE_ROLES](CODE_ROLES.md)。具体编码约束以根目录 AGENTS.md 为准。

## 6. 验证与下一步边界

统一入口为 `scripts/check.sh`，依次检查 JSON、生成器、Meson 构建与测试。
共享代码变更需要 Ubuntu 核心测试与 Meson 构建；页面/资源变更还需 GTK 冒烟，
CI 使用 `xvfb-run` 提供显示环境。构建通过不能替代实际学习路径和视觉验证。

近期优先核对教学语义、完成自足讲解样板并验证可视化的解释价值。当前需记住的缺口：

- 多数配置章节尚无实现；标准代码页与原生场景并存，不宣称课程全量完成。
- 预测反馈主要依据预设答案；概念图、实际运行和编译诊断尚未形成统一证据交互。
- `WorkbenchPage` 与 `learning_units` 是保留的兼容路径，删除前需要独立确认配置与资源引用。
- Linux CI/发行脚本仍安装旧 WebKitGTK、md4c-html 包；Meson 内容渲染已不用它们，
  后续清理构建环境时再处理，不把“未链接”写成“所有安装脚本已清干净”。

发布规则、签名与包验证统一见 [RELEASE](RELEASE.md)，不在本文重复维护发行流程。
