# ADR 0022：文档独立成窗口，实验坞作为它的对话框

- 日期：2026-09-01
- 状态：已接受，实施中
- 后续：ADR 0023 已取代本文的最终左右实验窗口及“文档窗口 → 模态实验窗口”终态；
  本文保留 `ExperimentDock` 复用、单例生命周期和第一阶段迁移的历史背景。
- 依据：`AGENTS.md`「GTK 与 Blueprint 规则」「架构原则（低耦合、SRP）」；
  与 ADR 0003 / 0017（ArticleView 后端）、ADR 0020（文档主导学习工作台）对照；
  用户对章节页右侧空间拥挤、文档和实验都缺少展开面积的反馈

## 背景

标准代码章节页 `resources/ui/chapters/empty_chapter.blp` 在一屏内塞了四块内容：
左侧整章源码框、右上知识点列表、右下结果框、底部知识点描述与运行状态。源码框占掉
大半宽度后，知识点列表和结果框都被压到很窄的右侧栏，长输出、宽代码都要来回滚动。

手册（`HandbookPage` + `ArticleView`）作为常驻 Stack 页塞在同一套 `chapter_stack`
里，宽度同样受主窗口其它布局牵制，长文档阅读体验受限。

主窗口真正需要常驻的是导航：面包屑、章节切换器、分类索引 / 首页学科图谱、知识点
列表。源码阅读、实验运行、文档阅读都是"展开来做"的活动，更适合各自独占一个可以
放大的窗口。

## 决策

### 1. 一个独立的**文档窗口**，实验坞是它的对话框

主从关系：文档窗口是阅读手册的主场，实验坞（源码 + 运行 + 结果）是"读到某个
知识点时打开来做一下"的附属，以对话框形式挂在文档窗口上。不是两个平级窗口。

- 新增 `ui/document_window`（`DocumentWindow`，派生自 `Gtk::Window`）和
  `ui/experiment_dialog`（`ExperimentDialog`，`Gtk::Window`，
  `set_transient_for(*document_window)`）。
  **模态性见下方「修订记录 2026-09-01」**：最初定为 `set_modal(false)`（一边看文档
  一边看实验），后改为 `set_modal(true)`。
- 两者都是**单例**：整个进程各一个实例，切分类 / 章节 / 知识点时更新内容，不新建。
  避开 GTK4 macOS 后端下多窗口的定位与 Space 归属问题。
- `DocumentWindow` 由 `MainWindow` 持有（`unique_ptr`），`set_transient_for(*this)`；
  `ExperimentDialog` 由 `DocumentWindow` 持有。都不是 `Gtk::ApplicationWindow`。
- 关闭按钮 = 隐藏而非销毁：`signal_close_request` 里 `set_visible(false)` 返回
  `true`。控件树、`ArticleView`、`ExperimentDock` 状态保留，下次 `present()` 即用。
- **不 `maximize()`**（GTK4 macOS 后端下会把窗口摆到工作区外）。固定
  `set_default_size`：文档窗 1280×1440，实验坞对话框 1200×900。

### 2. 结构

- `DocumentWindow`：主体是一个 `Gtk::Stack`，每个分类一个 `HandbookPage`（沿用现在
  的常驻策略，`ArticleView` 生命周期仍由 `HandbookPage` 独占）；`create_platform_article_view`
  的 `Gtk::Window&` 参数从主窗口改为 `DocumentWindow`。顶部一条工具栏放分类切换、
  字号、以及"打开实验坞"。
- 文档正文里 `render_markdown_html()` 插入的 `athena://knowledge/<id>` 链接被点击时，
  `DocumentWindow` 打开 `ExperimentDialog` 并加载对应实验（`ArticleView::set_link_handler`
  已是现成入口）。
- `ExperimentDialog` 的控件树写在 `resources/ui/experiment_dialog.blp`：整章源码
  （`GtkSource.View`）、结果（`Gtk::TextView`）、运行按钮、Spinner、状态标签、实验
  标题与目标标签，横向 `Gtk::Paned` 按“左侧源码、右侧实验操作坞”分栏；1200px
  默认宽度下初始位置为 720px，源码和右侧分别保留 680px / 420px 最小宽度。右侧不
  新增运行历史、AI、复制或重新定位入口，这些既有学习操作继续留在知识点行。
  `ExperimentDock` 接到这些控件上——它本就不拥有控件，几乎不改。

### 3. 主窗口与页面瘦身

- 主窗口回到纯导航：首页学科图谱、分类索引、章节页的知识点列表与说明。
- `empty_chapter.blp` 删除 `source_panel` / `result_panel` / 底部运行状态区，保留
  章节头、知识点列表、知识点描述。`CodeChapterPage` 不再构造内嵌 `ExperimentDock`。
- 第一阶段从标准章节页点“运行”：激活本行并让 `MainWindow` 打开
  `ExperimentDialog`，随后立即运行；从工作台正文点实验入口：只加载实验并等待用户
  在窗口中运行。文档窗口落地后，再把两条路径统一到文档位置。
- 点"手册"：`MainWindow` `present()` 文档窗口、切到对应分类、跳锚点。
- `WorkbenchPage` 与 `workbench_chapter.blp` 也改为走这套（它的 `workbench_dock_panel`
  删除）。

### 4. Blueprint 与生成流程

- `document_window.blp` 和 `experiment_dialog.blp` 不属于任何 `chapter`，参照
  `window.blp` 的处理：`meson.build` 各加一个 `blueprint-compiler compile` 的
  `custom_target`，产出 `.ui` 由 `scripts/project_generator/resources.py` 写进
  `/app` 前缀的 GResource 清单。

## 后果

- 主窗口回到"纯导航"，章节页显著变清爽；文档阅读和实验运行各自有可放大的面积。
- `ExperimentDock` 的两个使用方（`CodeChapterPage`、`WorkbenchPage`）统一指向同一个
  实验坞对话框，dock 控制逻辑集中，符合 SRP / 低耦合。
- 代价：新增 `DocumentWindow` + `ExperimentDialog` 两个类 + 两份 `.blp` +
  `meson.build` / `resources.py` 各两处；`empty_chapter.blp` 和
  `workbench_chapter.blp` 大改；`MainWindow` 增加窗口管理。
- 多窗口在 macOS：靠"单例 + `transient_for` + 不 maximize + 关闭即隐藏"四条规避
  已知问题；不允许后续在共享 / 领域层出现对这两个窗口的指针。

## 实施分步

1. **已完成**：`ExperimentDialog` + `experiment_dialog.blp` + meson / 生成器接线；`ExperimentDock`
   改接对话框控件；`empty_chapter.blp` 与 `CodeChapterPage` 去掉内嵌 dock；
   `MainWindow` 里选知识点先弹一个"临时挂在主窗口上的"实验坞对话框（文档窗口还没
   拆出来时的过渡）。
2. `DocumentWindow` + `document_window.blp` + meson / 生成器接线；把 `HandbookPage`
   的 Stack 迁进去；`ExperimentDialog` 的 `transient_for` 改到文档窗口；文档正文的
   `athena://knowledge/<id>` 链接接到"打开实验坞对话框"。
3. **已完成**：`WorkbenchPage` 与 `workbench_chapter.blp` 改为走这套。
4. 同步 `docs/ARCHITECTURE.md` 的导航与窗口描述。

## 修订记录

### 2026-09-01：`ExperimentDialog` 改为模态

- **原决策**：`set_modal(false)`，让实验窗口可与文档窗口并排，一边读一边看结果。
- **改为**：`set_modal(true)`。
- **原因**：
  1. 「AI 讲解」「AI 自测」两个按钮要从章节页知识点行迁进实验窗口右侧操作区
     （见方案第 3–6 项，分步实施）。这两个功能各自弹出的对话框本身就是模态
     （`lock_for_modal_dialog`）。若实验窗口非模态、其中的 AI 对话框模态，模态层级
     跨越一个非模态中间窗口，焦点与前置行为在 GTK4 macOS 后端下不稳。统一成
     「主窗口 → 模态实验窗口 → 模态 AI 对话框」的单链更可控。
  2. 运行实验是「专注做一下」的聚焦活动，实测中并排看文档的价值不高；文档正文里
     已有知识点讲解，实验窗口只需展示源码、运行、结果。
- **保留不变**：`set_transient_for`、`set_hide_on_close(true)`、单例复用、不 `maximize()`、
  固定 `set_default_size`。
- **待处理**：AI 对话框（`AiMarkdownDialog` / `QuizDialog`）的 `transient_for` 目前钉死
  主窗口，按钮迁入实验窗口时需要改成指向实验窗口（方案第 4 项的「模态套模态 parent
  链」）。本次修订只改实验窗口自身的模态性。
