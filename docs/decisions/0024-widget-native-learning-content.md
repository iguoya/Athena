# ADR 0024：学习内容统一由 GTK 控件承载，退出 Markdown/WebView 路线

- 日期：2026-09-08
- 状态：已接受，分阶段实施中
- 依据：`docs/ARCHITECTURE.md` 第 8 节「学习内容的界面承载模型」；
  `docs/LEARNING_WORKSPACE_FLOW_SKETCH.html`；对 ADR 0020 / 0022 / 0023
  原型的实际使用反馈
- 取代：ADR 0003、ADR 0017；修订 ADR 0012、ADR 0020、ADR 0023 中依赖
  `ArticleView` 的部分

## 背景

到 ADR 0023 为止，Athena 的学习内容分两条渲染路线：

- **成篇理论手册**：`resources/articles/**.md` → MD4C → HTML → `ArticleView`
  （macOS WKWebView / Ubuntu WebKitGTK 6.0），纯展示。
- **知识点实验、学习流引导**：GTK 控件树（Blueprint + 代码装配），已经
  完全不经过 Markdown。

连续学习流草图收敛后，一个知识点的界面顺序是「核心问题 → 预测 → 真实源码
→ 运行 → 预期/实际对照 → 迁移」。这条流里只有「核心问题」「概念句」等
少量文字来自文档，其余都是控件。继续维护一套 Markdown→HTML→WebView 栈
只为渲染这些文字，带来的成本与收益不匹配：

- WebView 是内容渲染层仅存的平台分支，两个后端（`article_view_macos.mm`、
  `article_view_webkitgtk.cc`）要各自履行加载、锚点、字号、主题、外链契约。
- 文档与实验分属两个渲染器，天然割裂：文档里的元素无法直接成为可交互
  控件，实验的状态也无法反向影响文档呈现。
- HTML 的字号 / 主题 / 无障碍要在 WebView 内单独处理，与应用其余部分不
  共享 GTK CSS 与焦点链。

方向决策：**学习内容（成篇理论 + 知识点实验 + 学习流引导）统一由 GTK
控件承载**，Markdown/WebView 退出内容载体角色。

## 决策

### 1. 内容由控件流承载

- 一个学习页面是 `Gtk::ScrolledWindow > Gtk::Box(vertical)`，按顺序容纳
  标题、段落、列表、代码块、表格、图、以及预测 / 运行 / 对照等交互控件。
- **Blueprint 描述静态与半静态结构**：页面骨架、每种内容块的模板、每种
  学习流阶段卡的模板、说明面板。
- **代码按数据实例化模板**：文档有几段、几个小节、几张表，知识点有几个，
  由内容数据在运行时决定，用 `Gtk::Builder` 循环实例化 `.blp` 模板或按
  结构直接构建，遵循 `AGENTS.md`「GTK 与 Blueprint 规则」。

### 2. 退出 Markdown/WebView 内容路线

分阶段移除（见「分阶段实施」）：

- `render/article_view.h`、`article_view_macos.mm`、
  `article_view_webkitgtk.cc`、`article_view_unavailable.cc`
- `render/markdown_renderer.*`、`ui/markdown_fallback.*`
- `ui/handbook_page.*` 的 WebView 依赖（页面本身按新渲染器重写）
- 构建依赖：`md4c` / `md4c-html`、`webkitgtk-6.0`、macOS `WebKit` framework
- `ArticleView` 相关：`m_article_views`、`scroll_to_anchor()`、
  `create_platform_article_view`、常驻 WKWebView 懒构建逻辑

`ui/ai_markdown_dialog` 与 AI 讲解 / 自测：AI 自测已用 GTK 控件渲染
（ADR 0015），不受影响；AI 讲解走 `show_static_markdown` / `show_ai_markdown`，
需要改用新的控件文档渲染器（见第 4 点），这是它与手册「共用底层 Markdown→HTML
渲染函数」关系的自然延续。

### 3. HTML 能力的控件替代

| 原 HTML 能力 | 控件替代 |
|---|---|
| 段落 / 标题 / 行内强调 | `Gtk::Label`（`use-markup`，Pango `<b>` `<tt>` `<span>`） |
| 无序 / 有序列表、引用块 | `Gtk::Box` 纵向 + 缩进 + 项目符号 `Label` |
| 代码块 | `GtkSourceView` 只读，复用 `cpp_syntax_highlighter` |
| 表格 | `Gtk::Grid`，表头行加 CSS class |
| 图 | 静态 SVG（`Gtk::Picture` + librsvg）或 `Gtk::DrawingArea` + Cairo；沿用 `AGENTS.md`「优先静态 SVG」约定 |
| H1–H3 目录 | 侧栏 `Gtk::ListBox`，记录每个标题控件，点击时 `ScrolledWindow` 滚到它 |
| 锚点跳转 | 标题控件登记进映射表，跳转 = 滚动到对应控件 |
| 字号 / 明暗主题 | GTK CSS，天然跟随应用设置，不再有 WebView 内单独一套 |
| 外部链接 | `Gtk::LinkButton` / `gtk_show_uri` |

### 4. 内容源格式：保留 Markdown

作者继续在 `resources/articles/**.md` 写 Markdown，写作方式完全不变，
只更换渲染目标：

- 解析产出**结构化「块序列」**（标题 / 段落 / 列表 / 代码块 / 表格 /
  图 / 引用块 …），不再产出 HTML。
- 运行期由「控件文档渲染器」遍历块序列，按块类型实例化对应控件
  （见第 3 点的替代表）。
- 解析器可沿用 MD4C（只取其 SAX 回调，丢弃 md4c-html），或改用纯
  Python / C++ 解析；解析器选型在阶段 1 原型里定。
- 行内强调沿用现约定：`**加粗**` 琥珀色重点、`***加粗斜体***` 红色
  陷阱（`AGENTS.md` 已有），转成 Pango `<span>` 前景色。

不采用 JSON / 结构化数据描述正文：长文写作成本高，且容易写成源码
说明书，与「文档由知识点主导、不是实现说明」的原则冲突。

### 5. 跨平台

内容渲染不再有平台分支。macOS 与 Ubuntu 用同一套 GTK 控件与 CSS。
`render/` 下只剩 Cairo / SVG 绘图，无 Objective-C++ 内容渲染源文件。
Meson 不再按平台选择 WebView 后端，也不再链接 `webkitgtk-6.0` 或
Apple `WebKit`。

## 分阶段实施

1. **控件文档渲染器原型**：把一份代表性 `.md`（`type_semantics_overview.md`）
   渲染成 `ScrolledWindow > Box` 控件流，覆盖标题、段落、强调、列表、
   代码块、表格、SVG 图、侧栏目录、锚点跳转。与 WebView 版并存对照。
2. **「类型推导」章节整合验证**：文档正文 + 闭环引导（核心问题 / 预测 /
   对照 / 迁移）+ 实验，全部在一个控件流里跑通，能编译运行、过
   `scripts/check.sh`。
3. **迁移其余 cpp 手册文档**，逐份切换到新渲染器。
4. **移除 WebView / MD4C 栈与依赖**，删除 `ArticleView` 及两个平台后端，
   更新 `meson.build`、`docs/ARCHITECTURE.md`、`CHAPTER_CONFIG.md`、
   `CODE_GENERATION.md`、技术栈条目。
5. 数据结构与算法、设计模式两个分类当前无手册内容，不需要迁移，等有
   内容时直接用新渲染器。

每个阶段单独提交并过验证；前三个阶段 WebView 栈保持可用，第 4 阶段才
真正不可逆。

## 后果

- 内容渲染层去掉仅存的平台分支；`ArticleView` 契约、两个平台后端、
  常驻 WKWebView 时序处理（ADR 0012 排查未果的空白弹窗根因）一并消失。
- 构建依赖减少：`md4c`、`md4c-html`、`webkitgtk-6.0`、Apple `WebKit`。
- 文档与实验在同一渲染器下，学习流可以让文档元素直接成为交互控件，
  实验状态可反向影响呈现（例如预测选择高亮对照区）。
- 字号、主题、无障碍、键盘导航与应用其余部分统一。
- **代价**：需要新增并长期维护一个「内容块 → 控件树」渲染器；HTML 的
  富排版（图文环绕、复杂表格、脚注）不再免费，需要时自己实现或回避。
- 现有 `resources/articles/**.md` 全部要迁移验证；迁移期两套渲染并存，
  短期复杂度上升。
- `ui/ai_markdown_dialog` 与 AI 讲解改用新渲染器；AI 自测不受影响。
- 图表必须为手册配一套 SVG / Cairo 机制（`AGENTS.md` 已定「优先静态
  SVG」，此前手册未真正用到）。

## 未决问题

- 「控件文档渲染器」放在哪一层：`render/` 还是新的 `content/` 子模块；
  它不依赖 `MainWindow`，只接收内容数据、产出控件。
- 侧栏目录与连续学习流的全局知识点目录如何共存或合并。
- 长文档滚动位置的保存与恢复（原由 WebView 承担）在控件流下的实现方式。
