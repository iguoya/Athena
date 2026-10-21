# 历史归档：未收录的条目（practice/c-gui-lab）

来源是旧 GitHub 仓库 `Linux`（`GTK/`、`SDL/`）（ADR 0176）。以下内容**没有**进归档窗口；旧仓库只会被设为 archived，历史完整保留，需要时从那里取回。清单与证据见 `comms/legacy-archive/artifacts/cursor/manifest-gtk.md`。

| 旧路径 | 原因 |
|---|---|
| `Linux/GTK/` 下约 575 个生成物文件、47 个单元 | Anjuta/Glade 向导生成的 autotools 样板（`configure`、`Makefile.in`、`ltmain.sh`、`po/` 等）与 IDE 工程文件 |
| `Linux/GTK` 的 17 个候选里的 11 个：`10-HBoxAndVBox`、`g28-pack`、`04-GtkBox`、`02-CSS`、`01-Hello`、`g23-hello`、`28-GtkLayout`、`18-Message`、`g29-grid`、`24-Glade`、`g30-app`、`g34-dialog`、`g36-multiwindow`、`g17-anjuta` | 与同目录其他向导工程同构，批注反复落在同几条上（`gtk_widget_show_all`、`gtk_main`、`gtk_container_set_border_width` 在 GTK4 的变化，Glade 文件相对路径），写不出 3 条以上**不重复**且经核对的实质批注 |
| `Linux/SDL/1-backgound` | Code::Blocks 的 SDL 模板原样，不是自写 |
| `Linux/SDL/3-line` | Anjuta 生成的 autotools 骨架，源码只剩一个 `main.c` |
| `Linux/GTK/GtkApp`（193 个文件）| 绝大多数是 Anjuta 工程生成物，手写源码 15 个文件左右，内容与 `GtkApp3` 同类，收了 `GtkApp3` |
| `Linux/Thread/01-Thread`（GTK 线程与界面更新示例） | 几乎整个文件是被注释掉的 GTK 线程示例 |
| `Linux/GTKMM/**` | 归 `programming/gtkmm-lab` |
