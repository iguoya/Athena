# ADR 0012：本地静态文档合并为"手册"页面，废弃 `content: article` 章节类型

- 日期：2026-08-19
- 状态：已接受
- 依据提交：（本 ADR 与对应实现同批提交）

## 背景

ADR 0010 之后又做过一次修正：把"本章总纲"从"点击时现场调用 DeepSeek 生
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

- **新增分类级字段 `category.handbook_documents`**（数组，元素是
  `resources/articles/` 下的文档路径）：**每个分类有自己独立的一部手册**，
  按数组顺序拼接渲染，语义上和具体章节解耦——不要求每份文档对应一个
  chapter，也允许为空（该分类暂无手册）。手册不跨分类合并。

  > 修订说明：本 ADR 初版把 `handbook_documents` 放在**顶层**，做成一部
  > 跨全部分类的合集。落地后判断这个划分不对——C++、数据结构与算法、
  > 设计模式三个分类的理论内容彼此独立，混进同一本手册后目录会互相干扰，
  > 章节编号也无法各自连续。因此改为分类级，三个分类各一部手册。生成器
  > 显式拒绝顶层 `handbook_documents`（报错而不是静默忽略），避免旧配置
  > 升级后手册毫无提示地空掉。
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
  变成"指向**本分类** `handbook_documents` 里已收录的一份文档"，"本章总纲"
  按钮从"弹一个新 Dialog"变成"跳到本分类手册页面里这份文档的起始锚点"
  （`MainWindow::show_handbook_page(category_name, overview_document)`）。
  生成器 `check` 校验 `overview_document` 必须已经在**同一个分类**的
  `handbook_documents` 列表里，缺了报错而不是静默忽略。
- **锚点计算**：`parse_markdown_headings()` 的标题锚点（`athena-heading-N`）
  按文档内出现顺序编号，天然在整个拼接后的合集里保持跨文档唯一，不需要
  额外的去重/加前缀逻辑；每份文档在合集里的起始锚点 = 它前面所有文档的
  标题总数，构建手册时顺带算出、存进
  `MainWindow::m_handbook_anchors_by_category`（按分类分开存，不同分类的
  手册各自从 0 开始编号）。
- **`ArticleView` 接口新增 `scroll_to_anchor()`**：页面还没加载完成时记住
  这次跳转请求，等 `didFinishNavigation` 触发后再执行，不丢失。
- **导航位置**：手册是**该分类标签行里的一个合成标签页**，跟"学习进度"
  同类——不来自 `athena.json` 的任何章节，由 `build_chapter_tabs()` 手工
  插入。有欢迎页的分类（只有 cpp）排在"欢迎页面 → 学习进度"之后，没有
  欢迎页的分类排在最前。侧边栏只剩分类按钮，**没有跨分类的全局手册入口**。
- **手册页面不登记进 `m_active_page_names`**：它由 `make_managed` 直接建出，
  没有 builder 持有引用，一旦从 `Gtk::Stack` 移除就会连控件带 WKWebView
  一起析构，而 `m_article_views` 里的 `ArticleView` 还指着里面的宿主控件。
  因此切分类时把手册页留在 Stack 里（只是没有标签按钮指向它），每个分类
  最多留一页、懒构建一次。这也正是本 ADR 选常驻页面而非临时 Dialog 的
  同一条理由的延续。

## 后果

- Dialog + 一次性 WKWebView 这条路径被完全移除，之前排查未果的空白弹窗
  问题也随之不再出现（因为触发它的代码路径已经不存在），但**没有真正定位
  到 GTK/WKWebView 层面那个时序 bug 的根因**——如果以后还要在 Dialog 里
  嵌入原生 WebView（不经过手册这条常驻路径），同样的坑可能会再次出现，
  应该优先复用手册验证过的常驻页面模式，而不是重新造一次性对话框。
- `content` 字段和"article 章节"这个概念从 schema、生成器、`ChapterCatalog`
  到 `MainWindow` 全部移除；以后任何"整篇静态 Markdown 内容"的需求都应该
  走 `handbook_documents`，不要重新引入一个独立的章节类型。
- 手册目前只有 cpp 一部有内容（3 份文档、都在同一个目录下），
  `document_base_directory` 用第一份文档的目录作为相对资源（图片等）的
  公共基准路径；如果以后手册文档分布在不同目录、其中确实引用了相对路径
  的图片，这个假设需要重新考虑（比如改成按文档单独设置 base_path，或
  统一约定手册文档不引用相对资源）。
- 数据结构与算法、设计模式两个分类目前一份文档都没有，它们的手册标签页
  显示一句占位说明而不是空白 WebView——既不谎称有内容，也不为空文档白起
  一个 WKWebView。等这两个分类真正开始写内容时直接往各自的
  `handbook_documents` 里加即可，不需要再改代码。
- 手册文档的一级、二级标题带"第 N 章"/"N.M"编号，改成分类级之后这些编号
  的范围也收敛到各自分类内部，跨分类不再需要协调；但**现有 cpp 三份文档
  的编号是按原来的跨分类合集排的，如果以后 da/dp 开始写手册，各自从第 1
  章重新起编即可，不要沿用 cpp 的序号**。
- "AI 讲解"" AI 自测""AI 讲解差异"三个功能（ADR 0010、0011）继续用独立的
  Dialog + 现场 AI 调用路径，跟手册是两条完全不相关的路径，共用的只是
  底层 Markdown → HTML 渲染函数；这些对话框仍然是"一次性创建"，如果未来
  也在这几个对话框上观察到类似的空白/时序问题，应该按这次的经验优先
  考虑"改成常驻页面"而不是继续在 Dialog 场景下修时序。
