# GTK 领域清单摘要（T-102）

- 生成：2026-10-21T15:48:44
- 目标：`practice/c-gui-lab`（现有，GTK4 画廊；旧代码多为 GTK2/3 → 建议 read-only/toolchain）
- 范围：`Linux/GTK/`
- 本机 Windows **未安装** GTK 开发库，未尝试编译（任务书要求）

## 统计

| 项 | 数量 |
|---|---:|
| 单元 | 127 |
| keep | 80 |
| drop-third-party | 0 |
| drop-junk | 47 |
| 生成物文件（drop-junk 桶内） | 575 |
| scoped 文件 | 1635 |
| 覆盖遗漏 | 0 |

### keep 版本分布（静态判断）

| version | n |
|---|---:|
| `gtk3` | 49 |
| `gtk2-or-3` | 17 |
| `unknown` | 9 |
| `gtk2` | 5 |

### topic_hint

| hint | n |
|---|---:|
| `archive.gtk.other` | 32 |
| `archive.gtk.glade` | 12 |
| `archive.gtk.basics` | 11 |
| `archive.gtk.layout-box` | 10 |
| `archive.gtk.scaffold` | 5 |
| `archive.gtk.layout-grid` | 4 |
| `archive.gtk.multiwindow` | 3 |
| `archive.gtk.app` | 2 |
| `archive.gtk.dialog` | 1 |

## keep 一览

- `gtk-gtkapp` — GtkApp ← `Linux/GTK/GtkApp` ver=gtk2 run=read-only files=193 first=2023-01-28
  - main.c 使用 GtkApplication（GTK3+）；静态判断工具链版本≈gtk3；手写源码少（非样板 15 / src 16）
- `gtk-gtkapp3` — GtkApp3 ← `Linux/GTK/GtkApp3` ver=gtk2 run=read-only files=29 first=2023-01-28
  - 静态判断工具链版本≈gtk2；手写源码少（非样板 11 / src 12）
- `gtk-01-hello` — 01-Hello ← `Linux/GTK/01-Hello` ver=gtk3 run=toolchain files=5 first=2023-01-28
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 0 / src 1）
- `gtk-01-hellogtk` — 01-HelloGTK ← `Linux/GTK/01-HelloGTK` ver=gtk2-or-3 run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-12-compile-hello` — 12-compile_hello ← `Linux/GTK/12-compile_hello` ver=unknown run=toolchain files=8 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 2）
- `gtk-20-simplegtk` — 20-simplegtk ← `Linux/GTK/20-simplegtk` ver=gtk3 run=toolchain files=16 first=2022-07-14
  - 静态判断工具链版本≈gtk3；main.c: 旧式 gtk_main 循环；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-21-gtkhello` — 21-GTKHello ← `Linux/GTK/21-GTKHello` ver=gtk3 run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 0 / src 1）
- `gtk-27-hello-c` — 27-Hello.c ← `Linux/GTK/27-Hello.c` ver=gtk3 run=toolchain files=1 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 1 / src 1）
- `gtk-g01-helloworld` — G01-HelloWorld ← `Linux/GTK/G01-HelloWorld` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g18-hello` — g18-hello ← `Linux/GTK/g18-hello` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；main.c: 旧式 gtk_main 循环；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-g19-basicwindow` — g19-basicwindow ← `Linux/GTK/g19-basicwindow` ver=gtk3 run=toolchain files=17 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g19-basicwindow.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g23-hello` — g23-hello ← `Linux/GTK/g23-hello` ver=gtk3 run=toolchain files=16 first=2022-07-14
  - 静态判断工具链版本≈gtk3；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-g24-hello` — g24-hello ← `Linux/GTK/g24-hello` ver=gtk3 run=toolchain files=17 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g24-hello.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g34-dialog` — g34-dialog ← `Linux/GTK/g34-dialog` ver=gtk3 run=toolchain files=19 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g34-dialog.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-04-gtk-glade` — 04-GTK_Glade ← `Linux/GTK/04-GTK_Glade` ver=gtk2-or-3 run=toolchain files=5 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-10-glade` — 10-glade ← `Linux/GTK/10-glade` ver=gtk2-or-3 run=toolchain files=6 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-11-glade` — 11-glade ← `Linux/GTK/11-glade` ver=gtk2-or-3 run=toolchain files=5 first=2022-07-14（dup 1）
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-14-glade-only-window` — 14-glade_only_window ← `Linux/GTK/14-glade_only_window` ver=gtk2-or-3 run=toolchain files=5 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-24-glade` — 24-Glade ← `Linux/GTK/24-Glade` ver=gtk2-or-3 run=toolchain files=5 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-25-glade` — 25-glade ← `Linux/GTK/25-glade` ver=gtk3 run=toolchain files=18 first=2022-07-14
  - 静态判断工具链版本≈gtk3；25-glade.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g10-glade` — G10-Glade ← `Linux/GTK/G10-Glade` ver=gtk3 run=toolchain files=12 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 2 / src 3）
- `gtk-g11-glade` — G11-Glade ← `Linux/GTK/G11-Glade` ver=gtk3 run=toolchain files=12 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 2 / src 3）
- `gtk-g12-glade` — G12-Glade ← `Linux/GTK/G12-Glade` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g14-glade` — G14-Glade ← `Linux/GTK/G14-Glade` ver=gtk3 run=toolchain files=2 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 0 / src 1）
- `gtk-g15-glade` — G15-Glade ← `Linux/GTK/G15-Glade` ver=gtk3 run=toolchain files=12 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 2 / src 3）
- `gtk-g16-glade` — G16-Glade ← `Linux/GTK/G16-Glade` ver=gtk3 run=toolchain files=16 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-04-gtkbox` — 04-GtkBox ← `Linux/GTK/04-GtkBox` ver=gtk2-or-3 run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-10-hboxandvbox` — 10-HBoxAndVBox ← `Linux/GTK/10-HBoxAndVBox` ver=gtk2 run=read-only files=3 first=2022-07-14（dup 3）
  - 静态判断工具链版本≈gtk2；main.c: 偏手工 destroy，缺 g_object_unref 意识；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-17-frame` — 17-Frame ← `Linux/GTK/17-Frame` ver=gtk2-or-3 run=toolchain files=4 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-22-gbox` — 22-GBox ← `Linux/GTK/22-GBox` ver=gtk2-or-3 run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-g20-box` — g20-box ← `Linux/GTK/g20-box` ver=gtk3 run=toolchain files=18 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g20-box.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g21-framework` — g21-framework ← `Linux/GTK/g21-framework` ver=gtk3 run=toolchain files=18 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g21-framework.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g25-box` — g25-box ← `Linux/GTK/g25-box` ver=gtk3 run=toolchain files=14 first=2022-07-14
  - 静态判断工具链版本≈gtk3；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-g26-box` — g26-box ← `Linux/GTK/g26-box` ver=gtk3 run=toolchain files=14 first=2022-07-14
  - 静态判断工具链版本≈gtk3；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-g28-pack` — g28-pack ← `Linux/GTK/g28-pack` ver=gtk3 run=toolchain files=16 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g28-pack.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g31-mixbox` — g31-mixbox ← `Linux/GTK/g31-mixbox` ver=gtk3 run=toolchain files=18 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g31-mixbox.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-15-gtkgrid` — 15-gtkgrid ← `Linux/GTK/15-gtkgrid` ver=gtk2-or-3 run=toolchain files=4 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-g29-grid` — g29-grid ← `Linux/GTK/g29-grid` ver=gtk3 run=toolchain files=17 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g29-grid.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g32-grid` — g32-grid ← `Linux/GTK/g32-grid` ver=gtk3 run=toolchain files=20 first=2022-07-14
  - 静态判断工具链版本≈gtk3；含 Anjuta 工程痕迹；手写源码少（非样板 4 / src 5）
- `gtk-g33-grid1` — g33-grid1 ← `Linux/GTK/g33-grid1` ver=gtk3 run=toolchain files=19 first=2022-07-14
  - 静态判断工具链版本≈gtk3；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g36-multiwindow` — g36-multiwindow ← `Linux/GTK/g36-multiwindow` ver=gtk3 run=toolchain files=21 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g36-multiwindow.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 4 / src 5）
- `gtk-g37-multi-window` — g37-multi_window ← `Linux/GTK/g37-multi_window` ver=gtk3 run=toolchain files=19 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g37-multi_window.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 4 / src 5）
- `gtk-g38-multi-window` — g38-multi_window ← `Linux/GTK/g38-multi_window` ver=gtk3 run=toolchain files=20 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g38-multi_window.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 4 / src 5）
- `gtk-02-css` — 02-CSS ← `Linux/GTK/02-CSS` ver=gtk2-or-3 run=toolchain files=3 first=2023-01-28
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-03-gtk-button` — 03-GTK_Button ← `Linux/GTK/03-GTK_Button` ver=gtk2-or-3 run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-05-point` — 05-Point ← `Linux/GTK/05-Point` ver=unknown run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 1）
- `gtk-06-array` — 06-Array ← `Linux/GTK/06-Array` ver=unknown run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 1）
- `gtk-07-datatype` — 07-DataType ← `Linux/GTK/07-DataType` ver=unknown run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 1）
- `gtk-08-point` — 08-Point ← `Linux/GTK/08-Point` ver=unknown run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 1）
- `gtk-09-struct` — 09-Struct ← `Linux/GTK/09-Struct` ver=unknown run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 1）
- `gtk-1-basic-principle` — 1-basic_principle ← `Linux/GTK/1-basic_principle` ver=unknown run=toolchain files=13 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 3）
- `gtk-12-cmakegtk` — 12-cmakeGTK ← `Linux/GTK/12-cmakeGTK` ver=unknown run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 1）
- `gtk-13-codeblockstest` — 13-CodeBlocksTest ← `Linux/GTK/13-CodeBlocksTest` ver=gtk2 run=read-only files=2 first=2022-07-14
  - 静态判断工具链版本≈gtk2；main.c: 偏手工 destroy，缺 g_object_unref 意识；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-13-memory-layout` — 13-memory_layout ← `Linux/GTK/13-memory_layout` ver=unknown run=toolchain files=5 first=2022-07-14
  - 静态判断工具链版本≈unknown；手写源码少（非样板 0 / src 1）
- `gtk-16-window` — 16-window ← `Linux/GTK/16-window` ver=gtk3 run=toolchain files=4 first=2022-07-14
  - 静态判断工具链版本≈gtk3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-18-message` — 18-Message ← `Linux/GTK/18-Message` ver=gtk2-or-3 run=toolchain files=5 first=2022-07-14（dup 1）
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-23-callback` — 23-CallBack ← `Linux/GTK/23-CallBack` ver=gtk2-or-3 run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-26-gtk4-c` — 26-Gtk4.c ← `Linux/GTK/26-Gtk4.c` ver=gtk3 run=toolchain files=1 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 1 / src 1）
- `gtk-28-gtklayout` — 28-GtkLayout ← `Linux/GTK/28-GtkLayout` ver=gtk2-or-3 run=toolchain files=4 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-29-cmake` — 29-cmake ← `Linux/GTK/29-cmake` ver=gtk2-or-3 run=toolchain files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-30-codeblocks` — 30-CodeBlocks ← `Linux/GTK/30-CodeBlocks` ver=gtk2 run=read-only files=3 first=2022-07-14
  - 静态判断工具链版本≈gtk2；main.c: 偏手工 destroy，缺 g_object_unref 意识；main.c: 旧式 gtk_main 循环；手写源码少（非样板 1 / src 2）
- `gtk-32-control` — 32-Control ← `Linux/GTK/32-Control` ver=gtk3 run=toolchain files=4 first=2023-01-28
  - 静态判断工具链版本≈gtk3；main.c: 旧式 gtk_main 循环；手写源码少（非样板 0 / src 1）
- `gtk-g02-gtkpicture` — G02-GtkPicture ← `Linux/GTK/G02-GtkPicture` ver=gtk3 run=toolchain files=16 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g03-buttonlabel` — G03-ButtonLabel ← `Linux/GTK/G03-ButtonLabel` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g04-buttontest` — G04-ButtonTest ← `Linux/GTK/G04-ButtonTest` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g05-image` — G05-Image ← `Linux/GTK/G05-Image` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g05-legacygtk` — G05-LegacyGTK ← `Linux/GTK/G05-LegacyGTK` ver=gtk3 run=toolchain files=12 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 2 / src 3）
- `gtk-g06-image` — G06-Image ← `Linux/GTK/G06-Image` ver=gtk3 run=toolchain files=13 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 2 / src 3）
- `gtk-g07-flowlayout` — G07-FlowLayout ← `Linux/GTK/G07-FlowLayout` ver=gtk3 run=toolchain files=12 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 2 / src 3）
- `gtk-g08-layout` — G08-Layout ← `Linux/GTK/G08-Layout` ver=gtk3 run=toolchain files=12 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 2 / src 3）
- `gtk-g09-gtk4` — G09-Gtk4 ← `Linux/GTK/G09-Gtk4` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g22-begin` — G22-Begin ← `Linux/GTK/G22-Begin` ver=gtk3 run=toolchain files=15 first=2022-07-14
  - 静态判断工具链版本≈gtk3；手写源码少（非样板 4 / src 5）
- `gtk-g27-button` — g27-button ← `Linux/GTK/g27-button` ver=gtk3 run=toolchain files=14 first=2022-07-14
  - 静态判断工具链版本≈gtk3；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-g30-app` — g30-app ← `Linux/GTK/g30-app` ver=gtk3 run=toolchain files=14 first=2022-07-14
  - 静态判断工具链版本≈gtk3；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-g35-text` — g35-text ← `Linux/GTK/g35-text` ver=gtk2-or-3 run=toolchain files=11 first=2022-07-14
  - 静态判断工具链版本≈gtk2-or-3；main.c: 旧式 gtk_main 循环；含 Anjuta 工程痕迹；手写源码少（非样板 0 / src 1）
- `gtk-14-gtk-foobar` — 14-gtk-foobar ← `Linux/GTK/14-gtk-foobar` ver=gtk3 run=toolchain files=18 first=2022-07-14
  - 静态判断工具链版本≈gtk3；14-gtk-foobar.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-15-gtk-foobar` — 15-gtk-foobar ← `Linux/GTK/15-gtk-foobar` ver=gtk3 run=toolchain files=17 first=2022-07-14
  - 静态判断工具链版本≈gtk3；gtk-foobar.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g17-anjuta` — g17-anjuta ← `Linux/GTK/g17-anjuta` ver=gtk3 run=toolchain files=17 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g17-anjuta.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-g37-conponent` — g37-conponent ← `Linux/GTK/g37-conponent` ver=gtk3 run=toolchain files=18 first=2022-07-14
  - 静态判断工具链版本≈gtk3；g37-conponent.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）
- `gtk-gtk-foobar` — gtk-foobar ← `Linux/GTK/gtk-foobar` ver=gtk3 run=toolchain files=18 first=2022-07-14
  - 静态判断工具链版本≈gtk3；gtk-foobar.c: 含 TODO/FIXME；含 Anjuta 工程痕迹；手写源码少（非样板 2 / src 3）

## 待裁决

1. 大量 Anjuta 脚手架工程（g17–g38、gtk-foobar…）业务代码几乎只有 callbacks 空壳：是 keep 作「历史脚手架标本」还是大量 merge/drop？
2. 静态判断多为 gtk2/gtk3；`practice/c-gui-lab` 现为 **GTK4 + libadwaita**。建议归档条目全部 `read-only` 或 `toolchain`（需 GTK3），**不要**假装能并进现有 gtk-style 可运行画廊。
3. `Linux/SDL` 由 leader 划给 c-gui-lab——本清单未收录 SDL；若要我补核对另开任务。
