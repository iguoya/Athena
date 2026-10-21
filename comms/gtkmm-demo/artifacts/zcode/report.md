# T-101 审查报告：参考层八章译文忠实度与缺译（chapter-wrapping-c-libraries 未审，附录 G 归 T-003）

- 审查人：zcode · 2026-10-21
- 范围：`curriculum.json` reference[] 中 status=pending 的 8 项里任务书指定的 7 章
  （chapter-refptr、chapter-signals、sec-signals-comparison、sec-windows-installation、
  chapter-working-with-source、chapter-contributing、chapter-custom-signals），
  共 14 节文件、96 个文字段（para + listitem），全部逐段英中对照读过
  （底稿 `/tmp` 已删，产出即本报告与 ref-fix.json）。
- 基准：`content/glossary.json`（widget=部件、signal handler=信号处理函数、
  top-level=顶级 等 8 条主译法）；`content/po-units/` 对照（注意：PO 是 gtkmm3
  时代镜像，sec-eventsignals 的 PO 译文整节对应旧 X 事件 API，msgid 全空，
  只能作历史参照不能照抄）；上游 pinned b89295e 的英文原文（blocks[].text）。
- 产出：`artifacts/zcode/ref-fix.json`——14 节 49 段草稿译文，覆盖全部 20 个缺译段、
  全部审出的合并/错位块，以及全部 P0 与大部分 P1 的修正译文；leader 合并时对
  P1/P2 可自取。**未改 `guide/gtkmm/` 任何文件。**

## 总体结论

参考层旧 PO 译文的底子比 gtkmm-review 报告里的正文层好——多数段落忠实可读。
问题集中在三处：① **sec-eventsignals 整节停留在 gtkmm3 的 X 事件 API 时代**
（button_press_event 在 gtkmm4 已移除，现行为 EventController/Gesture），现有
译文与上游重写后的原文完全脱节，是本批唯一的成片 P0 区；② **旧 PO 合并译文**
至少 5 处（多处还互相复写，同一句译文出现在两个块里），且拆分后暴露出
「最后一个或倒数第二个 throw」被译成「最后一个或第一个」这类方向性误译；
③ 散见错别字与术语违规（「膜拜参数」「啊运行你」「处理程序」「处于效率考虑」）。
缺译 20 段全部补齐。

## 发现（按严重度）

### P0（误导学习者，7 条）

| # | 位置 | 证据 | 处置 |
|---|---|---|---|
| P0-1 | `chapter-signals/sec-eventsignals.json` 块 1 | EN（gtkmm4）：用 `Gtk::EventController` 子类（`Gtk::GestureClick::signal_pressed()` 等）处理事件 → ZH 整段是 gtkmm3 旧文：「button_press_event 信号会发送坐标」「X 事件也用于处理按键」。button_press_event 在 gtkmm4 已不存在，读者照做必失败 | ref-fix 重译 |
| P0-2 | `sec-eventsignals.json` 块 3 | 同上模式：EN 用 `Gtk::GestureClick::signal_pressed()` → ZH「如果你处理 Gtk::Button 的 button_press_event 信号」 | ref-fix 重译 |
| P0-3 | `chapter-signals/sec-exceptions-in-signal-handlers.json` 块 9 | EN "And here's an excerpt from a `gdb` session." → ZH「**使用git版本的gtkmm**」——译文与原文完全无关（他处残留），下文读者找不到对应的 gdb 会话 | ref-fix 补译 |
| P0-4 | `chapter-signals/sec-connecting-signal-handlers.json` 块 3 | EN "First let's identify the **parties involved**:"（后文列的正是 handler 与 button 两方）→ ZH「首先让我们确定**代码的行为**」。指鹿为马，下面三条列表失去铺垫 | ref-fix 重译 |
| P0-5 | `chapter-signals/sec-writing-signal-handlers.json` 块 2 | EN "the **template arguments** are important" → ZH「这里的**膜拜参数**很重要」。template 误成「膜拜」，教学点（模板参数即返回值+参数类型）全部失效 | ref-fix 重译 |
| P0-6 | `sec-signals-comparison/sec-signals-comparison.json` 块 1 | EN "allows you to connect a callback" → ZH「gtk 的 C 代码**啊运行你**连接到……」（「允许你」之误），整句不可读 | ref-fix 重译 |
| P0-7 | `chapter-contributing/chapter-contributing.json` 块 2 | EN（2024 版）贡献走 GitLab issue/MR + Discourse → ZH「请将你的贡献发送到 gtkmm **邮件列表，网址为，**」——上游已删邮件列表改 GitLab，译文不但过时还留下「网址为，」的空壳残句；Discourse 一句整丢 | ref-fix 重译 |

### P1（明显缺陷，17 条）

| # | 位置 | 证据 | 处置 |
|---|---|---|---|
| P1-1 | `sec-connecting-signal-handlers.json` 块 0 | ①「信号的处理**程序**」违反 glossary（avoid：信号处理程序）；②「所使用**的的**libsigc++」叠字 | ref-fix 重译 |
| P1-2 | `sec-binding-extra-arguments.json` 块 0（合并块） | 块 0 的 zh 塞了块 0/2/4 三段，且丢 helloworld2 链接；「**那个**按钮被点击了」应为「**哪个**按钮」（which） | ref-fix 拆分三段 |
| P1-3 | `sec-binding-extra-arguments.json` 块 5 | EN "This is generally **overused** in GTK to pass information that **should be stored as member data**"（GTK 里这种 hack 常被滥用）→ ZH「通过……传递……数据**可以有效降低代码复杂度**」——评价方向译反；"far less need" 译成「不再需要」也过了 | ref-fix 重译；旧译者的「（译注：lambda 更好）」非原文内容，忠实版移除（信息本身有价值，是否保留译注体例请 leader 定） |
| P1-4 | `sec-exceptions-in-signal-handlers.json` 块 4+6、块 9+11、块 14+16 三组合并 | 旧 PO 把相邻两段合并翻译并互相复写：块 4 与块 6 的 zh 完全相同、块 11 开头挂着块 9 的「这是gdb会话的摘录：」、块 14 与块 16 的 zh 完全相同；且块 16 的「最后一个或**第一个** throw」是 EN「last (or possibly the last but one)」（最后一个或倒数第二个）的方向性误译 | ref-fix 全部拆分重译 |
| P1-5 | `sec-exceptions-in-signal-handlers.json` 块 1 | 「本小节**组要**介绍」（主要） | ref-fix 修正 |
| P1-6 | `chapter-refptr/sec-refptr-constness.json` 块 2 | 「是**处于**效率考虑」（出于） | ref-fix 修正 |
| P1-7 | `chapter-refptr/sec-refptr-copying.json` 块 0 | EN "But unlike normal pointers, you don't need to worry about…" → ZH「你不需要担心删除底层实例」丢掉「但与普通指针不同」的转折——本句的教学点正是 RefPtr 与裸指针的差异 | ref-fix 修正 |
| P1-8 | `sec-eventsignals.json` 块 2 | EN "Some **event controller** signals behave **slightly** differently" → ZH「这些信号的行为有所不同」丢「事件控制器」主语与「略」；「则不再传播信号不再调用」缺标点 | ref-fix 重译 |
| P1-9 | `sec-eventsignals.json` 块 6 | 「当**鼠标悬停在鼠标**上方」（按钮） | ref-fix 修正 |
| P1-10 | `sec-eventsignals.json` 块 9 | EN "To specify that your handler should be called **before** the other handlers…This connect() parameter is optional, **if the signal handler returns void**" → ZH「这样你的信号处理函数就**总是会被调用**」——before 语义丢失；「仅当返回 void 时参数可选」整句丢失 | ref-fix 重译 |
| P1-11 | `chapter-signals/sec-overriding-default-signal-handlers.json` 块 6 | 「然后调用Gtk::Button**已被覆写本该被调用的**成员函数」杂糅难读 | ref-fix 重译 |
| P1-12 | `chapter-signals/sec-writing-signal-handlers.json` 块 3 | 「对于接受期望调用的函数有更多参数的信号也是一样的阅读规则」不通顺，且 EN "Here's one with **three** (taken from…)" 的「三参数示例」信息丢失 | ref-fix 重译 |
| P1-13 | `sec-windows-installation.json` 块 1 | EN 更新至 2024-12（「只含 gtkmm2 安装器」）→ ZH 停在「撰写本章时（2020年10月）已经很久没人维护（译注：朋友，MSYS2了解一下）」：内容过时 + 口语译注 | ref-fix 重译 |
| P1-14 | `sec-windows-installation.json` 块 7 | 「**WIndwos**」错拼；EN 两个链接（README.win32.md 与 MSVC_NMake/README）被混译成「README.win32以及此自述文件」 | ref-fix 重译（两个 URL 均保留） |
| P1-15 | `chapter-working-with-source/sec-installing-jhbuild.json` 块 4、6 | 块 4「之后**他**只会重新编译自上次构建依赖变更过的文件」（他/它 + 语序缠绕）；块 6「要返回之前的环境你只需要 jhbuild shell 即可」——**丢了动词 exit**，读者不知道该做什么 | ref-fix 重译 |
| P1-16 | `sec-setting-up-jhbuild.json` 块 7 | EN "keep this prefix different from **other software that you've installed**" → ZH「建议你选择的新前缀与**旧前缀**保持不同」——比较对象译错（应与其他软件的安装位置区分） | ref-fix 修正 |
| P1-17 | `chapter-contributing/chapter-contributing.json` 块 1 | 「我们希望你前往**此仓库**……提供MR」——EN 的 merge request 链接丢失，「此仓库」指代不明 | ref-fix 修正（文字版；markdown 链接可由 leader 合并时恢复） |

### P2（可改进，10 条，未入 ref-fix，报告存档）

1. refptr 章内「正常指针/普通指针」混用（casting[0] vs casting[2]/copying[0]），建议统一「普通指针」。
2. casting[2]「也能接受 const Glib::RefPtr<DerivedType>& **对象**」——接受的是引用，加「对象」二字轻微失真。
3. checking-for-null[2]「不需要你自己进行置空」可作「无需自己记得去做」。
4. dereferencing[0]「就像使用普通指针访问底层实例的方法一样」语序可顺。
5. connecting[12]「在**动作**中使用槽」（in action = 实际运用）。
6. connecting[16] EN "This is perfectly fine" 的评价语气译成了「所以」。
7. connecting[17] EN "We just told you that…" → ZH「你应该已经注意到了」——转述者变了。
8. disconnecting[2] 增译「若你想如此做，只需……即可」（无害）。
9. comparison[0] 丢尾注「- sort of. More on this later.」（算是吧，稍后详述）。
10. exceptions[0]「困难的**多**」应为「得多」；custom-signals[0]「定义了并使用了」生硬；overriding[0]/[1]/[2]/[7] 若干口语化/语气偏差。

## 缺译清单（20 段，全部已译入 ref-fix.json）

- refptr 3：sec-refptr-constness[0,1]、sec-refptr-dereferencing[2]
- signals 11：sec-binding-extra-arguments[2,4]、sec-connecting-signal-handlers[11,15]、
  sec-eventsignals[0,7,11] + listitem[12,13,14]、sec-eventsignals[15]
- windows-installation 5：sec-windows-installation[2] + listitem[3,4,5,6]
- working-with-source 1：sec-setting-up-jhbuild[8]

## 合并/错位清单（ref-fix 覆盖）

- sec-binding-extra-arguments[0]（合并 0/2/4）
- sec-exceptions-in-signal-handlers[4]+[6]、[9]+[11]、[14]+[16]（三组合并复写）

## 需要 leader 裁决

1. **译注体例**：旧 PO 译者插话（binding[5] 的 lambda 译注、windows[1] 的「MSYS2 了解一下」）
   忠实版一律移除；若应用允许「译注」体例，建议定格式（如「【译注】…」）并只保留有信息量的。
2. **链接形态**：本批译文链接写成「文字（URL）」纯文本（如 windows[3-7]、eventsignals[15]）；
   gtkmm-review 报告确认前端 renderInline 支持 `[文字](url)`，合并时是否统一转成 markdown 链接请定。
3. chapter-wrapping-c-libraries（第 8 项 pending）不在本任务书名单，未审。
