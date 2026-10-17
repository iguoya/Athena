# T-103 审查报告：gtkmm 第 22–31 章译文忠实度

- 审查人：zcode · 2026-10-17
- 范围：课表 order 22–31（recent-documents、keyboardevents、timeouts、memory、builder、internationalization、customwidgets、multi-threaded-programs、recommended-techniques、building-applications），共 36 页，英中对照底稿在 `comms/gtkmm-review/artifacts/zcode/dump/22..31-*.txt`（本次新生成）。
- 基准与口径沿 T-101（`artifacts/zcode/report.md`）：英文 `text` 为快照原文，`zh` 为译文；语义以 docs.gtk.org 为准。严重度：P0 误导学习者 / P1 明显缺陷 / P2 可改进。
- 丢链接口径：链接丢失但译文完整可读记 P2；链接丢失导致残句或语义丢失记 P1。
- 术语表 `glossary.json` 七条主译法已统一，不重复报告；heading/figure 不审。

## 发现（按严重度）

### P0（误导学习者）

（待各章审完后汇总；逐章明细见下方「各章明细」）

### P1（明显缺陷）

（待各章审完后汇总）

### P2（可改进）

（待各章审完后汇总）

## 各章明细（逐段落盘）

### 22 · chapter-recent-documents（2 页，30 文字段 28 有 zh）

- **P1（1 条）** `sec-filechooser-filedialog.json` 块 4/6：EN "a simple example of how to use the **`FileDialog`** class"（块 2 明说 FileChooser 系自 4.10 弃用、由 `FileDialog` 取代）→ ZH「如何在程序中使用 **FileChooserDialog** 类的简单示例」「选择 **File Chooser Dialog** 菜单项和 Recent 侧边项后」。新 API `FileDialog` 全段被写成弃用类 `FileChooserDialog`，学习者按译文去查文档会查到已被替代的类。建议三处「FileChooserDialog/File Chooser Dialog」改回「FileDialog/File Dialog」。
- P2：`sec-recentmanager.json` 块 1 「如何描述文件、**及其它的**MIME类型」——"its mime type" 是「它的 MIME 类型」，「及其它」是错字且产生「以及其他类型」歧义，改「及其」；块 15「从**列表项**中删除、修改、查找项目」应为「从列表中」；块 17「如果指定的URI**于**最近文件列表中不存在」的「于」应为「在」。`sec-filechooser-filedialog.json` 块 14 "apply a filter to a **chooser widget**" 译「应用于**你所选的部件**」——chooser widget 指 FileChooser 系部件本身，不是使用者选中的部件，建议「应用于文件选择器部件」。
- 丢链接（P2）：`sec-recentmanager.json` 块 19 EN "the properties listed [above](#list-file-metadata)" → ZH「查找这里所列出的任何属性」，锚点链接丢失，建议补 `[上文](#list-file-metadata)`。
- 结论：recentmanager 页译文忠实、平实；filechooser 页 FileDialog/FileDialogDialog 类名错译需修。

### 23 · chapter-keyboardevents（3 页，22 文字段 14 有 zh）

本章是已审各章中质量最差的一章：**大量段落是 gtkmm3 旧译文对 gtkmm4 新原文的错位残留**，多处整段机制描述与原文对不上。

- **P0（3 条）**
  - `sec-keyboardevents-propagation.json` 块 7：EN "there are **9 `EventControllerKey`s, 3 in each of a `Gtk::Window`, a `Gtk::Box` and a `Gtk::Label`. In each of the widgets there is one event controller for each propagation phase.**" → ZH「Gtk::Window在默认事件处理程序之后调用了三个事件处理程序，一个在Gtk::Entry中、一个在Gtk::Grid中、一个在Gtk::Window中。」——控制器数量（9→3）、部件（Box→Grid、Label→Entry）、「每阶段各一个控制器」机制全错，是 gtkmm3 旧示例（Entry/Grid/Window）译文残留。按原文重译。
  - 同文件块 9：EN 讲 **key press** 事件在 `Label` 上按 capture→target→bubble 三阶段的完整传播路径 → ZH「当你在**条目**中写入的时候，将发出一个**按键放开**事件……**windowKeyReleaseBefore()**将先被调用。然后调用**已被覆盖的默认信号处理函数**……」——整段被 gtkmm3 旧示例描述替换，按键类型（press→release）、目标部件（Label→Entry）、三阶段机制、函数名全错。按原文重译。
  - `sec-keyboardevents-mouse.json` 块 1：EN "You use `Gtk::GestureClick` instead of `Gtk::EventControllerKey`." → ZH「**Gtk::FontButton实现了Gtk::FontChooser接口。**」——与原文完全无关的错位填充（内容属于 misc 章），鼠标事件教学点丢失。按原文重译。
- **P1（5 条）**
  - `sec-keyboardevents-overview.json` 块 2/3：EN "the arguments are (`guint` `keyval`, `guint` `keycode`, `Gdk::ModifierType` `state`)" / "read the value of the **`keyval` argument**" → ZH「它接受一个 **GdkEventKey\*参数**」「读取 **GdkEventKey::keyval** 的值」——gtkmm4 的 `EventControllerKey` 信号处理器是三参数签名，译文写成 gtkmm3 的 `GdkEventKey*` 结构体指针旧 API，按译文写代码必然编译失败。按原文改为三参数。
  - `sec-keyboardevents-overview.json` 块 0：EN "Event signals differ… described in the [Event signals](#sec-eventsignals) section… use **keyboard events and mouse events**" → ZH「**X事件**与其他信号在某些方面有所不同。这些差异在附录的**X事件信号**小节中说明。在这，我们将使用键盘事件说明……」——两处「X」怪字（疑为旧版实体替换残留）、丢附录链接、漏译 "and mouse events"。重译该段。
  - `sec-keyboardevents-overview.json` 块 1：EN "You can **add an event controller** and connect a signal handler" → ZH「你可以连接到信号处理函数来处理此类事件」——漏译半句，丢 gtkmm4 核心概念 EventController。补译。
  - `sec-keyboardevents-overview.json` 块 7：EN 只有三个快捷键介绍（Alt+1/Alt+2/Esc closes the window）→ ZH 末尾增译「**默认信号处理函数被覆盖如附录中覆盖默认信号处理函数小节所述。**」（旧版原文残留，本版无此内容），且 "closes" 增译成「隐藏（关闭）」。删增译。
  - `sec-keyboardevents-propagation.json` 块 4：EN 后半 "The event will then **propagate up until it reaches the top-level widget, or until you stop the propagation by returning `true`** from an event handler" 整句漏译（本页核心机制：向上传播+返回 true 停止）；开头还增译「**与其他事件相反**」（原文无）。补译后半句、删增译。
  - `sec-keyboardevents-mouse.json` 块 2：EN "There are other event classes… for instance `Gtk::EventControllerMotion` and `Gtk::EventControllerScroll`." → ZH「Gtk::EventControllerKey, Gtk::EventControllerMotion, Gtk::EventControllerScroll和Gtk::GestureStylus」——残句（不成句），且 Key/GestureStylus 为旧版残留列举。按原文改写成完整句。
- P2：`sec-keyboardevents-mouse.json` 块 5 EN 快照本身含未展开 DocBook 实体 `[Reference](&url_refdocs_base_gtk_html;classGtk_1_1EventController.html)`，ZH「参考」无法保留链接——快照工程问题，记入供 leader 对照（同模式段落他章可能也有）。
- 术语记录：Entry 在 propagation 块 9 译「**条目**」（「当你在条目中写入」）；该段重写后可顺带定译法。
- 结论：整章需按 gtkmm4 原文重译的段落集中在 overview 块 0–3、propagation 块 4/7/9、mouse 块 1/2；已译段落里没有一段可放心直接沿用。

### 24 · chapter-chapter-timeouts（3 页，20 文字段 20 有 zh，全译）

- **P1（1 条）** `sec-monitoring-io.json` 块 10：EN 末句 "A **lambda expression** can be used, if you don't need the automatic disconnection that `sigc::mem_fun()` provides when the object goes out of scope." 整句漏译——lambda 用法及其与 mem_fun 自动断连的取舍是本节实用知识点。补译。
- P2：`sec-monitoring-io.json` 块 2「第三个参数可能是**一下**的一项或多项」——「一下」为「以下」错字；同句括号注（`Glib::IO_IN | Glib::IO_OUT | Glib::IO_PRI` 示例）为原文没有的增译，内容正确可保留或删。`sec-timeouts.json` 块 0 漏 "Using the following methods"（用下面的方法）半句。
- 结论：全章已译完且整体忠实，是本批质量较好的一章；仅 lambda 漏句与个别错字。

### 25 · chapter-memory（2 页，26 文字段 22 有 zh）

- **P1（6 条）**
  - `sec-memory-shared-resources.json` 块 3：EN "You have no way of getting a **bare** `Gdk::Pixbuf`" → ZH「你无法**暴露**Gdk::Pixbuf对象」——getting a bare（拿到裸对象）译成「暴露」，本句教学点（只能经 RefPtr、拿不到裸 Pixbuf）丢失。改「你没办法获得一个裸的 Gdk::Pixbuf」。
  - `sec-memory-shared-resources.json` 块 0：EN "**Cairomm** has its own smartpointer, `Cairo::RefPtr<>`" → ZH「**开罗**有自己的智能指针」——库名 Cairomm 误译为「开罗」。改「Cairomm 有自己的智能指针」。
  - `sec-memory-shared-resources.json` 块 6：EN "If you copy a `RefPtr`, for instance" → ZH「你可以像对正常指针进行类型转换一样，将RefPtr转换到基础类型。」——旧版「cast away」段落残留，与本句无关；同时块 8 的 ZH 开头是「如果你复制一个RefPtr，例如：，……」（把块 6 原文并进了块 8，且「例如：，」残句）。块 6 改译「如果你复制一个RefPtr，例如」，块 8 从「或者」起译。
  - `sec-memory-widgets.json` 块 9：EN "the increased data hiding and **reduced dependencies**" → ZH「增加了数据的隐蔽性和**隐藏了依赖**」——「减少依赖」译成「隐藏依赖」，函数作用域优点的语义错。改「减少了依赖」。
  - `sec-memory-widgets.json` 块 13/15：块 13 ZH 末尾「在这，程序员删除pButton以防止内存泄漏。」是 EN 块 15（缺译段）的内容被错并进上一段，原文块 13 无此句。从块 13 删除该句、给块 15 补译。
  - `sec-memory-widgets.json` 块 25：EN "Or you can let **Gtk::Application::make_window_and_run()** create a top-level window and delete it when it's closed." → ZH「**例如，你的顶级窗口可能只是main()函数中的一个实例。**」——整句被 gtkmm3 旧版内容替换，make_window_and_run() 教学点丢失。按原文改译。
- P2：`sec-memory-widgets.json` 块 23「主动**deletepButton**」缺空格；块 5 "failing to `delete`"（未能 delete）译「delete部件出现差错」，建议「忘记 delete」；`sec-memory-shared-resources.json` 块 9 "See the [appendix](#chapter-refptr)" 丢链接（「请参见附录」可读），建议补 `[附录](#chapter-refptr)`。
- 结论：memory-widgets 页大体忠实但错位三处；shared-resources 页块 3/6 语义损失重，该页前半需按原文重译。

### 26 · chapter-builder（3 页，27 文字段 24 有 zh）

本章被 gtkmm3/Glade 时代旧译文系统性污染：新工具 **Cambalache 全章被译成 Glade**（`Cambalache`→「Glade」），`.ui` 文件多处译成「Glade 文件」，而原文明确说明 Cambalache 取代 Glade、Glade 不支持 gtk4。

- **P0（1 条）** `sec-builder-accessing-widgets.json` 块 1：EN "The dialogs in this chapter are derived from `Gtk::Window` because **`Gtk::Dialog` is deprecated since gtkmm 4.10**." → ZH「再次步骤中，我们使用Gtk::Builder实例将Gtk::Builder UI文件和我们的应用程序窗口类相关联。」——整段被旧版无关内容替换，「Gtk::Dialog 自 4.10 弃用」这一关键弃用提示丢失（任务书重点项「是否弃用」）。按原文重译。
- **P1（5 条）**
  - 全章 Cambalache→Glade 混淆（6 处）：`sec-builder-loading-ui-file.json` 块 0（"[Cambalache](https://gitlab.gnome.org/jpu/cambalache) application"→「Glade应用程序」，外链丢失）、`sec-builder-accessing-widgets.json` 块 0（"specified in the `Cambalache` window"→「在Glade的窗口属性中指定」）、块 8 与 `sec-builder-using-derived-widgets.json` 块 17（"load a `.ui` file"→「加载Glade文件」）、derived 块 0（"You can use `Cambalache` and `Gtk::Builder`"→「Gtk::Builder和Glade」）。全部改回 Cambalache／`.ui` 文件。
  - `sec-builder-loading-ui-file.json` 块 7/9 错位：块 7 ZH 末尾「这将实例化.glade文件中定义的窗口」是 EN 块 9（缺译）内容错并进上一段，且 `.ui` 写成 `.glade`；块 7 本身应止于「例如：」。拆开补译块 9。
  - `sec-builder-using-derived-widgets.json` 块 3：EN 例证 "`Gtk::Window` typedefs `BaseObjectType` as `GtkWindow`" → ZH「**Gtk::Dialog**将**GtkDialog**别名为BaseObjectType」——例证类名被旧版示例（Dialog）替换，与原文不符。改回 Window/GtkWindow。
  - `sec-builder-using-derived-widgets.json` 块 8/10 错位：块 8 ZH 末尾「可以调用此构造函数：」是 EN 块 10 内容错并；块 10 本身 EN "can invoke this constructor" 被填成「手工编码构造函数」（旧版残留，与本句无关）。块 8 删错并句，块 10 改译「可以调用这个构造函数」。
  - `sec-builder-using-derived-widgets.json` 块 15：EN 无版本前提、末句为 "add a few lines of **hand-coded XML** to the XML code generated by `Cambalache`" → ZH 开头增译「如果将gtkmm与**glibmm2.62以上的版本**一起使用」（旧版原文残留）、`.ui` 写成「.glade文件」、末句被替换为「通过使用**属性类定义和声明一个新属性目录**来实现」（旧版内容，与手写 XML 修补不同）。按本版原文重译。
- P2：`sec-builder-accessing-widgets.json` 块 0 "to show a dialog" 增译成「show()一个对话框」（函数名为增译）；块 5 "see the [Memory Management](#chapter-memory) chapter" 丢链接（「参阅内存管理章节」可读）；块 6 Reference 实体未展开（快照问题，同 23 章）。
- 结论：全章需先清理 Glade 时代残留（Cambalache/.ui/两处块错位/Dialog 例证）再谈润色；错位与替换集中，修复面大但点状。

### 27 · chapter-internationalization（6 页，62 文字段 55 有 zh）

- **P1（7 条）**
  - `sec-internationalization-intro.json` 块 5/16：EN "GUI resource files such as **`.ui` files**" / "including `.ui` files… add your `.ui` files to the list" → ZH「**glade的GUI资源文件**」「如**GladeUI文件**…如果你使用**Glade**设计了应用程序UI，则你还需要将**.glade**添加到…」——`.ui` 全部残留为 Glade/.glade（gtkmm3 时代写法），与 builder 章同根；块 16 还丢了 `.desktop` 文件规范链接。改回 `.ui`。
  - `sec-i18n-marking-strings.json` 块 2/4：EN 块 2 末 "and then, for example, **substitute:**"（代码示例 3）、块 4 "**with:**"（代码示例 5）是「替换前→替换后」两段结构 → ZH 块 2 压缩成「然后将：替换为：」（不知所云），块 4 缺译。块 2 改「然后，例如，替换：」，块 4 补译「为：」。
  - `sec-i18n-marking-strings.json` 块 19：EN 末句 "A `fuzzy` tag appears **if a string content changed, but the location is still the same**."（fuzzy 出现的成因）漏译；同时增译括号注「（通常该标记意味着翻译需要更新，不检查翻译直接删除标记是不对的）」——内容合理但原文无、且原文前句是 "simply remove"，增译与之有张力。补译成因句；括号注要么删、要么改为明确标注为译者注。
  - `sec-i18n-marking-strings.json` 块 22–25（Resources 节）：EN 四个外链（L10N Guidelines、Intltool README、Git for GNOME translators、gettext manual）→ ZH 全部只留文字丢链接（如「本地化开发人员指南」「gettext手册」），资源节失去可达性。补 `[文字](url)`。
  - `sec-i18n-getting-help-with-translations.json` 块 0：EN "If your program is **free software**" → ZH「如果你的程序是**免费软件**」——free software 是「自由软件」（许可证要求），译「免费」误导加入条件；且丢 GNOME Translation Project 链接。
  - 同文件块 1：EN "file an [issue to the **damned-lies** project](…) and ask to have your program added to the [list of modules to translate](…)" → ZH「然后**联系gnome-i18n**请求将你的程序添加到待翻译模块列表中」——提交流程被旧版做法（联系邮件列表）替换，两个链接全丢。按本版流程重译。
  - 同文件块 2：EN "simply **freeze the strings** at least a couple of days before you make a new release" → ZH 增译「**在gnome-i18n邮件列表上宣布**冻结字符串更改」（旧版流程残留）。删增译。
- P2（择要）：错字族——intro 块 1「容易**的**多」、块 17「将**一下**代码」（→以下）、expecting-utf8 块 0「指针**算数**」（→算术）、pitfalls 块 16「不常见的**用于**例如缩写」（→用语）、getting-help 块 2「字符串**数数量**」；intro 块 6 丢 autogen.sh 外链（文字可读）；块 10 末增译「通常做法是在po文件夹再创建一个ChangeLog文件…」（旧版内容，无害但原文无）；块 12 "a **system-wide** directory" 译「**系统所有的**区域设置文件夹」（→系统级）；块 13「它将**从中**寻找」指代不明；块 17 末「编码设置（在标头中指定，但也指定其内容的编码）为了UTF-8」括号增译+残句；块 20 "has been an alternative to" 译成「已由…替代」（方向反，结论恰好相同）；pitfalls 块 8/16 各有一句原文没有的延伸断言（「这会导致很多字符串无法被正确翻译」「最好使用application而不是app」）；pitfalls 块 11 compose() 链接为未展开实体（快照问题）。
- 结论：概念段（marking/pitfalls/utf8 正文）忠实度尚可；**流程与资源段（intro 尾部、getting-help 全页、Resources 节）是旧版流程残留重灾区**，链接系统性丢失；例页（sec-i18n-example）首两段整段缺译。

### 28 · chapter-customwidgets（3 页，32 文字段 22 有 zh）

本章核心教学内容（需覆写的虚方法列表）函数名错位集中，是 gtkmm3 旧 API 名残留的又一重灾区；`sec-custom-css-names` 页几乎整页缺译。

- **P1（3 条）**
  - `size_allocate_vfunc()` 全部残留为 `on_size_allocate()``（gtkmm3 默认信号处理器名，gtkmm4 应覆写虚函数 size_allocate_vfunc()）：`sec-custom-containers.json` 块 4（列表项本身）、块 5（正文复述）、块 7，`sec-custom-widgets.json` 块 4。按译文覆写 `on_size_allocate()` 无法生效。四处改回 size_allocate_vfunc()。
  - `sec-custom-widgets.json` 块 5/6：EN "**on_realize()**: (optional)" → ZH「**on_map()**：…」、EN "**on_unrealize()**: (optional)" → ZH「**on_unmap()**：…」——两个生命周期方法的函数名被错填成 map/unmap，与块 7/8 重复，`on_realize`/`on_unrealize` 从方法列表中消失（GTK4 自定义部件的关键方法）。块 5 改 on_realize()、块 6 改 on_unrealize()。
  - `sec-custom-widgets.json` 块 12：EN "The **[custom CSS name example](#custom-css-name-example)** shows how that's done." → ZH「**以下示例**演示了如何完成这些操作。」——指代错误（读者会去看本页 Penrose 示例，而 class init 用法在 CSS name 一节的示例里），且丢链接。改「自定义 CSS 名称示例一节演示了如何完成这些操作」。
- P2：`sec-custom-containers.json` 块 1「应重写**一下**虚方法」（→以下）；块 3 与 `sec-custom-widgets.json` 块 3 "the minimum **and** natural width or height" 均译「最小自然宽度/高度」丢「和」；containers 块 3 "Calculate" 译「返回」；块 7 末句 "It's your container, so you decide." 漏译；块 10 "a container with child widgets, one above the other" 增译成「具有**两个**子部件」；`sec-custom-widgets.json` 块 1「覆写」与 containers 块 1「重写」同概念两种叫法（本章内混用）；块 10 丢 Custom Containers 节链接（文字可读）。
- 结论：containers/widgets 两页主体结构在、大段忠实，但虚方法名错位直接破坏本章教学核心，须优先修；css-names 页 12 个文字段全缺（见缺译清单）。

### 29 · chapter-multi-threaded-programs（3 页，16 文字段 16 有 zh，全译）

- **P1（2 条）**
  - `sec-the-constraints.json` 块 6：EN "Any `sigc::connection` object should be regarded as owned by **the thread in which the method returning the `sigc::connection` object was called**." → ZH「任何sigc::connection对象都应**视线程的拥有者在此线程调用了返回sigc::connection对象的方法**」——残句，规则 3（connection 归属）无法从译文重建。改「应视为由『调用返回该 connection 对象的方法』时所在的线程拥有」。
  - `sec-using-glib-dispatcher.json` 块 2：EN "with a thread-safe **(asynchronous)** queue. **At the time of writing** `glibmm` does not have one, although most people writing multi-threaded code will have one available to them" → ZH「使用线程安全的（**同步**）队列。尽管大多数编写多线程代码的人都会有一个可用的**多线程代码**，但是**编写glibmm时没有**」——① asynchronous 译反成「同步」；② "At the time of writing"（撰写本文时）错挂到「编写glibmm时」；③ "have one（队列）available" 译成「有一个可用的多线程代码」。整句需重译。
- P2：`sec-the-constraints.json` 块 1 "These interactions **arise from** the fact" 译「这些交互**产生了**以下事实」（因果倒置，同上轮 changes-gtkmm3 块 0 模式），且 "on disconnection or destruction"（slot 自身断连/析构时）主体错挂到 sigc::trackable；块 3「这些规则**下下面**列出」错字；块 8 "nulling those slots **by disconnecting them or destroying the trackable object**"（通过断连或销毁对象来置空槽）译成「在sigc::trackable对象断开连接和被销毁时」，操作方式变时间状语，所有权范围弱化；`sec-using-glib-dispatcher.json` 块 1「程序的**主进程**」（主线程）、「任何工作**现场**」（线程）两处概念错字；块 3 "the pipe could … fill up"（管道被填满）译「至少可以填满**系统**」对象错，且 "block on the write"（阻塞在写上）漏译。
- 结论：全章已译完，规则 1/2/5 与示例页忠实度高；但规则 3 残句与 Dispatcher 队列段两处 P1 需先修。

### 30 · chapter-recommended-techniques（2 页，12 文字段 11 有 zh）

- **P0（1 条）** `sec-application-lifetime.json` 块 1：EN "Use **`Meson`**! It is your friend :) It examines C and C++ files … generates **`build.ninja`** or an equivalent file …" → ZH「使用**GNU autoconf和automake**。Automake检查**C文件**…并生成**Makefile**…」——整段构建建议被 gtkmm3 旧版替换：Meson→autotools、build.ninja→Makefile、C and C++→只 C。与全书现状（i18n 章明言 autotools 不推荐用于新应用）相反，直接误导学习者选错构建系统。按本版原文重译。
- **P1（1 条）** `sec-using-a-gtkmm-widget.json` 块 1：EN "create it with `new` **or `Gtk::make_managed()`** in your code." → ZH「**使用new创建它**」——漏 `Gtk::make_managed()`（gtkmm4 推荐方式）；同时末句「即使通过指针使用部件，也应该使该指针成为容器类的成员变量，以便你后续访问它」为原文没有的增译（旧版残留）。补 make_managed()、删增译。
- P2：`sec-application-lifetime.json` 块 3 "as described in the `libsigc++` documentation" 译「libsigc++所述的」丢「文档」；块 5「示例都是**是用**这种技术」（→使用）；`sec-using-a-gtkmm-widget.json` 块 3「为**所以**你需要使用的信号」（→所有）；块 5 EN 两处 `Gtk::Widget::set_visible(false)` 译成 `Gtk::Widget::hide()`（功能等价但与原文 API 不符），且 "If you don't want **all** widgets to be shown" 丢 all。
- 结论：短章但 P0 一条（Meson 建议整段反转）；make_window_and_run 生命周期段（块 4）整段缺译。

## 各章结论（每章一行）

（随审随填）
