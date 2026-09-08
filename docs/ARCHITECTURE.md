# Athena 架构说明

## 1. 项目目标

Athena 是为快速渐进学习和掌握 C++ 而开发的自用软件平台，突出学练合一：把零散的代码知识点学习整合到统一框架中，方便运行验证和自我修正。项目使用 GTK4、gtkmm、GtkSourceView 5、MD4C、Meson 和 Blueprint 构建。GtkSourceView 负责只读源码框的 C++ 语法高亮和行号显示；MD4C/md4c-html 把文章章节的 Markdown 转换为 HTML。macOS 通过系统 WKWebView、Ubuntu 通过 WebKitGTK 6.0 和统一 CSS 完成文章排版；文章模式只保留 WebView 路径，不在受支持平台维护 GtkTextView 降级渲染。项目结构由 `resources/athena.json` 驱动，用户既可以运行可实验的知识点，也可以阅读不适合用单次运行结果解释的理论、原则和工程思想。

内容设计以 C++ 知识点和学习目标为起点：学习文档负责建立概念体系、语义边界、常见
误区和思维模型，教学代码负责把这些思想转化为可操作、可观察、可验证的实验。文档不是
现有源码的说明书，生成流程也不得通过总结实现代码反向决定课程内容。

Athena 不采用“只读文档”或“只看代码”任一极端：只有文档容易停留在被动理解，难以
保持注意力并学有所用；只有代码容易失去全局框架，陷入局部实现细节。学习过程遵循
“思想建立行动方向，行动验证思想并产生反馈，反馈再修正、深化乃至升华思想”的循环。
因此文档与实验不是两套平行内容，而是同一知识点在理解与实践两个阶段的协作关系。

项目采用轻量分层和注册表，不以完整 MVC/MVP 为当前目标。核心问题是让课程配置、C++ 演示实现和 GTK 界面之间具有稳定、可校验的连接。重要架构取舍的背景与后果记录在 `docs/decisions/` 的 ADR 中。

## 2. 当前实现

当前数据流如下：

```text
resources/athena.json
        |
        |
        v
project_generator/model.py：唯一严格校验 + 默认值/路径/ID 规范化
        |
        +--> builddir/app.gresource.xml + Blueprint/文章/源码资源
        +--> builddir/function_registry.generated.cc --> FunctionRegistry
        +--> builddir/chapter_catalog.generated.json
        |                 |
        |                 v
        |      GResource: /app/data/chapter_catalog.json
        |                 |
        |                 v
        |          ChapterCatalog（只解码）
        +--> 显式 scaffold：只创建缺失的人工章节骨架
                          |
        FunctionRegistry + ChapterCatalog ----------> MainWindow（导航协调）
                                                     |
                                                     +--> ChapterPageStack（Stack 子页装配/切换）
                                                     +--> ChapterIndexPage
                                                     |       +--> KnowledgeGraph（前置依赖与章节指标聚合）
                                                     |       +--> KnowledgeGraphView（连线 + GTK 节点卡片）
                                                     +--> CodeChapterPage
                                                     |       +--> ExperimentDialog（共享、非模态）
                                                     |               +--> ExperimentDock
                                                     |                       +--> ExperimentRunner
                                                     +--> WorkbenchPage（文档主导原型）
                                                     |       +--> ArticleView
                                                     |       +--> ExperimentDialog（同一实例）
                                                     +--> PocketCubePage
                                                     +--> HandbookPage（每分类一部，懒构建一次）
                                                     +--> ProgressPage / LearningDialogs
```

已有的优点：

- 章节菜单和 Blueprint 资源主要由 JSON 驱动。
- 所有章节共享同一个 `empty_chapter.blp`。
- 手册文档作为 GResource 随应用打包，并可在开发期从源码树回退读取。
- 手册 HTML 和 CSS 与平台显示控件分离；macOS 原生后端在同一个 HTML 页面中渲染目录、正文、字号控制和明暗主题，页内链接直接完成标题跳转。
- 手册 H1–H3 同时作为导航目录，标题保持简短，详细说明由标题后的正文承担。
- TypeSemantics 已使用学习工作台原型：初始让文档占满阅读区；配置了 `teaches`
  的小节在正文末尾显示一个或多个实验入口，点击后打开共享的模态实验窗口。
  窗口只显示当前实验、验证目标、真实源码、运行状态和观察结果，不重复全章知识点目录。
- `ExperimentDialog` 是标准代码页与学习工作台共享的单例窗口，暂时以 `MainWindow`
  为 transient parent；ADR 0023 第一阶段把内部调整为“当前目标 → 完整真实源码 →
  运行操作 → 观察结果”的纵向证据链。`ExperimentDock` 继续只负责源码定位、后台运行
  状态和结果呈现；页面只上报当前选择哪个实验，不接触窗口内部控件。
- 每个知识点可以独立运行并显示结果；实验代码在独立工作线程执行（同一时刻只运行一个，运行中的新请求被忽略），状态栏的转圈指示与耗时提示反馈进度，结果和耗时经主线程回填，界面不阻塞。
- Meson 配置阶段会校验配置引用的 Blueprint 文件是否存在。
- 统一生成器会校验完整项目模型，并在临时工程中端到端测试五个子命令。
- GResource XML 和函数注册表均生成在构建目录，正常配置和构建不会改脏源码树。
- `athena.json` 引用的教学源码随 GResource 打包；开发时优先读取仓库文件，安装后自动使用内置源码。
- `ChapterCatalog` 只解码构建生成的规范化 Catalog，不再解析作者配置、计算默认值
  或修正数据；它和 `FunctionRegistry` 均与 GTK 解耦，可使用 Google Test 单独验证。
- `ContentLoader` 统一封装 GResource、开发期源码文件和 Markdown 文档读取。
- Markdown 中标记为 `cpp`、`c++` 或 `cxx` 的围栏代码块由共享
  `markdown_renderer` 做轻量 C++ 词法着色，关键字、类型、字符串、注释、数字和
  预处理行分别使用 CSS token class；标记为 `text` 或未声明语言的围栏保持单色。
  着色过程不加载运行时 JavaScript，也不改变 Markdown 原文，macOS WKWebView 与
  Ubuntu WebKitGTK 继续复用同一份 HTML/CSS。
- `SourceLocator` 按知识点成员函数名定位真实 C++ 定义范围；`load_member_source_text()`
  在此基础上取出该成员函数的全文，AI 讲解的源码快照、AI 自测的参考实现共用它，
  不各自再写一遍“读文件 + 定位 + 截取”。知识点标题旁只读展示“重要度”徽章（橙色，0–5，来自 `athena.json` 的 `subchapter.importance`，由内容作者基于教学与工程实践给出的客观难度判断，不要求已写出实现代码，未评时不显示；用户不可修改，参见 `docs/CHAPTER_CONFIG.md`）；条目本身（标题与描述）不响应点击。
- C++ 分类的默认索引页把章节网格与知识图谱合并：`KnowledgeGraph` 从同分类
  `chapter.prerequisites` 计算稳定分层和连线，并聚合 `LearningStore` 熟练度；真实 GTK
  节点卡片保留章节图标、标题和简介，同时用独立色系显示章节重要度（已评知识点
  `importance` 的平均值）、掌握程度（5 星知识点数）和完成程度（平均熟练度 / 5）。
  2K 屏幕下图谱主区域按最大并列数铺满等宽轨道，节点不设固定宽高或描述行数，
  由完整内容自然测量；右侧说明栏解释三种口径。返回 C++ 目录时重建图谱，避免 AI 自测后显示旧颜色。
  其他分类没有成熟依赖数据，继续使用自适应 FlowBox 网格。
- 全局正常可读文字以 14pt 为硬下限：GTK 的所有 `GtkWindow` 默认使用 16pt，
  局部样式不得降到 14pt 以下；Markdown/WKWebView 默认 21px（约 15.75pt），
  阅读器缩小控制最低停在 19px（约 14.25pt）。图表坐标文字同样遵守这一基线，
  只有没有文字语义的图标和装饰尺寸可以更小。
- 知识点行尾操作区以分隔线隔离，依次放置“运行”“AI 讲解”“AI 自测”按钮与只读的“熟练度”五星结果（绿色，0–5 星）。熟练度不能手动修改，只在用户答完一次完整 AI 自测后，按本地固定公式从正确题数换算并持久化；“运行”只由知识点是否已实现决定，满星后仍可重复实验。三个动作都绑定所在行的 topic，点击时先激活本行再执行。运行历史及其双记录比较、git 快照和“AI 讲解差异”已按 ADR 0023 移除；旧数据库中的 `run_history` 表保持原样，不读写也不删除。
- “AI 自测”和“AI 讲解”共用非 GTK 的 `AiService`：优先用 DeepSeek（`deepseek-chat`），未配置或请求失败再退回火山方舟豆包（`doubao-seed-2-1-pro-260628`）；两者都未配置时直接返回明确错误。Key 优先从侧边栏“设置”读取，未保存时回退到 `ATHENA_ARK_API_KEY`/`ATHENA_DEEPSEEK_API_KEY` 环境变量。两家服务商都是 OpenAI 兼容协议，底层共用同一个可替换的请求通道，只是 endpoint/model 不同。Key 与请求体经权限受限的临时文件传入、用后即删，不出现在进程参数里；临时文件放在 GLib 按操作系统选择的 Athena 用户缓存目录。`AiService` 只返回普通数据，不更新 GTK，`LearningDialogs` 负责工作线程与主线程之间的结果交接。服务商顺序、回答解析、代码围栏清理和自测题解码都有不访问网络的单元测试（参见 ADR 0010、ADR 0011、ADR 0014）。
- **手册**按分类各自独立，一个分类一部，作为该分类标签行里的**合成标签页**（跟"学习进度"同类，不来自 `athena.json` 的任何章节）：有欢迎页的分类（只有 cpp）排在"欢迎页面 → 学习进度"之后，没有欢迎页的分类排在最前；侧边栏只剩分类按钮，没有跨分类的全局手册入口。`HandbookPage` 按该分类 `handbook_documents`（`docs/CHAPTER_CONFIG.md` 4.3）列出的顺序拼接各文档 Markdown（文档间插入 `---` 分隔），一次性喂给 `parse_markdown_headings`/`render_markdown_html`，生成一份跨文档的完整目录，并独占宿主控件、文档锚点和 `ArticleView` 生命周期。渲染继续使用常驻 WKWebView，不是每次点击现造 Dialog+WKWebView——后者在实测中出现过对话框刚弹出时宿主控件还没经过真正布局分配、WebView 尺寸算成 0 的时序问题，稳定性不如常驻页面，因此彻底放弃了这条路径。**手册页面不进 `m_active_page_names`**：切分类时把它留在 Stack 里（只是没有标签按钮指向它），每个分类最多留一页、懒构建一次；`MainWindow` 只保留对应 `HandbookPage` 模块，不再平行维护 WebView 与锚点缓存。还没收录文档的分类（当前是 da、dp）显示一句占位说明，不为空文档白起一个 WebView。手册文档的一级、二级标题手工带"第 N 章"/"N.M"编号，**各分类手册各自从第 1 章起编，不跨分类连续**；`resources/article.css` 给 `**加粗**` 配了琥珀色（`--article-highlight`，标一般重点）、给 `***加粗斜体***`（md4c 渲染成 `<em><strong>`）配了红色（`--article-danger`，标真正的易错点/陷阱），两档颜色写文档时按实际内容判断取舍，不是每句话都要标。
- “说明文档”**不调用 DeepSeek**：`chapter.overview_document` 指向**本分类** `handbook_documents` 里已收录的一份静态 Markdown 文档路径，点击按钮跳到本分类手册页面里该文档的起始位置（`MainWindow::show_handbook_page(category_name, overview_document)`，通过 `ArticleView::scroll_to_anchor()` 执行页内 `scrollIntoView`）——跳的是**本分类**的手册，不发起任何网络请求（参见 `docs/CHAPTER_CONFIG.md` 6.2）。撰写这份文档时可以用 AI 辅助起草，但必须经人工审核才能提交，跟“自然语言 description 不应由普通模板生成器直接转换成未经审查的实现”是同一条原则在文档内容上的应用。未提供 `overview_document` 的章节，按钮退回复制章节标题/简介/知识点信息到剪贴板并唤起本机 AI 助手。当前 TypeSemantics、Reference、RAII 三个已实现章节写了说明文档，其余章节还没有。
- **“AI 讲解”**（`LearningDialogs::show_ai_insight()`）现场把该知识点真实源码发给 AI，请它从**整体**（这段代码整体在做什么、为什么这样设计、跟这个知识点想教的概念是什么关系、适用场景）和**局部**（关键实现细节、容易被忽略或误解的地方、常见误用）两个角度讲解。这是跟手册“说明文档”按钮（本地静态、需人工审核、不联网）互补的路径：手册适合覆盖面广、要求内容稳定的原理性说明；AI 讲解适合当前这一段具体源码的即时解释。
- “AI 讲解”结果按 `(function_id, 源码快照)` 缓存进 `LearningStore` 的 `ai_insight` 表（`load_ai_insight()`/`save_ai_insight()`，一个知识点只保留最近一次，upsert 覆盖）。点击时先查缓存，源码快照与当前 `load_member_source_text()` 读到的内容一致就直接用 `show_static_markdown()` 展示；源码变了或从没生成过，才调用 `show_ai_markdown()` 请求 AI。请求成功后通过 `on_success` 回调把结果和源码快照存回缓存，请求失败的错误提示不缓存。
- **学习进度**跟手册不同，不是全局常驻页面，而是 cpp 分类里紧跟"欢迎页面"之后的一个**合成标签页**：它不对应 `athena.json` 里的任何章节，由 `MainWindow::build_chapter_tabs()` 在遍历到欢迎页（按 Blueprint 根控件名 `welcome_page` 识别，不硬编码章节 `name`）之后调用 `append_progress_tab()` 手工插入，因此只统计 cpp 分类（数据结构与算法、设计模式两个分类当前没有实现内容，等真有内容再决定要不要各自加一份）。页面不用 WebView，是纯 GTK 控件搭的统计仪表盘（`ui/progress_page.cc`）：顶部四张统计卡片（知识点总数/已掌握/学习中/平均熟练度，各用一种强调色，仿常见管理后台的 stat tile），紧接着是“建议接下来学习”卡片（`suggest_next_topics()`，纯本地规则：优先推荐已经在学的 1–4 星知识点，再推荐完全没碰过的 0 星，5 星不再推荐，同优先级内保持 `athena.json` 声明顺序；不调用 AI，也暂不接可点击跳转，是第一版概要功能，全部掌握或还没有任何知识点时不显示），再往下一行两张 Cairo 手绘图表（环形图看整体三档占比、直方图看熟练度分布），最后按章节用 `Gtk::Expander` 列出（收起显示章节名 + `Gtk::LevelBar` 进度条 + "已掌握/总数"，展开显示每个知识点的星级只读展示）。逐章节完成度已经由这份列表完整表达，因此不再另画一张信息重复、章节名难以清晰排布的柱状图。统计口径是"5 星 = 已掌握"，数据来自 `LearningStore::load_all_mastery()`（一次性批量读取全部 `knowledge_progress`，不是按知识点逐个查询）与 `ChapterCatalog` 交叉。页面名登记进 `m_active_page_names`，切到别的分类时和普通章节页一起被移除；切回 cpp、AI 自测成绩成功写入或用户再次激活“学习进度”标签时，窗口只替换该页面并重新读取、聚合数据，不重建整个分类标签栏。数据量小，重新查库加布局的开销可以忽略，也不需要维护额外的“数据是否过期”状态（这一点跟懒构建一次的手册相反）。构造函数里 `open_learning_store()` 必须排在 `setup_category_sidebar()` 之前：后者第一个分类按钮的 `set_active()` 会立刻触发学习进度页构建，学习存储还没打开的话首屏统计会恒为全 0（这是真实出现过的症状，不是假设）。
- 欢迎页面只保留学习路线和学习特色等静态说明，不再显示硬编码的章节数、学习阶段和 `0%` 完成度“学习概览”卡片；实时学习数据统一由紧邻的“学习进度”页面呈现，避免两个入口表达重复且可能不一致的统计信息。
- 学习进度分为三层：`registry/progress_stats.h`（`ChapterProgress`/`CategoryProgress`/`aggregate_category_progress`）不依赖 GTK，负责"哪些算已掌握、完成度怎么算"；`ui/progress_page.h` 只接收已经聚合的 `CategoryProgress` 并装配 GTK 控件，不读取目录或 SQLite；`render/chart_view.h` 负责 Cairo 绘图且不含统计口径。`render/chart_scale.h` 保存绘图纯计算和配色常量。数据聚合、页面构造和刻度计算分别有独立测试。**完成度用的是平均熟练度占满分的比例（`ChapterProgress::completion_ratio()`），不是"5 星知识点占比"**：后者是二值口径，评到 4 星在章节进度条上会和完全没学过一样；没有任何 5 星时进度条还会恒为 0，无法反映 1–4 星的学习进展。
- 熟练度直方图带有坐标轴和网格线。图中文字使用 Pango 布局而不是 Cairo 的简化文字接口，确保 macOS 上“星”等中文能自动回退到可用字体，不显示方块；圆环按“外沿半径－半线宽”计算实际路径，并预留 18px 抗锯齿边距，避免粗线越过 DrawingArea 被裁切。图表配色集中在 `render/chart_scale.h` 的 `kChartMastered`/`kChartInProgress`/`kChartNotStarted` 等常量，按十六进制定义并在注释里标注各自对应的 `style.css` `@athena_*` 变量——Cairo 取不到 GTK 的 `@define-color` 命名颜色，只能维护这一份独立副本，改配色时两边必须一起改（曾经"未开始"这一段就因为只改了一边，出现过图上颜色和图例色块对不上的情况）。
- 没有引入图表库：GTK 生态里成熟的图表库全部绑定 Qt（Qwt、QCustomPlot、Qt Charts），ImPlot 是立即模式、要接 OpenGL 帧循环，PLplot 虽然能画进现有 Cairo 上下文但 API 老旧、面向科研出版图，都不适合这几张小图；GNOME 自家应用（系统监视器、Health）遇到同样问题也是直接手绘。这个决定的前提是数据规模小（几十个知识点、十几个章节，一个 0-5 的标量）——如果统计维度显著变复杂或需要真正的下钻交互，再重新评估。
- “AI 自测”要求 AI 以 JSON 返回针对该知识点具体源码的自测题（题干、可选代码片段 `code`、选项数组、正确选项下标数组 `correct_indices`、解释），继续用 GTK 控件渲染，不是 Markdown/WebView；`code` 单独放在只读等宽代码框中，不和题干挤在普通文字标签里。提示词把 AI 限定为出题者：题目只能依据当前知识点说明和真实源码，覆盖核心语义、代码行为、常见误用，以及与该知识点确实相关的边界情况；能用短代码场景考察时，优先询问输出或编译结果、对象与资源生命周期、所有权、异常安全、错误定位和修改方案，不改成定义背诵或措辞辩论，只有无法通过代码表达时才保留少量概念题。难度以基础理解和源码分析应用为主，不靠范围外冷门细节提高难度，也不使用未定义行为或未说明的平台差异。题量由实际存在的独立考察点决定，少于或多于 5 道都有效，覆盖完整后停止，也不把同一事实换说法重复出题。`correct_indices` 只有一个元素时按单选渲染（选项互斥），多个元素时按多选渲染（选项互相独立、可多选，标题标注“多选”）；本地代码严格比较用户所选集合与标准答案集合，多选不给部分分，AI 不参与评分。用户必须答完全部有效题目才产生总成绩，熟练度按 `floor(答对题数 / 总题数 × 5)` 换算，只有全对才是 5 星；中途关闭不改原成绩，重新完整自测则以最新成绩覆盖。正确显示绿色“✓ 回答正确”，错误显示红色“✗ 回答错误，正确答案是……”并展开解释，随后选项和提交按钮置灰。`AiService` 解码前会去掉 AI 偶尔添加的 JSON 代码围栏，也兼容 AI 偶尔省略提示词要求的外层 `{"questions": [...]}` 包装、直接返回题目数组本身这两种响应形状，并过滤无效题目和越界答案下标；整体无法解码时，界面退化为原样显示文本，不丢失回答。正文字号用 `.ai-dialog-question`/`.ai-dialog-option`/`.ai-quiz-code` 等 class，不影响主界面的 `.code-view`（18pt）（参见 ADR 0015）。
- 对话框不额外加“关闭”按钮——系统原生标题栏自带关闭按钮，重复一个没有意义。确有内容区动作时用 `append_dialog_action_bar()` 加在末尾；它和统一处理模态锁定/生命周期的 `lock_for_modal_dialog()` 都在 `ui/dialog_helpers.h`，由 `LearningDialogs` 和独立的 `AboutDialog` 模块复用。
- **“关于”对话框**是 `AboutDialog` 模块内部手写的 `Gtk::Dialog`，不用 GTK 内建的 `Gtk::AboutDialog`——后者是一套独立的“品牌展示页”视觉语言（大 Logo 居中、切标签页看 License），跟其余自己画的对话框（原生标题栏 + 左对齐表单式内容 + 底部居中按钮）风格不统一。内容完全静态、没有异步操作，惰性创建一次后长期复用；`MainWindow` 只调用 `present()`。
- 标准章节页上方是一个统一的 Frame：图标 + 标题/简介（hexpand 占满中间空间）+
  “说明文档”按钮（紫色，跟运行/成功/危险等其他语义色区分开，不依赖当前选中的
  知识点、常驻可点）。章节打开时默认无激活条目，底部说明栏保持占位提示并支持换行；
  真实源码和观察结果位于独立实验窗口，不再占用章节知识点列表的宽度。
- **应用实践**（`practice` 分类）章节用专属布局（`practice_cube.blp` 等），不是标准 `chapter_page` 那套“知识点列表 + 源码框 + 结果区”三栏结构——目前只有 2 阶魔方一章，左栏是源码框 + “运行”“重置魔方”两个按钮 + 输出框，右栏是带标题的两个 `Frame`：“当前状态”一行 + “未来状态”九宫格（没有单独的运行状态日志，“就绪/运行中/已完成”这类文字提示价值不大，已经去掉）。“当前状态”那一行横向排三块：3D 视图（可拖拽旋转）、六面展开图（两者互补，一个直觉一个精确无遮挡）、状态摘要文字（`kCubeStateSpaceSizeIgnoringOrientation` 给出的状态空间数量、`PocketCube::move_history()` 拼成的当前路径、`is_solved()` 判断的是否复原），这一行不设 vexpand，高度由内容自然撑开。“未来状态”九宫格设成 homogeneous + hexpand/vexpand，撑满剩余整块区域；每一格是 3D 视图 + 展开图横向并排（跟“当前状态”那一行同一种视觉逻辑）叠一份 caption，对应 `next_move_set()` 给出的 U/R/F 三个面 × 顺时针/逆时针/180° 这 9 种非冗余转法（2 阶魔方没有固定参考系，转 D/L/B 都等价于先整体转半圈再转 U/R/F，是冗余操作，不单独穷举），只读预览、不接受点击；每格右下角叠一个“复原”`Gtk::ToggleButton`（`Gtk::Overlay`），按下后把这一格切换成显示当前实际状态（不套用这一步转法），方便跟默认显示的“转完的样子”来回切换对比，纯展示开关，不会真的把这步转法应用到 `cube` 上。`PocketCubePage` 独占这套控件装配、状态和动画交互；`MainWindow` 只识别页面类型并创建模块。其余动画、重置和九宫格刷新规则保持不变。
- 教学/实践源码分两个平级顶层目录：`language/` 按 C++ 语言特性拆分知识点（`language/references/`、`language/raii/` 等），`practice/` 收纳自成一体的应用实践项目，一个项目的状态表示、算法、渲染代码都收在自己的子目录里（比如 `practice/pocket_cube/` 同时放 `state.h/.cc`——不依赖 GTK、可脱离渲染层单独测试的魔方状态与转动代数、`view.h/.cc`——3D/展开图的 Cairo 渲染、`pocket_cube.hpp`——真正的知识点实现），不嵌进 `language/` 底下，也不分散到 `render/` 之类别的顶层目录。`scripts/project_generator/model.py` 的 `project_path()` 用 `SOURCE_PREFIXES = ("language", "practice")` 校验 `implementation.header`/`source` 等字段，两个前缀都接受。
- 曾经实现过知识点笔记，但控件长期隐藏、没有可用入口，却要求代码页维护自动保存定时器、切换时刷新和存储读写，因此已移除界面及运行时 API。旧数据库中的 `note` 列不删除、不覆盖，避免升级时破坏用户历史数据；新数据库不再创建该列。若以后确有记录学习心得的需求，应先重新设计可发现的入口和检索方式，而不是恢复隐藏文本框。
- `MainWindow` 只保留分类导航、页面懒加载调度、跨页跳转、进度刷新和模块生命周期；代码页、实践页、手册、对话框与实验执行均由独立模块拥有。`ChapterPageStack` 只管理 `Gtk::Stack` 子页占位、替换、切换与常驻页；`ChapterIndexPage` 独占分类索引控件树，C++ 图谱的节点和说明由 `KnowledgeGraphView` 装配。窗口只传入 Catalog 派生数据和导航回调。
- 应用窗口默认图标名 `cn.athena.icon`：运行时从 GResource 的图标主题目录解析（不依赖系统安装），Linux `meson install` 同时部署 hicolor 图标与桌面条目，macOS 打包使用 `.app` 内的 icns。
- 章节页面按需构建：打开分类只为各章挂占位页，首次从索引节点或顶栏切换器进入章节时才创建真实页面（含 WKWebView），显著加快启动与分类切换；已构建页面由 builder 缓存持有，切回分类直接重挂。
- Meson 将 Catalog、内容加载、Markdown 转换、函数注册和课程实现统一编译为内部 `athena-core` 静态库，应用与核心测试共同链接该库。
- TypeSemantics 的 6 个知识点、Reference 的 4 个知识点、FunctionCallable 的 5 个知识点和 RAII 的 6 个知识点已接入注册表；未实现的知识点在界面中保持禁用。TypeSemantics 里原来合在一起的"类型推导"已拆成 `auto_deduction`（用可观察的运行时行为证明 auto/auto&/const auto& 的效果和结构化绑定，不借 decltype）和 `decltype_deduction`（专讲 decltype 自己的三条取类型规则）：两者受众和验证手段都不同，合并成一个知识点会强迫初学 auto 的人先学会 decltype 才能确认 auto 做了什么。

当前的主要问题：

- `MainWindow` 模块化已按 ADR 0014 完成，并在其后把 Stack 子页装配抽成
  `ChapterPageStack`、分类入口抽成 `ChapterIndexPage`；窗口协调层不再手搓章节卡片或记账活动页。后续新增页面行为应继续
  放进对应功能模块，避免把控件树、后台执行或持久化细节重新堆回窗口协调层。
- 注册表由 `athena.json` 生成；新章节可显式执行 `scaffold` 创建不会覆盖已有文件的首次实现骨架。
- 骨架生成只适合一个头文件与一个源文件的普通章节；一个类拆到多个源文件（通过各知识点自己的 `subchapter.source` 指定）曾是 RAII 的做法，现在认定为应当避免的特例，不是推荐路径——多个 `.cpp` 会导致按知识点切换源码框内容碎片化，看不到类的完整定义。默认约定是整章合并到一个 `.hpp`；`TypeSemantics`、`RAII` 已按路线图第 11 条迁移完成，连同 `Reference`、`FunctionCallable` 四个已实现章节现在都是单文件形态，详见 `docs/CHAPTER_CONFIG.md` 6.1。
- macOS 与 Ubuntu 均有文章显示后端：分别为 WKWebView 与 WebKitGTK 6.0，并复用相同 HTML、CSS、锚点和外部链接导航规则。

## 3. 目标架构

目标流程：

```text
                       +------------------------+
                       | resources/athena.json  |
                       +-----------+------------+
                                   |
                       +-----------v------------+
                       | Format + semantic check |
                       +-----------+------------+
                                   |
             +---------------------+---------------------+
             |                     |                     |
  +----------v-----------+ +-------v--------+ +----------v-----------+
  | Runtime chapter data | | Generated IDs | | Generated registry   |
  +----------+-----------+ +-------+--------+ +----------+-----------+
             |                     |                     |
  +----------v-----------+         |          +----------v-----------+
  | ChapterCatalog       |<--------+--------->| Function implementations |
  +----------+-----------+                    +----------+-----------+
             |                                           |
             +--------------------+----------------------+
                                  |
                       +----------v-----------+
                       | MainWindow/Presenter |
                       +----------+-----------+
                                  |
                       +----------v-----------+
                       | GTK/Blueprint views  |
                       +----------------------+
```

### 3.1 配置层

`resources/athena.json` 保存：

- 分类、章节和知识点的稳定 `name`。
- 数组表达的显示顺序，以及显示标题和描述。
- 通用 Blueprint、特殊界面覆盖和各层图标。
- 由 `name` 直接表达的函数 ID 分类、C++ 类名和成员函数名。
- 知识点视觉分组等运行时元数据。
- 知识点的 `importance`（0–5，内容作者标注的客观难度，缺省未评）；这是内容数据而不是用户数据，与存在 `LearningStore` 里的 AI 自测熟练度结果是两个独立概念。
- 可选的 `subchapter.teaches`：指出实验服务于哪份教学文档的哪一个唯一标题；
  同一小节可关联多个实验，生成器校验文档归属以及标题存在性和唯一性。
- 分类级 `handbook_documents`：该分类手册收录的静态 Markdown 文档路径，按顺序拼接渲染；手册按分类各自独立，不跨分类合并。章节可选的 `overview_document` 指向**本分类**列表里的一条，供“说明文档”按钮跳转。
- 已实现章节的 `implementation.header`；类名和函数名由章节与知识点的 `name` 派生，分类名只进入稳定函数 ID。

它不保存 C++ 函数体，也不负责表达 GTK 对象的运行时状态。

### 3.2 校验与生成层

生成器负责：

- 根据项目配置契约校验基本结构。
- 校验 ID 唯一性、C++ 标识符、C++20 关键字和资源文件存在性。
- 生成稳定的复合 ID、最终图标、源码路径和 UI 资源路径。
- 生成 C++ 只需解码的规范化运行时 Catalog。
- 生成演示注册表和必要的声明。
- 生成或更新 GResource 输入。
- 对新章节提供不会覆盖人工代码的实现骨架。

### 3.3 领域层

当前已经引入以下不依赖 GTK 的类型：

- `ChapterCatalog`：解码并查询生成的分类、章节和知识点元数据。
- `FunctionRegistry`：由 ID 查找可执行知识点函数。
- `SourceLocator`：在真实教学源码中定位成员函数定义范围，不依赖 GTK，可独立测试。

后续如果运行结果需要区分标准输出、错误和状态，再引入 `FunctionResult`；当前直接向
`ostream` 输出足以覆盖教学实验。

这些类型可以使用普通 C++ 单元测试验证，不需要启动 GTK。

源码按职责分组：`registry/` 放置项目配置的解析、校验、查询以及知识点函数注册；
`content/` 统一读取 GResource、Markdown 和教学源码；`render/` 放置 Markdown 到
HTML 的转换以及各平台 ArticleView 后端；`storage/` 以 SQLite 持久化熟练度、
AI 讲解缓存和应用设置。目录归组不改变 `ChapterCatalog` 与
`FunctionRegistry` 的职责边界，二者只通过稳定 ID 协作。

### 3.4 演示实现层

每个 `code` 章节类负责一个主题，成员函数负责一个可运行知识点。例如：

```cpp
class Reference final {
public:
    void reference_basics(std::ostream& output) const;
    void const_reference(std::ostream& output) const;
    void pass_by_reference(std::ostream& output) const;
    void return_by_reference(std::ostream& output) const;
};
```

初期可以继续使用统一签名：

```cpp
void method(std::ostream& output) const;
```

当知识点函数需要输入、结构化错误或状态时，再统一迁移为 `FunctionContext` 和
`FunctionResult`，不要让每个 JSON 条目定义任意 C++ 签名。

各分类 `handbook_documents` 里的文档不生成章节类和演示注册项。它们的正文属于文档资源；共享渲染层使用 md4c-html 把拼接后的合集 Markdown 生成完整 HTML，注入标题锚点，并生成同页的手册目录与阅读工具栏。HTML 原生页内链接负责目录跳转，`overview_document` 触发的跳转经 `ArticleView::scroll_to_anchor()` 执行同样的锚点滚动，应用生成的受控脚本负责字号和明暗主题设置。平台 ArticleView 后端只负责加载 HTML、执行锚点跳转，以及管理原生控件生命周期。

### 3.5 表示层

GTK/Blueprint 层负责：

- 为章节显示分类、说明、源码和执行结果。
- 为手册显示合集 Markdown 正文和可跳转目录；平台 WebView（macOS WKWebView / Ubuntu WebKitGTK）在一个 HTML 阅读页面中统一显示目录、正文、字号和明暗主题设置。标题由每份文档自己的一级标题提供，不重复显示章节头，也不显示运行按钮与结果区。
- 为学习工作台在小节正文末尾渲染实验入口组，并按需展开从属实验坞；文档决定
  学习顺序，代码只验证已经讲解的规则，不用全局实验列表反向组织正文。
- 把用户操作转换为稳定函数 ID。
- 调用 `FunctionRegistry`，但不感知具体章节类。

`MainWindow` 是轻量协调者，不直接解析 JSON，不包含页面内部控件树，也不维护每个章节的手写函数映射。

### 3.6 MainWindow 模块化边界

本节记录已经落地的结构。作者配置校验和规范化在 Python，`ChapterCatalog` 只解码
生成产物；统计、源码定位、内容加载、函数注册、图表比例计算，以及 AI 服务商回退/
响应解码、页面渲染、学习对话框和后台实验执行均是独立模块。`MainWindow` 只持有
顶层导航控件与功能模块，负责页面懒加载、Stack/标签切换、说明文档跨页跳转和进度刷新。

`LearningDialogs`（`ui/learning_dialogs.h`）已按单一职责进一步拆细（ADR 0016）：
它本身只是一个**门面**，装配共享依赖并把三个入口 `show_settings()`、
`show_quiz()`、`show_ai_insight()`（后两者的参数统一是一个 `DialogTopic`：知识点 ID、
标题、说明、源码路径、成员函数名）转发给各自独立的 `SettingsDialog`、`QuizDialog`、
`AiInsightDialog`。共享部分也各自成模块：`ApiKeyStore` 管 Key 的读写（应用内设置优先、
回退同名环境变量），`AiMarkdownDialog` 是 AI 回答的 Markdown 展示通道（md4c +
WKWebView）。未配置任何服务商 Key 时由子模块自己提示去“设置”里填。自测评分回写星级和刷新学习进度页
通过调用方传入的 `function<bool(int)>` 回调完成，任何子模块都不反向调用 `MainWindow`。

当前层次：

```text
MainWindow（顶层导航、页面切换、模块生命周期）
├── ChapterPageStack（Stack 子页占位与切换、常驻手册页保留）
├── ChapterIndexPage（普通分类网格 / C++ 学习图谱）
│   └── KnowledgeGraphView（前置连线、章节卡片、指标说明）
├── CodeChapterPage（保留的标准代码页；知识点列表与附加学习动作）
│   └── 请求 MainWindow 打开共享 ExperimentDialog
├── ExperimentDialog（目标 / 源码 / 运行 / 结果纵向证据链；模态单例）
│   └── ExperimentDock（当前实验、源码定位、运行状态与结果）
│       └── ExperimentRunner（非 GTK：函数执行与耗时）
├── WorkbenchPage（文档主导；文档实验入口请求打开实验窗口）
│   ├── ArticleView（正文、目录与实验入口组）
│   └── 请求 MainWindow 打开同一 ExperimentDialog
├── PocketCubePage（有状态实践页、动画与专属控件）
├── HandbookPage（手册内容、ArticleView 生命周期、文档跳转）
├── ProgressPage（CategoryProgress -> GTK 统计页面）
├── LearningDialogs（门面：装配下列子模块并转发三个入口）
│   ├── SettingsDialog（AI 服务商 Key 设置面板）
│   ├── QuizDialog（AI 自测：JSON 选择题 + 本地判分 + 熟练度回写）
│   ├── AiInsightDialog（AI 讲解：源码讲解 + 结果缓存）
│   ├── ApiKeyStore（Key 读写：应用内设置优先、回退环境变量）
│   └── AiMarkdownDialog（AI 回答的 Markdown/WebView 展示通道）
├── AboutDialog（静态关于对话框）
└── AiService（非 GTK：服务商回退、请求和回答解码）

数据与基础能力：
ChapterCatalog / FunctionRegistry / ContentLoader / SourceLocator / LearningStore
```

依赖只能从上向下：页面模块使用数据与基础能力，后者不能持有窗口或 GTK 控件。
页面之间不互相调用，跨页面导航由 `MainWindow` 协调。异步服务返回普通数据或通过
完成回调通知表示层，不直接更新 GTK。详细边界和低风险到高风险的拆分顺序见
ADR 0014；学习对话框按单一职责的进一步拆分见 ADR 0016。

## 4. 标识符策略

可运行知识点的稳定查找键由 `code` 配置中的三个 `name` 派生，不在 JSON 中重复保存：

```text
<category.name>.<chapter.name>.<subchapter.name>
```

示例：

```text
cpp.Reference.reference_basics
cpp.Reference.const_reference
```

约束：

- 分类名和成员函数名使用 ASCII `snake_case`；章节名使用合法 C++ 类型名。
- 查找键不从显示标题推导。
- 调整数组顺序不会改变查找键。
- 注册表、日志、测试和 UI 事件统一使用完整查找键。

## 5. 依赖方向

允许的依赖方向：

```text
GTK UI -> ChapterCatalog / FunctionRegistry -> Function implementations
GTK UI -> ArticleView -> platform web view
MainWindow -> feature pages -> non-GTK services/domain data
Generator -> config contract and templates
Meson -> Generator outputs
```

禁止：

- 演示实现依赖 `MainWindow`。
- 领域模型包含 GTK 控件指针。
- UI 代码复制章节标题或方法映射。
- 生成文件反向成为配置的唯一来源。
- 页面模块互相持有 GTK 控件，或基础服务反向调用 `MainWindow`。

## 6. 渐进式改造顺序

1. 已完成：稳定分类/章节/知识点名称及运行时语义校验。
2. 已完成：将注册表抽成 `FunctionRegistry`，统一复合 ID。
3. 已完成：将作者 JSON 的严格校验集中到 Python，`ChapterCatalog` 只解码规范化产物。
4. 已完成：为 ChapterCatalog、Markdown、FunctionRegistry 和 GTK 资源建立基础测试。
5. 已完成：从 `athena.json` 生成函数注册表，消除手写课程映射。
6. 已完成：生成稳定完整 ID，供 Catalog、注册表、测试和诊断复用。
7. 已完成：支持安全的一次性章节实现骨架生成。
8. 已完成：解决源代码展示的安装后资源策略。
9. 已完成：在 Ubuntu 上为 ArticleView 接入 WebKitGTK 6.0，复用现有 HTML、CSS、锚点和导航规则。
10. 已完成：按 ADR 0014 从低风险到高风险拆分 `MainWindow`。`AiService`、
    `ProgressPage`、`LearningDialogs`、`HandbookPage`、`CodeChapterPage`、非 GTK 的
    `ExperimentRunner`、`PocketCubePage` 与 `AboutDialog` 均已落地；窗口只保留导航、
    跨页协调和模块生命周期。统一知识点激活路径与常驻 WKWebView 规则保持不变。
11. 已完成：把 `TypeSemantics`（原 `.hpp`+`.cpp`）和 `RAII`（原 `.hpp`+ 3 个 `.cpp`）
    迁移为单文件 `.hpp`，对齐 6.1 的默认约定；三个已实现章节（连同 `Reference`）现在
    全部是单文件形态，`athena.json` 不再有任何 `source`/`implementation.source` 覆盖，
    源码框展示的都是完整、一致的整章代码。
12. 只有出现多前端或大量界面行为必须脱离 GTK 测试时，再考虑正式 Presenter/View
    接口。

## 7. MVC/MVP 决策

当前没有必要引入完整 MVC 或 MVP。GTK 控件本身已经承担 View，`ChapterCatalog` 是数据模型，`MainWindow` 可以暂时承担轻量协调职责。优先解决稳定 ID、注册表生成、配置校验和职责拆分，这些问题比增加模式类层次更直接。

如果未来出现以下情况，可以引入 Presenter：

- 同一课程模型需要支持多个前端。
- 大量 UI 行为需要无 GTK 单元测试。
- 窗口类仍包含复杂的导航、过滤、运行状态和错误恢复逻辑。

## 8. 学习内容的界面承载模型

这一节澄清一个反复出现的困惑：草图里“既有说明文字、又有图标、还有运行按钮和
预测选项”的混合界面，在桌面 GUI 里到底由什么承载、和 Markdown 是什么关系。

### 8.1 桌面 GUI 没有“富文档控件”

一个看起来像文章的交互页面，不是某一个特殊控件，而是**一批标准控件按纵向
顺序码进一个可滚动容器**：外层 `Gtk::ScrolledWindow`，内层 `Gtk::Box`
（`orientation: vertical`），里面依次是 `Label`（段落，`use-markup` 支持局部
加粗、等宽、颜色、链接）、`Image`、`Gtk::Box`（横向排一行按钮）、
`GtkSourceView`（只读代码）、`Gtk::Grid`（两列对照）等等。

“文档感”是排版的视觉结果，不是控件类型。业界把这种形态叫 *interactive
document*；notebook（Jupyter / Observable）是它最成熟的形式——交替排列的
“展示单元”和“交互单元”。

Blueprint（`.blp`）负责描述其中**静态或半静态**的部分：页面骨架、每种卡片的
模板、说明面板。**结构由运行时数据决定**的部分（有几个知识点、正文有几段、
几个小节）用代码按数据实例化模板或直接构建，见第 3 节“GTK 与 Blueprint 规则”。

### 8.2 Markdown 的三种角色

| 角色 | 做法 | 能否承载按钮 / 动态 |
|---|---|---|
| A 不用 Markdown | 每段文字写成一个 `Label`，控件直接穿插 | 能，控件就是真 widget |
| B 当富文本渲染 | `.md → HTML → WebView`，只作展示 | 不能，除非向 WebView 注入运行时脚本 |
| C 当结构化数据解析 | MD4C 解析成 AST，代码决定“普通段落→`Label`，自定义块 `:::experiment`→在该位置放一个原生实验 widget” | 能，自定义块位置换成真 widget |

“Markdown 只能承载文字和图片”这个判断**只在角色 B 成立**。角色 C 里 Markdown
只是一种内容数据格式，渲染成 HTML 还是控件由代码决定。

### 8.3 Athena 当前的分工

- **成篇理论（分类手册）**：角色 B。`resources/articles/**.md` → MD4C →
  HTML → `ArticleView`（macOS WKWebView / Ubuntu WebKitGTK 6.0）。纯展示，
  没有运行按钮，也不注入 JavaScript（`markdown_renderer` 的 C++ 词法着色是
  在生成 HTML 时完成的，不是运行时脚本）。见 ADR 0003、0012、0017。
- **可运行知识点（实验页）**：角色 A。`ExperimentPage` 的控件树写在 Blueprint
  里，`ExperimentDock` 装配 `GtkSourceView` 源码框、`TextView` 结果、运行按钮、
  `Spinner`。这里**完全不经过 Markdown**。
- **知识点的短引导句**（核心问题、预测提示、观察点、反思提示）：角色 A。
  文本来自 `athena.json` 的 `subchapter.learning` 字段（见
  `docs/CHAPTER_CONFIG.md`），用 `Label` 显示，不是一篇 Markdown 文章。

一句话原则：**短引导句是穿插在控件流里的 `Label`；成篇理论是单独用
Markdown → WebView 展示的文档；两者不塞进同一个渲染器。**

### 8.4 两条路线的权衡

把成篇内容也改用控件流（角色 A）承载，相对 WebView（角色 B）：

| 维度 | 控件流（角色 A / C） | Markdown + WebView（角色 B） |
|---|---|---|
| 交互 | 每个元素是真控件，信号、状态天然 | 静态；要交互需注入脚本并在两个后端各接一次桥 |
| 内容编写成本 | 高：没有“写纯文本即出版面”，富排版、图文环绕、表格、脚注都要自己实现 | 低：作者写 `.md` 即可 |
| 跨平台一致性 | 需要在 macOS / Ubuntu 两处调控件样式 | 一份 HTML/CSS 两平台基本一致 |
| 主题 / 无障碍 / 键盘导航 | 与应用其余部分天然统一 | 需要 WebView 内单独处理 |
| 图表 / 公式 / 语法高亮 | 代码高亮有 `GtkSourceView`，其余自己画 | HTML 生态成熟 |
| 依赖 | 去掉 MD4C / WebView 栈 | 保留 MD4C，两个平台各一个 WebView 后端 |

结论：短引导句和实验适合控件流；成篇理论目前仍适合 Markdown + WebView。
若要把成篇理论也迁到控件流、或解除 WebView 的“不注入运行时脚本”限制，属于
推翻 ADR 0003 / 0012 / 0017 / 0020 的不可逆方向，必须先新增 ADR。
