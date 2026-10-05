# ADR 0002：内容基准是官方教程全量翻译，参考资料分三层认定

- 日期：2026-10-06
- 状态：已接受；内容工程按此搭建
- 延续：主仓库 ADR 0043（内容必须有出处）、0054（宁增勿删）、0028（大纲/教学过程/实验三层）

## 背景

本应用的内容基准经过明确选定：以 GNOME 官方教程
《Programming with gtkmm 4》（https://gnome.pages.gitlab.gnome.org/gtkmm-documentation/，
下称「官方教程」）为**编排基准**，按其章节结构组织中文课程，而不是自创大纲再
到处凑资料——这直接回应「文档与实验分离、来源杂乱」的原始痛点。

翻译合规已查证：官方教程采用 **GFDL 1.2 或更高版本，无不变章节（Invariant
Sections）、无前/后封面文本**，版权 © 2002–2010 Murray Cumming。GFDL 明确允许
复制、修改、翻译与再发行。

gtkmm 的 API 文档对行为细节经常只写「见 C 文档」，gtkmm 自身文档不构成完整
语义权威；同时 GTK4 生态有两套官方演示源码可作参照。

## 决策

1. **编排基准：官方教程全量翻译 + 分层呈现。**
   - 32 章 + 8 附录**全量翻译**，不跳章；
   - 教学主线按学习路径编排：版本迁移内容（「Changes in gtkmm 3」「Changes in
     gtkmm-4.0 and glibmm-2.68」）、贡献指南（「Contributing」）与附录 F/G
     （源码工作、gmmproc 封装）归入应用内**参考层**，完整呈现但不作为学习
     路径节点——从第一天就分层，无删除（主仓库 ADR 0054）；
   - 主线各节挂 `translation_ref`（教程章/节/URL），可回溯原文。

2. **语义基准：`docs.gtk.org/gtk4`（GTK4 C API 文档）是行为争议的最终权威。**
   gtkmm 是 C API 的包装，文档与代码、模拟与真实行为不一致时，以 C 文档与
   GTK 源码的语义为准。出处引用（主仓库 ADR 0043）优先指向
   `docs.gtk.org` 与官方教程章节；glibmm / GtkSourceView 等配套库同理指向
   各自的官方文档。

3. **参考层：两套官方演示源码引入应用内「参考」部分。**
   - `gtk4-demo`（GTK 源码树 `demos/gtk-demo/`，C 语言）：行为与形态参照；
   - **gtkmm-demo**（GNOME/gtkmm 仓库 `demos/gtk-demo/`，官方 C++ 移植，
     24+ 示例：appwindow、builder、dialog、drawingarea、dropdown、flowbox、
     gestures、glarea、gridview、headerbar、iconbrowser、images、ListView/
     ColumnView 系列、overlay、panes、pixbufs、shortcuts 等）：本应用演示与
     实验的首选参照源，随 gtkmm 库同为 LGPL 许可，引用时保留版权与许可声明；
   - gtkmm-documentation 仓库自带的 `examples/`（教程各节示例）随章节对应引用。
   - 其他渠道（书籍、第三方教程、博客）不进基准层，可在文档中提及但不作为
     出处引用目标。

4. **GFDL 义务落地**：应用内置声明页，包含 GFDL 许可证全文、原文出处
   （教程名、原作者、官方 URL）与修改标注（中文翻译及增补）。

5. **观察题出处**：演示观察题的出处是清单中的演示条目本身（`demos.json`
   `id`），题面引用演示行为；其余判分题出处按第 2 条指向语义基准或教程章节。

## 后果

- 内容工程有唯一编排骨架，翻译进度与课程进度是同一件事，不出现「自创大纲
  与官方教程两套结构对照维护」的成本。
- 义务清单固定三项（许可全文、出处标注、修改标注），随声明页一次性落地。
- 参考层的演示源码是「官方质量基准」：本应用的演示与实验若与 gtkmm-demo
  行为不一致，按参考层修正自己的代码，不改参考。
