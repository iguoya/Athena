#pragma once

// 让 apps/cpp 在 MSYS2 当前的包组合下编得过（glib 2.90 + glibmm 2.86）。
//
// 冲突：glib 2.89.2 起把 GDBusActionGroup / GEmblem / GdkCursor 改用
// G_DECLARE_FINAL_TYPE 声明，宏会生成 `typedef struct {...} GXxxClass;`；
// 而 glibmm / gdkmm 2.86 仍按旧方式前置声明 `using GXxxClass = struct _GXxxClass;`。
// 同一个名字指向两个类型，编译期直接冲突。上游 glibmm 2.89.0 已改掉写法，
// 只是 MSYS2 还没打包（时间线见主仓库 ADR 0049）。
//
// **这里不追求版本形式上配套，只要它能在 Windows 上编过、跑对。** glib 那次改的
// 是声明方式，不是内存布局——三个 Class 结构体实质都是「只含父类字段的壳」，
// ABI 没变。所以做法是：先让 glib 自己的声明就位，再把 C++ 绑定那三个前置声明
// **改个名字**。它们在绑定里只当类型标签用（`using BaseClassType = GXxxClass`），
// 改名后绑定内部仍然自洽，也不再和 glib 撞名。
//
// 注意方向：要改的是 `using` **左边**那个名字，不能去动 `struct _GXxxClass`——
// 把下划线名映射成 typedef 名会得到 `struct <typedef-name>`，那是非法的
// （第一版垫片就是这么写的，实测报 "using typedef-name after 'struct'"）。
//
// 这是欠账。MSYS2 把 glibmm 更新到 2.89+ 之后，删掉本文件与 meson.build 里那行
// -include 即可；删完 cpp-windows 仍然绿，就说明上游已经跟上了。
// 每个 include 都用 __has_include 兜住：-include 是**项目级**的，会预置到所有
// C++ 编译单元前面，包括不链接 gtk4 / glib 的那些目标（生成器检查、纯逻辑测试）。
// 它们的 include 路径里没有这些头文件，不设防就会在无关目标上报
// "fatal error: gdk/gdk.h: No such file or directory"。
#if __has_include(<glib.h>)
#include <glib.h>

#if GLIB_CHECK_VERSION(2, 89, 2)
// 先包含，让 glib / gdk 自己生成的 typedef 先占住这三个名字
#if __has_include(<gdk/gdk.h>)
#include <gdk/gdk.h>
#endif
#if __has_include(<gio/gio.h>)
#include <gio/gio.h>
#endif

#define GDBusActionGroupClass GDBusActionGroupClass_mm_shim
#define GEmblemClass GEmblemClass_mm_shim
#define GdkCursorClass GdkCursorClass_mm_shim
#endif
#endif
