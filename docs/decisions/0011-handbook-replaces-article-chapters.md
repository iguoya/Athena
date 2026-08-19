# ADR 0011：本地静态文档合并为"手册"页面，废弃 `content: article` 章节类型

- 日期：2026-08-19
- 状态：已接受
- 依据提交：（本 ADR 与对应实现同批提交）

## 背景

ADR 0009 之后又做过一次修正：把"本章总纲"从"点击时现场调用 DeepSeek 生
成"改成"本地读取一份人工撰写的静态 Markdown 文档，用 Dialog + WKWebView
显示"。这个 Dialog 方案在实测中暴露了一个稳定性问题：对话框刚 `show()`
出来时，承载 WKWebView 的 `Gtk::DrawingArea` 往往还没经过真正的布局分配，
WebView 的初始尺寸被算成 0，内容因此不可见；Dialog 只有这一次创建机会，
不像常驻主窗口的页面那样后续还有很多次真实 resize 能自我纠正。排查过程
中加了 idle 回调兜底重新计算尺寸，仍未能稳定复现修复。

与此同时，用户希望把现有的 `content: article` 独立文章章节（当时只有
"程序与源码组织"一个）也并入同一套静态文档体系，做成一本"手册"：现有
article 章节和各章节总纲文档的合集，一份带完整目录的常驻页面，而不是
分散成好几个互不相关的独立入口。

## 决策

- **新增顶层字段 `handbook_documents`**（数组，元素是 `resources/articles/`
  下的文档路径）：手册收录的静态文档合集，按数组顺序拼接渲染，语义上
  和具体章节解耦——不要求每份文档对应一个 chapter。
- **手册页面复用主窗口已经验证过稳定的常驺 WKWebView 嵌入方式**（跟原来
  `article` 类型章节标签页是同一套渲染机制：`Gtk::DrawingArea` 常驻在
  `Gtk::Stack` 里，`create_platform_article_view` 一次性创建、经历过多次
  真实 resize），不再用 Dialog + 现造的一次性 WKWebView——绕开了排查未果
  的时序 bug，而不是修复它。
- **彻底废弃 `content: article` 章节类型和 `chapter.document` 字段**：所有
  章节现在都是同一种（原来的 `code` 类型），`defaults.content`、
  `defaults.chapter_ui.article`、`article_chapter.blp`、
  `MainWindow::initialize_article_page()` 全部移除。原来唯一使用这个机制
  的"程序与源码组织"章节从 `athena.json` 里整体删除（它没有可运行知识点，
  内容直接并入 `handbook_documents`）。"欢迎页面"原来也标了
  `content: article` 但用的是自定义 `ui.blueprint`，实测这个标记对它的
  行为没有任何实际影响（自定义 blueprint 已经绕开了 content 相关的全部
  分支），去掉后行为不变。
- **`chapter.overview_document` 语义改变**：从"指向一份单独展示的文档"
  变成"指向 `handbook_documents` 里已收录的一份文档"，"本章总纲"按钮从
  "弹一个新 Dialog"变成"跳到手册页面里这份文档的起始锚点"
  （`MainWindow::show_handbook_page(overview_document)`）。生成器 `check`
  校验 `overview_document` 必须已经在 `handbook_documents` 列表里，缺了
  报错而不是静默忽略。
- **锚点计算**：`parse_markdown_headings()` 的标题锚点（`athena-heading-N`）
  按文档内出现顺序编号，天然在整个拼接后的合集里保持跨文档唯一，不需要
  额外的去重/加前缀逻辑；每份文档在合集里的起始锚点 = 它前面所有文档的
  标题总数，构建手册时顺带算出、存进
  `MainWindow::m_handbook_anchor_by_document`。
- **`ArticleView` 接口新增 `scroll_to_anchor()`**：页面还没加载完成时记住
  这次跳转请求，等 `didFinishNavigation` 触发后再执行，不丢失。
- **导航位置**：手册入口在左侧分类按钮上方独立一行，跟分类按钮共用同一个
  互斥 `ToggleButton` 组；点击分类时如果当前正显示手册，即使目标分类跟
  `m_current_category` 相同也要强制重新走一遍 `build_chapter_tabs`（用
  `m_showing_handbook` 标记），否则会出现"点了分类按钮但页面停在手册"的
  死角。

## 后果

- Dialog + 一次性 WKWebView 这条路径被完全移除，之前排查未果的空白弹窗
  问题也随之不再出现（因为触发它的代码路径已经不存在），但**没有真正定位
  到 GTK/WKWebView 层面那个时序 bug 的根因**——如果以后还要在 Dialog 里
  嵌入原生 WebView（不经过手册这条常驻路径），同样的坑可能会再次出现，
  应该优先复用手册验证过的常驻页面模式，而不是重新造一次性对话框。
- `content` 字段和"article 章节"这个概念从 schema、生成器、`ChapterCatalog`
  到 `MainWindow` 全部移除；以后任何"整篇静态 Markdown 内容"的需求都应该
  走 `handbook_documents`，不要重新引入一个独立的章节类型。
- 手册目前只有 3 份文档、都在同一个目录下，`document_base_directory` 用
  第一份文档的目录作为相对资源（图片等）的公共基准路径；如果以后手册
  文档分布在不同目录、其中确实引用了相对路径的图片，这个假设需要重新
  考虑（比如改成按文档单独设置 base_path，或统一约定手册文档不引用相对
  资源）。
- "AI 讲解"" AI 自测""AI 讲解差异"三个功能（ADR 0009、0010）继续用独立的
  Dialog + 现场 AI 调用路径，跟手册是两条完全不相关的路径，共用的只是
  底层 Markdown → HTML 渲染函数；这些对话框仍然是"一次性创建"，如果未来
  也在这几个对话框上观察到类似的空白/时序问题，应该按这次的经验优先
  考虑"改成常驻页面"而不是继续在 Dialog 场景下修时序。
