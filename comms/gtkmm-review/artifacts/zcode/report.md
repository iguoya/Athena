# T-101 审查报告：gtkmm 前十章译文忠实度与术语

- 审查人：zcode · 2026-10-17
- 范围：课表 order 1–10（introduction、installation、basics、changes-gtkmm3、changes-gtkmm4、button、range、misc、container、listmodel），共 560 块、约 460 个文字段，全部逐块读过（英中对照底稿在 `comms/gtkmm-review/artifacts/zcode/dump/01..10-*.txt`）。
- 基准：根 AGENTS.md「跨应用教学规范」、guide/gtkmm/AGENTS.md、应用 ADR 0002/0003/0004/0005/0007、upstream pinned b89295e（4.14.0，已克隆对照 DocBook 源）、`guide/gtkmm/scripts/check.py`（只读运行，全绿）。

## 总体结论

前十章译文分两档：**listmodel 章（新译）质量良好**，basics/introduction 大体忠实但有旧版残留；**changes 两章、range、misc/entry、container 的相当一部分段落是「重写」而非「翻译」**——存在三处整段替换/技术含义译反的 P0，若干信号名、API 名、参数方向写错的 P1。术语层面 **widget 一词全书四种译法（部件/控件/小部件/组件）且章内混用**，packing 三种译法同页并存。另有两个系统性工程问题：① `sync_upstream.py` 提取时把正文里转义的尖括号内容（`&lt;...&gt;`）当 XML 标签剥掉，全书 31 段快照英文已损坏（前 10 章确证 2 处），译文无从忠实；② zh 译文系统性丢失原文链接（前端 renderInline 明确支持 markdown 链接，丢失即丢信息）。changes-gtkmm3/4 标 pending 名副其实（各缺 1/7 段），misc/container/listmodel 章标 pending 但页级 translated 与 check 口径自洽——缺的几乎全是 heading/figure，而 check 只把 para/listitem 当文字段（check.py:225），与 AGENTS.md「translated 要求全部文字段有 zh」的表述存在口径分歧，需 leader 裁决（见结构建议）。

## 发现（按严重度）

### P0（误导学习者，3 条）

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| P0-1 | `content/chapters/changes-gtkmm4/sec-deprecations-4-10.json` 块 0 | EN: "does make several changes (both small and large ones) that were **not possible while maintaining binary compatibility**" → ZH: 「虽然有些变更**但是保持了二进制兼容**」。技术含义整句译反：gtkmm-4.0 正是**破坏**二进制兼容才换 API 名、并行安装；译文断言相反事实 | 改为「也做了若干大小改动——这些改动在保持二进制兼容的前提下是无法完成的」 |
| P0-2 | `content/chapters/chapter-misc-widgets/sec-text-entry.json` 块 4 | EN 讲「把键盘焦点移到别的控件也可能表示输入完毕；`Gtk::EventControllerFocus` 的 **leave 信号**可通知；ComboBox with an Entry 一节有示例」→ ZH 只剩「**在控件内移动光标不会发出这两个信号。**」整段机制被替换为原文没有的断言，leave 信号教学点与章节指引全丢 | 按原文补译焦点离开/leave 信号两句与示例指引 |
| P0-3 | `content/chapters/chapter-range-widgets/sec-scrollbar-widgets.json` 块 0 | EN 整段讲 trough/slider 交互（拖动滑块、点击滑轨步进、按哪个鼠标键决定步幅）→ ZH 完全未译，替换为原文不存在的概括「两者都把控件的『调整』委托给一个 Adjustment，并都会响应 adjust_bounds、change_value 与 move_slider 信号」（三个信号名属实，但这句本身是译者自造的） | 按原文重译 trough/slider 交互段 |

### P1（明显缺陷，13 条）

| # | 位置 | 证据 | 建议改法 |
|---|---|---|---|
| P1-1 | 术语全局 | widget 译法：部件 54 处/控件 26 处/小部件 6 处/组件 1 处，几乎每章内部混用（`sec-widgets-overview.json` 块 0–2 用「控件」、同页块 5/7 用「部件」）；packing 在 `sec-multi-item-containers.json` 同页出现「打包」（块 2）/「装填」（块 7）/「组装」（块 13）；signal handler「信号处理器/信号处理函数」混用；CheckButton 有「复选按钮/多选按钮」两种叫法 | 定主译法（建议 widget=控件、packing=打包/装填择一）写进翻译约定并全书统一；vocab.json 目前是生词标注表，可增设「翻译约定」节 |
| P1-2 | `chapter-button-widget/sec-pushbuttons.json` 块 10 | "emitted when the button is pressed **and** released" → 「当按下**或**释放按钮时将会发出该信号」。clicked 是完整点击（按下并释放）才发，按「或」理解一次点击会发两次——与本应用「预测–运行」主原型直接冲突 | 改「按下并释放」 |
| P1-3 | `sec-toggle-buttons.json` 块 1 | "it causes the **clicked** signal to be emitted. This is usually what you want." → 「控件会发出 **toggled 信号**」。信号名张冠李戴，且丢末句 | 改回 clicked 并补末句 |
| P1-4 | `sec-radio-buttons.json` 块 4 | "by using set_group() to tell the other CheckButtons…" → ZH 增译「通过 **get_group() 来得到这个组**，然后…」。原文无 get_group()，系 gtkmm3 旧示例残留写法 | 删增译 |
| P1-5 | `chapter-misc-widgets/sec-text-entry.json` 块 17 | "which of your model **columns** should be used" → 「指定该模型的**那一行**」。行/列颠倒，直接误导 ListModel 学习 | 改「列」 |
| P1-6 | `chapter-misc-widgets/sec-spinbutton.json` 块 7、9 | 原文只写 mouse button 2/3；ZH 增译括号注「键2(通常是**右键**)」「键3(通常是**中键**)」——X11 惯例 2=中键、3=右键，两条注解正好注反 | 删注或改为 2=中键、3=右键 |
| P1-7 | `chapter-installation/sec-installation-dependencies.json` 块 2 | DocBook 205 行原文 `<application>gtk4</application>`（快照 EN 同）→ ZH「**gtkmm4**」。依赖包名写错（该依赖是 GTK4 C 库） | 改回 gtk4 |
| P1-8 | `sec-install-unix-and-linux.json` 块 5 | "can be downloaded from [https://download.gnome.org/…]" → ZH「可以从 **中** 下载 gtkmm 的源代码」——链接全丢成残句。同类：changes-gtkmm4 块 2（丢 glibmm reference 句）、块 30/31（丢 wiki/迁移指南链接）；renderInline 支持 `[文字](url)` 语法，译文可带链接 | 补 markdown 链接；建立「译文保留链接」约定 |
| P1-9 | 提取 bug（内容工程） | DocBook 825–826 行 `sigc::slot&lt;R(Args...)&gt;`、1280 行 `&lt;b&gt;bold text&lt;/b&gt;`，快照 EN 分别只剩 "sigc::slot" 与 "bold text and strikethrough text"（`changes-gtkmm4` 块 19、`sec-labels.json` 块 3），模板参数/Pango 标签全被剥掉。根因：`extract_source.py` `strip_tags()` 在 XML 解析（实体已还原成 `<`）之后跑 `<[^>]+>` 剥标签正则，还原出的尖括号内容被当标签吞掉。全书正文含尖括号实体的段落共 31 段 | 修 strip_tags（对解析后文本先重新转义 `&lt;`/`&gt;` 再剥标签，或改走 XML 序列化 API），修后重跑 sync 并复核受影响段指纹 |
| P1-10 | `chapter-basics/sec-helloworld.json` 块 17 | "make_window_and_run() will return, causing our main() function to return" → 「**run() 函数将返回**，导致 main() 函数的**最后一行将被执行**」。函数名错 + 增译，gtkmm3 译文残留 | 按原文改 make_window_and_run() 并删增译 |
| P1-11 | `changes-gtkmm3/changes-gtkmm3.json` 块 19 | "ensure that your application builds with the deprecated … API disabled" → ZH 增「**然后删除他们**」。原文无「删除 API」步骤，误导迁移操作 | 删增译，改为「确保在禁用弃用 API 的宏下能编译通过」 |
| P1-12 | `chapter-container-widgets/sec-multi-item-containers.json` 块 22 | "invisible containers **into which we can pack our widgets**" → 「这些都是不可见容器**我们可以将容器装入其中**」。装填方向译反（应是把部件装进盒） | 改「我们可以把部件装进这些不可见容器」 |
| P1-13 | `sec-multi-item-containers.json` 块 40 | EN 两种方案之二含 "Connect a signal handler to the **command_line signal**, and handle the command-line options in the signal handler." 整句漏译——不接该信号 HANDLES_COMMAND_LINE 方案不工作 | 补译该句 |

另有一处与 P0-1 同模式但情节较轻：`changes-gtkmm3.json` 块 0 把 "changes that were not possible while maintaining binary compatibility" 译成「这些变动导致无法做到令他们保持二进制兼容」（因果倒置，「于」应为「与」），该页 status=pending，修 P0-1 时一并照改。

### P2（可改进，择要 10 条）

| # | 位置 | 问题 |
|---|---|---|
| P2-1 | `sec-gtkmm.json` 块 2/8、`sec-install-unix-and-linux.json` 块 0/4 | heading 的 zh 被填成相邻 para 的旧版译文（错位填充，共 4 处）。UI 不渲染 heading zh、PO 单元不含 heading，影响限数据层；建议清空或换正确标题译文 |
| P2-2 | `sec-basics-simple-example.json` 块 13 | 残句「当窗口被关闭。」；"arguments, passed to your application on the command line" 主宾颠倒成「参数会将命令行传递给你的应用程序」 |
| P2-3 | `sec-headers-and-linking.json` 块 1 | "(properly installed)" 误译「(也许已经安装的)」 |
| P2-4 | `sec-basics-ustring.json` 块 5/7 | 「与含为 ASCII 的」残句错字；"UTF-8 string literals" 译成「UTF-8 字符」（丢「字面量」，指向国际化章的原意偏了） |
| P2-5 | `sec-basics-gobj-and-wrap.json` 块 7 | 「C**示例**拥有一个浮动引用」——instance 误写「示例」 |
| P2-6 | `sec-helloworld.json` 块 0/14/16 | 「已经可以自己所学的知识」缺「用」；"without comments" 译「没有注释过的 main() 函数」；"must have one" 译「都有」 |
| P2-7 | `sec-infobar.json` 块 0 | "small items of information" 译「小物品」 |
| P2-8 | `sec-listmodel-datamodel.json` 块 0 | 漏译后半句 "generally scale fine to thousands of items"（可扩展到数千条目） |
| P2-9 | `sec-labels.json` 块 6 | 章节链接译成「(框架部件的教程: 框架(Frame)部件)」的怪格式；`sec-scale-widgets.json` 块 5 trough（滑轨）译成「滑块」 |
| P2-10 | 杂项错字 | 「我们**想**其他的…一样」(sec-gtkmm 块 12)、「强行的**是**」(sec-toggle-buttons 块 2)、「示例程序**连接**」(sec-multi-item-containers 块 86)、「跳到 upper 或 lower **values**」英文残留 (sec-spinbutton 块 9) |

## 各章结论（每章一行）

1. **introduction**（translated）：可读；heading 错位填充 2 处、「GTK 写成 GTK+」、控件/部件混用起点、错字若干——无 P0/P1 级语义错误。
2. **installation**（translated）：P1 两处（gtk4→gtkmm4、下载链接丢成残句），heading 错位 2 处，漏译 Meson（块 9）；其余平实。
3. **basics**（translated）：P1 一处（helloworld 块 17 的 run() 残留）；残句、properly installed 误译各一；同页术语混用在此章最直观。
4. **changes-gtkmm3**（页 pending）：20 段缺 1 para；已译 19 段含因果倒置与「然后删除他们」增译——完成度高但需先修再转 translated。
5. **changes-gtkmm4**（页 pending）：36 段缺 7 para（含 4.10 弃用类长清单 2 段）；已译部分除 P0-1 与快照损坏的 sigc::slot 条外质量尚可；P0-1 必须先修。
6. **button**（translated）：P1 三处（clicked 时序、clicked→toggled、get_group 增译），信号语义错误集中在这一章，与本应用预测–运行主原型正面冲突，优先修。
7. **range**（translated）：P0-1 处（scrollbar 首段整段替换）；scale 页丢例句、trough 术语错；本章是前十章质量最差的一章。
8. **misc**（章 pending、页 translated）：P0 一处（entry leave 信号段替换）、P1 两处（行/列颠倒、鼠标键注反）；12 个缺失 zh 全为 heading/figure。
9. **container**（章 pending、页 translated）：P1 三处（装填方向反、command_line 漏句、行/列设置语义错）；packing 三译法同页混用；137 块中 13 缺全为 heading/figure，para 层已全译。
10. **listmodel**（章 pending、页 translated）：前十章质量最好，仅 1 处漏半句（P2-8）；9 缺全为 heading/figure。

## translated/pending 状态与实际译完度（任务书第 4 条）

- **changes-gtkmm3**：页 pending 属实——缺 1 para（块 17）。补齐该段即可达 check 口径，但建议先修块 0/19 两处再转。
- **changes-gtkmm4**：页 pending 属实——缺 7 para（块 4/5/18/32/33/34/35，其中 33/34 是 4.10 弃用/新增类长清单，是否逐类翻译可由 leader 定夺）。P0-1 在已译段里，修复与补译可并行。
- **misc/container/listmodel**：章 pending、页全 translated 与 check 口径自洽——para/listitem 已全译，缺的全是 heading/figure。章级 pending 是人工总闸，实际完成度（para 层）≈100%；章状态何时翻转取决于 leader 对 heading 是否算译文义务的裁决。
- check.py:225 只把 `para`/`listitem` 计入「文字段」，`heading`/`figure` 不校验；前端 heading/figure 恒渲染英文原文（`page-view.tsx:832-838、874-881`，不读 zh）。三处（AGENTS.md 表述 / check 口径 / 前端行为）现状不一致但未造成用户可见错误。

## 结构建议（由 leader 裁决，本报告不自行改动）

1. **裁决 heading/figure 的译文义务**：若维持前端「标题恒英文」的设计，把「heading/figure 不要求 zh」写进 guide/gtkmm/AGENTS.md，check 口径即名正言顺，heading 里 4 处错位 zh 顺手清掉；若要中英混排标题，则前端与 check 同步扩口径。
2. **修 sync_upstream 提取 bug（P1-9）**：影响全书 31 段快照英文，修复后重跑 sync、复核受影响段指纹与译文。
3. **建术语基准**：widget/packing/signal handler 等主译法一表定死（可挂 vocab.json 或独立翻译约定文件），后续翻译与返修按表执行。
4. **译文链接约定**：zh 中以 markdown 链接保留原文外链（renderInline 已支持），杜绝「可以从 中下载」式残句。

## 证据与工具

- 英中对照底稿：`comms/gtkmm-review/artifacts/zcode/dump/01-chapter-introduction.txt` … `10-chapter-listmodel.txt`
- 统计脚本：`_survey.py`（各页块数/缺失/stale）、`_terms.py`（术语分布、heading 错位）；`guide/gtkmm/scripts/check.py` 只读运行全绿（203 JSON 解析通过、课表校验通过）
- 上游对照：upstream.json pinned b89295e（4.14.0）DocBook 源已临时克隆核对（Sigc 条目 825–826 行、Label 1280 行、gtk4 205 行），克隆已删
