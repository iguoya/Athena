#pragma once

// glib 2.90 与 glibmm 2.88 之间的一处临时兼容垫片。
//
// 背景：glib 2.90（通往 3.0 的开发系列）把一批类型改用 G_DECLARE_FINAL_TYPE
// 声明，宏会生成 `typedef struct GDBusActionGroupClass GDBusActionGroupClass;`；
// 而 glibmm / gtkmm 的头文件里仍是 gmmproc 生成的前置声明
// `using GDBusActionGroupClass = struct _GDBusActionGroupClass;`——同一个名字
// 指向两个不同的结构体，编译期直接冲突。
//
// 这**不是平台问题**：本地 macOS（glib 2.88.3）与 CI 上的 Ubuntu（glib 2.88.0）
// 都编得过，MSYS2 只是因为跟进上游更快才先撞上。等 Linux 与 macOS 升到 2.90，
// 同样会撞，所以这个垫片对三个平台都有意义，不是给 Windows 开的后门。
//
// 做法：把 glibmm 用的下划线名重定向到 glib 实际生成的名字，两边的声明就一致了。
// 只在 glib >= 2.90 时生效——低版本上那些 `struct _Xxx` 是真实存在的类型名，
// 乱改会把正确的代码改坏。
//
// **这是欠账，不是长久之计。** glibmm 适配 glib 2.90 之后应当整个删掉：删掉后
// cpp-windows 这个 job 仍然绿，就说明上游已经修好了。
#include <glib.h>

#if GLIB_CHECK_VERSION(2, 90, 0)
#define _GDBusActionGroupClass GDBusActionGroupClass
#define _GEmblemClass GEmblemClass
#define _GdkCursorClass GdkCursorClass
#endif
