# ADR 0004：领域核心编译为 athena-core 静态库，与 GTK 解耦

- 日期：2026-08-14（2026-08-15 补记）
- 状态：已接受
- 依据提交：`229dbe3` 拆分章节目录与演示注册表、`5f82add` 复用静态库、
  `d46e372` 核心测试

## 背景

章节目录、函数注册、内容加载与 Markdown 转换最初与窗口代码耦合，只能通过
启动 GTK 界面间接验证，测试慢且定位困难。

## 决策

- `registry/`、`content/`、`render/` 的非平台部分编译为内部 `athena-core`
  静态库，不依赖 gtkmm。
- 窗口协调层（`mainwindow.cc`）与平台 ArticleView 后端在其之上。
- 核心逻辑一律使用不链接 GTK 的 Google Test 验证。

## 后果

- 核心测试快速、可移植；未来可增加只测核心的 Linux CI 任务。
- 新代码先问"能不能进 athena-core"，凡是依赖 GTK 控件的逻辑不得下沉。
