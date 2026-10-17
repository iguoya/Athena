# T-102 审查报告：gtkmm 第 11–21 章译文忠实度

- 审查人：zcode · 2026-10-17
- 范围：课表 order 11–21（treeview、dropdown、combobox、textview、menus-and-toolbars、adjustment、dialogs、drawingarea、draganddrop、clipboard、printing），共 61 页，全部逐块读过（英中对照底稿在 `comms/gtkmm-review/artifacts/zcode/dump/11..21-*.txt`）。
- 基准与口径：同 T-101（`artifacts/zcode/report.md`）。原文=快照英文 `text`，译文=`zh`，语义以 docs.gtk.org 为准；术语表七条主译法不再报；标题/图注 zh 不审；缺译段不审、末尾单列。严重度：P0 误导学习者 / P1 明显缺陷 / P2 可改进。

## 发现（按严重度）

### P0（误导学习者）

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| P0-1 | `chapter-dialogs/sec-dialogs-alertdialog.json` 块 2、块 5 | 块 2 EN: "and a **`response` signal which is emitted when the user dismisses the dialog**" → ZH: 「且有一个**run()方法可以阻塞到用户关闭对话框**」；块 5 EN: "The **`response` signal handler** receives an `int`…" → ZH: 「**run()方法返回一个int**」。两处把 response 信号机制整体替换为 run() 方法：`run()` 是 GTK 4.10 起弃用的旧路径，而本章示例用的 `AlertDialog`（4.10+ 新类）**没有** run() 方法，正规用法是 set_visible(true) + 连接 response 信号（恰在缺译的块 6）。按译文学习者会在新 API 上找不存在的方法 | 块 2 改「并且有一个在用户关闭对话框时发出的 `response` 信号」；块 5 改「`response` 信号的处理函数接收一个 int…」；与补译块 6 同步 |

### P1（明显缺陷）

（待补）

### P2（可改进）

（待补）

## 各章结论（每章至少一行）

11. **treeview**（8 页全 translated）：P1 三处——全部是**行/列颠倒**（model 页块 14 "data in model rows"→「模型列中的数据」、块 36 "add it as a Model column"→「添加到模型的一个行中」、view 页块 8 "other column types / as the column type"两处→「行」），与前十章 misc 章 P1-5 同模式，直接干扰 TreeModelColumn 的使用理解。P2：丢链接 5 处（本页内锚点与外链都有）、「子物件/子行」不统一、「示例化」「构筑」「这这些」错字与两处残句；其余段落（dnd、contextmenu、新增弃用提示）质量好。
12. **dropdown**（6 页全 translated）：新译章节，语句质量好；P1 两处集中在 model 页——块 1 末句「DropDown 可选带 Entry 以便在长列表中搜索」**整句漏译**（恰是未决术语 Entry 的呈现点），块 2 后半「StringList 提供更简单的纯文本特化」**漏译**；块 0 有增译（把块 1 的「文字、图片、复合部件」搬进块 0，丢了「而非 cell renderer」的对比）。
13. **combobox**（6 页全 translated）：P1 三处——model 页块 1 "restricts the user to the available choices"（限制用户只能选可选项）误译「将**显示**用户的可选项」；model 页块 4/块 6 三处 **column 译成「行」**（与 treeview 章同模式）；comboboxentry 页块 8 末句「连接 `Entry` 的 `activate` 信号、添加 `Gtk::EventControllerFocus` 连其 `leave` 信号」**整句漏译**——与 T-101 P0-2（misc 章同源段）同一段落，activate 信号名在译文中无处可寻，判 P1（前半「回车/失焦=输入完毕」仍在，未到整段替换的 P0 程度）。
14. **textview**（3 页全 translated）：P1 两处——buffer 页块 5 "all **outstanding** iterators become invalid"（所有现存的迭代器都失效）误译「所有**越过修改范围的**迭代器都将失效」，弱化失效范围；块 36 覆盖方向**译反**："Some of these may be **overridden by** the `Gtk::TextTag`s"（视图设置可被 Tag 覆盖）译成「视图方法…可能会**覆写**缓冲区中的 `Gtk::TextTag`」，且 "if they specify the same things"（指定了同样的属性）误译「如果它们指定同一**区域**」。P2：「显式」错写成「显示」、properties 同页「属性/特性」不统一、examples 页丢外链 2 处。
15. **menus-and-toolbars**（5 页全 translated）：**无 P0/P1**，是 11–21 章目前最干净的一章；gio_resource 页段 3/6/10 质量好。P2 择要：段 0 首词「Menus」英文残留、「Gio::ResourceAPI」粘连、「引用了**那些**文件」应为「哪些」、段 6 增译「一个示例：」、menus-examples 段 1 "Classes are derived"（复数）译「**这个类**」、若干语序小错。
16. **adjustment**（3 页全 translated）：P1 一处——easy 页块 1 **一增一漏**：增译原文没有的「把 step_increment 作为单击步长」，漏译末句 "By default, they will only modify the `value` of an adjustment"（默认只改 value，不动 lower/upper——adjustment 语义的关键句）。**未决术语 Adjustment 在本章就有四种译法混用**：`Gtk::Adjustment` 对象 / 裸「调整」/「调整对象」/ 保留原文 Adjustment（详见术语汇总）。P2：creating 页块 4 残句（「与平移部件能见到的区域大小。」缺谓语「相对应」）、internals 页块 1 句读混乱（「value_changed信号你的程序也可以如此」缺标点、后半句「如果你操纵滚动条与其共享调整对象的其他可调整部件将会自动更新」不成句）、Scale 一处译「比例部件」与章内保留原文不统一、丢链接 1 处。
17. **dialogs**（6 页全 pending，缺译 8 段 para，见缺译清单）：**P0 一处**——alertdialog 页块 2 与块 5 把原文的 **`response` 信号机制整体替换为「run() 方法」**（「有一个run()方法可以阻塞到用户关闭对话框」「run()方法返回一个int」）；`run()` 属 4.10 弃用路径，本章示例用的 `AlertDialog`（4.10+）根本没有该方法，正规用法在缺译的块 6 里（set_visible + response 信号）——**补译块 6 应与修此 P0 同步做**，否则学习者按译文走死路。P2：windowdialog 页块 1 把 [Window Reference] 译「**部件**参考」（Window 是窗口）；filedialog 页块 1「该类」因块 0 缺译而无先行词；about 页两处语序。已译段（about 块 1 模态/非模态说明）质量好。
18. **drawingarea**（7 页全 pending，缺译 2 段 para：curved-lines 块 10 虚线说明、**arcs 块 0 弧度制与角度方向的核心教学段**）：**P1 一条（顶格）**——lines 页块 20/21「画细线」两段连续三处技术错位：① "Cairo will try to use half of each adjacent pixel, **which isn't possible**"（均分相邻像素不可能）译成「绘制一个像素宽度的线条**那是不可能做到的**」；② "the width of **the line** is an odd number of pixels" 译「**像素的宽度**是奇数」；③ "position **in the middle of the pixel**"（把位置定在像素中心）译「**将像素放于要绘制的线条的中间**」——核心技巧方向颠倒，本节教学点基本报废。P2：**Cairo 全章音译「开罗」**（含错字「开若」一处），与 gtkmm/Pango 等库名保留原文的做法不一致，建议 leader 定夺统一保留 Cairo；cairographics/cairomm/FAQ 外链丢 4 处；ticks 译「可读线」、clock 块 7 "our next lines"（接下来画的线）译「下一行」、wrapping（换行）译「环绕」、块 6 "scaled over and down"（缩放后平移）丢平移语义等。model/curved/arcs/images 页的机制讲解段（块 6/9/11 等）质量好。

## 未决术语用法汇总（wrap/wrapper、Entry、Adjustment）

（待补）

## 缺译段清单（供 leader 核对）

（待补：暂只记 para/listitem，heading/figure 按口径不算——treeview 章无 para/listitem 缺译）

## 明细

### 第 11 章 treeview

**P1（3 条）**

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| T11-P1-1 | `sec-treeview-model.json` 块 14 | EN: "use those `TreeModelColumn`s when getting and setting the data in **model rows**" → ZH: 「获取和设置**模型列**中的数据」 | 改「模型行中的数据」 |
| T11-P1-2 | `sec-treeview-model.json` 块 36 | EN: "just add it as a **Model column**, but don't add it to the View" → ZH: 「将其添加到**模型的一个行**中而不将其添加到视图中」（"Hidden" Columns 一节的核心操作） | 改「作为模型的一列添加」 |
| T11-P1-3 | `sec-treeview.json` 块 8 | EN: "For other **column types** … use (unsigned) int or (unsigned) long as the **column type** instead" → ZH: 「对于其他类型的**行**…作为**行**类型」（同段两处） | 两处「行」均改「列」 |

**P2（择要）**

| # | 位置 | 问题 |
|---|---|---|
| T11-P2-1 | `sec-treeview-model.json` 块 1 | "can contain lists or trees of data, **in columns**" → 「**每一行**都可以包含数据列表或数据树」：in columns 丢失、引入原文没有的「每一行」 |
| T11-P2-2 | `sec-treeview-model.json` 块 3 | "you will normally use either…" 增译「可以省略很多麻烦」 |
| T11-P2-3 | `sec-treeview-model.json` 块 14 | 残句「你TreeModelColumn实例添加到ColumnRecord」缺「把」；块 18 「示**例**化它」应为「实例化」、「使他」「访问他」应为「它」 |
| T11-P2-4 | `sec-treeview-model.json` 块 25 | child items 译「子**物件**」，章内其余处用「子行」，不统一 |
| T11-P2-5 | `sec-treeview.json` 块 3 | 「**构筑**完成后」错字，应为「构造」 |
| T11-P2-6 | `sec-treeview.json` 块 30 | 「你应该检查新值如果其对于你的应用程序而言是合适的则将其储存」语病 |
| T11-P2-7 | `sec-treeview-selection.json` 块 0 | "get the Gtk::TreeView::Selection object **from** the TreeView" 语序颠倒成「从TreeView的Gtk::TreeView::Selection对象获取」 |
| T11-P2-8 | `sec-treeview-sort.json` 块 3 | "supplying the **model column** on which model should be sorted" 关键参数说明未译，成「以提供此功能」；块 6 「让**这这些**树形视图」错字、「其提供了该模型的**将**已排序版本」残句 |
| T11-P2-9 | 丢链接 5 处 | `sec-treeview-draganddrop.json` 块 0（#chapter-draganddrop）、`sec-treeview-contextmenu.json` 块 0（#sec-menus-popup）、`sec-treeview-examples.json` 块 0（treeview directory 外链）、块 1（custom TreeModel 外链）、块 21（#sec-treeview-draganddrop）——链接文字都在但 `[文字](url)` 全部丢失，不可导航 |
| T11-P2-10 | `sec-treeview-examples.json` 块 21 | "It uses a **derived** Gtk::TreeStore which overrides…" 漏译 derived，且「通过从Gtk::TreeStore来覆盖虚函数」残句 |

### 第 12 章 dropdown

**P1（2 条）**

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| T12-P1-1 | `sec-dropdown-model.json` 块 1 | EN 末句 "The `DropDown` widget can optionally have an `Entry` in the dropdown menu, allowing the user to search in a long list." 整句漏译——恰是「未决术语 Entry」在本章的呈现点，也丢了对 search 页的导引 | 补译「`DropDown` 还可以选择在下拉菜单中带一个 `Entry`，让用户能在长列表中搜索」 |
| T12-P1-2 | `sec-dropdown-model.json` 块 2 | EN 后半 "This provides flexibility, but the `StringList` class provides a simpler text-based specialization in case that flexibility is not required." 漏译——StringList 这个更简单的替代方案在本章再无第二次出现 | 补译「这提供了灵活性；若用不着这种灵活，`StringList` 类提供了更简单的纯文本特化」 |

**P2（1 条）**

| # | 位置 | 问题 |
|---|---|---|
| T12-P2-1 | `sec-dropdown-model.json` 块 0 | EN "the content is displayed using widgets **instead of cell renderers**" 的对比丢失；增译「可以是任意内容——文字、图片，乃至更复杂的复合部件」（系把块 1 的内容提前搬来，原文此句没有） |

### 第 13 章 combobox

**P1（3 条）**

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| T13-P1-1 | `sec-combobox-model.json` 块 1 | EN: "The `ComboBox` widget usually **restricts the user to the available choices**, but it can **optionally** have an `Entry`…" → ZH: 「通常**将显示用户的可选项**，但是它可以有一个 Entry」——restrict（限制用户只能选可选项）误译为「显示」，与 Entry 例外的对比逻辑随之丢失 | 改「通常把用户限制在可选项之内，但也可以选择带一个 `Entry`」 |
| T13-P1-2 | `sec-combobox-model.json` 块 4、块 6 | EN 块 4 "one integer and one text **column**" → 「一个整数**行**和一个文本**行**」；块 6 "specify what **columns** will be displayed" → 「指定哪个**行**将要被组合框显示」、"specify a particular **mapping**" → 「指定具体映射到哪**行**」（mapping 指 CellRenderer 属性与模型**列**的映射）。同页三处行/列颠倒 | 三处「行」均改「列」 |
| T13-P1-3 | `sec-comboboxentry.json` 块 8 | EN 末句 "To be notified of these events, connect to the `Entry`'s **activate** signal (available since gtkmm 4.8), and add a `Gtk::EventControllerFocus` and connect to its **leave** signal, like so" 整句漏译——本节核心操作指引，activate 信号名全章译文再无出现；与 T-101 P0-2（misc 章同源段）同一上游段落 | 补译该句（信号名与 gtkmm 4.8 版本注都要） |

**P2（3 条）**

| # | 位置 | 问题 |
|---|---|---|
| T13-P2-1 | `sec-combobox-changes.json` 块 0 | "you should handle the `changed` signal" → 「你应该处理changed。」——丢「信号」二字，信号名成光杆残句 |
| T13-P2-2 | `sec-comboboxentry.json` 块 2 | "specify **which** of your model columns is the text column"（单数：哪一列）→ 「指定**哪些**模型列是文本列」，暗示可多列 |
| T13-P2-3 | `sec-combobox-get.json` 块 0 | 「读取模型中储存于该行的整数ID值（于并未被显示的列）」语序别扭，括号为增译 |

### 第 14 章 textview

**P1（2 条）**

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| T14-P1-1 | `sec-textview-buffer.json` 块 5 | EN: "Whenever the buffer is modified in a way that affects the number of characters in the buffer, **all outstanding iterators become invalid**" → ZH: 「所有**越过修改范围的**迭代器都将失效」。outstanding＝当前持有/存活的所有迭代器（docs.gtk.org：任何影响字符数的修改使**全部**迭代器失效），译文弱化成「修改范围之外的」失效，读者可能以为范围外的迭代器仍可用 | 改「所有现存的迭代器都会失效」 |
| T14-P1-2 | `sec-textview-buffer.json` 块 36 | EN: "Some of these may be **overridden by** the `Gtk::TextTag`s in the buffer, **if they specify the same things**" → ZH: 「如果它们指定同一**区域**，则其中一些可能会**覆写**缓冲区中的 `Gtk::TextTag`」。①覆盖方向反：实际是 Tag 覆盖视图级设置（set_left_margin() 等），不是视图方法覆写 Tag；②"same things" 指指定了同样的**属性**，不是「区域」 | 改「其中一些设置可能会被缓冲区中指定了同样属性的 `Gtk::TextTag` 覆盖」 |

**P2（3 条）**

| # | 位置 | 问题 |
|---|---|---|
| T14-P2-1 | `sec-textview-buffer.json` 块 17 | "instead of creating one **explicitly**" → 「而不是**显示**创建一个」，「显式」错写成「显示」 |
| T14-P2-2 | `sec-textview-buffer.json` 块 12 | "many other **properties**" 译「许多其他的**特性**」，同页块 9/块 24 均译「属性」，不统一；块 0 "In this case the TextBuffer is the model" 增译「**预期的**模型」、块 1「复数个」为 plural 直译 |
| T14-P2-3 | `sec-textview-examples.json` 块 6、块 7 | 原文的页内锚点链接（#sec-i18n-example）与 gtkmm demo 外链（gitlab URL）均丢，链接文字在但 `[文字](url)` 不存 |

### 第 15 章 menus-and-toolbars

**P0/P1：无。**

**P2（择要 1 条合并）**

| # | 位置 | 问题 |
|---|---|---|
| T15-P2-1 | 多处 | `sec-menus-popup.json` 块 0 首词「Menus」英文残留；`sec-gio-resource.json` 块 1 「Gio::Resource**API**」粘连、块 2 「引用了**那些**文件」应为「哪些」、块 6 增译「一个示例：」（上段 An example 已译过）、块 0 "included as literal strings in the code" 的「字面字符串」丢失；`sec-menus-examples.json` 块 1 "Classes are derived from…"（你写的两个类分别派生）译「**这个类**是自…派生而来」；`sec-menubar-and-toolbar.json` 块 5 「这些的字符串」语序。另：menus-examples 页有一批 EN 为空串的 heading 块（6–12、20–22、29），系快照提取产物，非译文问题 |

### 第 16 章 adjustment

**P1（1 条）**

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| T16-P1-1 | `sec-adjustments-easy.json` 块 1 | EN: "They will treat the lower and upper values of an adjustment as a range within which the user can manipulate the adjustment's value. **By default, they will only modify the value of an adjustment.**" → ZH: 「它们会把 lower 与 upper 值当作范围的上下限，**把 step_increment 作为单击步长**。」——末句「默认只修改 value（不动其他字段）」整句漏译，属 adjustment 语义的关键约定；增译的「单击步长」原文没有 | 补译「默认情况下，它们只会修改 adjustment 的 `value`」；增译句可保留但需 leader 定夺 |

**P2（2 条）**

| # | 位置 | 问题 |
|---|---|---|
| T16-P2-1 | `sec-creating-adjustment.json` 块 4 | "The page_size argument usually corresponds somehow to the visible area of a panning widget" → 「page_size参数通常以某种方式与平移部件能见到的区域大小。」——缺谓语「相对应」，残句；另 value 参数句丢了「位置」（topmost or leftmost position） |
| T16-P2-2 | `sec-adjustment-internals.json` 块 1 | 句读混乱：「…连接到其调整对象的value_changed信号你的程序也可以如此。」缺标点；后半句「如果你操纵滚动条与其共享调整对象的其他可调整部件将会自动更新」不成句。块 4 "scale widget" 译「**比例**部件」，章内其余处保留 Scale 不译。`sec-creating-adjustment.json` 块 0 丢 #chapter-range-widgets 锚点链接、块 0 末句「表达了它的共有部分的API」拗口；internals 块 0 EN 的口语引导（"OK, you say, that's nice, but…"）整段丢失、句末不成句 |

### 第 17 章 dialogs

**P0（1 条，已列入总表 P0-1）**

**P2（2 条）**

| # | 位置 | 问题 |
|---|---|---|
| T17-P2-1 | `sec-dialogs-windowdialog.json` 块 1 | "[Window Reference]" 译「**部件**参考」——`Gtk::Window` 是窗口不是部件，且全章其余 Reference 行均只译「参考」 |
| T17-P2-2 | `sec-dialogs-filedialog.json` 块 1 | "Most of the useful member methods **for FileChooserDialog**" 译「**该类**的大部分…」，因块 0 缺译而无先行词（补译块 0 后自然消解）；`sec-dialogs-alertdialog.json` 块 3 "used for most simple notifications" 译「多被用于简单的通知」（应为「用于大多数简单通知」）；`sec-about-dialog.json` 块 0 「显示程序有关信息」缺「与…的」 |
