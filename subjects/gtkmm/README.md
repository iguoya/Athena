# gtkmm 官方教程精读

跟随 [GTK 官方 gtkmm 教程](https://developer.gnome.org/documentation/books/programming-with-gtkmm-4.html)
的中文精读应用：逐段对照官方原文与译文阅读，章节测验自检，并把可复核的翻译整理成
能反哺上游 GNOME 贡献通道的标准 PO 文件。

- 内容基准：官方 DocBook 原文按段落快照入库，译文以 GNOME 官方 `zh_CN.po`
  （Damned Lies）为准，缺失段落走自译；取舍见 `docs/decisions/`。
- 附加能力：英译训练模式（隐藏译文逐段揭示）、C++ 语法高亮、`workspace/`
  学习者工作集（骨架实验的个人副本，不入库）。
- 启动：`launcher open gtkmm`（`app.json` 声明，Tauri 2 + React）。
- 验证：`python scripts/check.py`（内容契约、PO 对齐审计、GNU msgfmt 校验、
  前端构建、Rust 检查；原生演示的构建需要本机 GTK 工具链，规则见 `AGENTS.md`）。
