# ADR 0014：按页面与用例逐步拆分 MainWindow

- 日期：2026-08-21
- 状态：已接受，分步实施中
- 依据提交：（本 ADR 确定边界与实施顺序；实际完成情况以架构文档为准）

## 背景

`mainwindow.cc` 当前约 2650 行。它已经不再解析作者配置，也不维护手写课程注册表，
但仍同时承担以下职责：

- 分类导航、标签和页面缓存；
- 代码章节页面装配、知识点选择、源码定位和运行状态；
- 分类手册拼接、WKWebView 页面创建、缓存和跳转；
- 学习进度页面及图表控件装配；
- 设置、运行历史、AI Markdown 和 AI 自测对话框；
- AI 服务商选择、HTTP 请求、回答清理与题目 JSON 解码；
- 后台实验执行、耗时统计、源码快照和历史记录持久化。

这些职责虽然已拆成方法，但共享同一个窗口类，导致状态和回调捕获范围过大。继续在
同一文件增加功能会放大生命周期错误、界面状态不同步和难以单独测试的问题。

## 决策

不引入完整 MVC/MVP，也不一次性重写窗口。按功能边界逐步形成以下结构，文件名可在
实施时微调，但依赖方向不变：

```text
MainWindow：顶层窗口、分类导航、页面切换与模块生命周期
├── CodeChapterPage：代码页控件、知识点选择、源码与运行结果显示
│   └── ExperimentRunner：后台执行、耗时、快照与运行记录
├── HandbookPage：分类手册组装、ArticleView 生命周期与文档跳转
├── ProgressPage：把 CategoryProgress 渲染为统计卡、图表和章节列表
├── LearningDialogs：设置、运行历史、AI 回答和自测题对话框
└── AiService：服务商回退、HTTP 请求、文本清理和自测题解码
```

边界规则：

- `MainWindow` 只持有顶层 GTK 控件和各功能模块，负责导航，不再实现页面内部控件树。
- 页面模块接收已经解码的 `ChapterMeta`、`CategoryProgress` 等数据，不读取作者 JSON，
  不重新计算 ID、图标和源码继承。
- `AiService` 与 `ExperimentRunner` 不依赖 GTK；异步完成后通过结果对象或回调把数据
  交回表示层，只有表示层更新控件。
- `CodeChapterPage` 可以依赖 `ChapterCatalog`、`FunctionRegistry`、`ContentLoader`、
  `LearningStore` 和 `SourceLocator` 的窄接口；这些组件不能反向依赖页面或窗口。
- `HandbookPage` 独占它创建的 `ArticleView` 与宿主控件生命周期，避免窗口同时维护
  GTK 页面、原生 WebView 和多个平行缓存。
- `ProgressPage` 只渲染已经聚合的数据；统计口径继续留在不依赖 GTK 的
  `aggregate_category_progress()`。
- 跨模块共享状态使用稳定函数 ID 和明确的数据对象，不共享零散 GTK 控件指针。

## 实施顺序

按低风险到高风险逐步提交，每一步都保持应用可构建、可运行：

1. 提取不依赖 GTK 的 `AiService`、回答清理和自测题解码，并补纯 C++ 测试。
2. 提取 `ProgressPage`，复用现有 `CategoryProgress` 和 ChartView，不改变统计口径。
3. 提取设置、运行历史、AI 回答和自测题等叶子对话框。
4. 提取 `HandbookPage`，保留当前已经验证的常驻 WKWebView 生命周期规则。
5. 最后提取状态最多的 `CodeChapterPage` 与 `ExperimentRunner`，统一知识点激活、源码
   高亮、运行、输出和持久化回调。
6. 删除迁移后留在 `MainWindow` 的转发方法和无效状态；此时窗口只保留顶层协调。

## 后果

- 每个阶段会新增少量对象和构造参数，但换来更窄的状态范围和可单独测试的边界。
- 不以行数作为唯一目标；如果拆分后出现跨模块双向调用或共享控件指针，说明边界错误，
  不能仅为缩短文件继续拆类。
- 本 ADR 是后续实施合同。代码仍以 `MainWindow` 方法为主，但 `AiService` 和
  `ProgressPage` 已落地；架构文档必须持续区分“已经完成”和“计划拆分”，直到每个
  模块真正落地。
