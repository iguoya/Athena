#pragma once

// MSYS2 上 glib ≥ 2.89.2 与尚未跟上的 glibmm 会在三个 Class 名字上冲突。
// 垫片只改 C++ 绑定的类型标签，不改内存布局。glibmm 升到 2.89+ 后连同
// meson.build 里的 -include 一起删掉。纯逻辑测试的编译单元没有这些头，
// __has_include 让 -include 对它们变成空操作。
#if __has_include(<glib.h>)
#include <glib.h>

#if GLIB_CHECK_VERSION(2, 89, 2)
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
