#ifndef ATHENA_C_APP_WINDOW_H
#define ATHENA_C_APP_WINDOW_H

struct Progress;

// 打开这个应用的主窗口，直到用户关闭为止；返回进程退出码。
//
// 有两个实现，由 CMake 按 vendor/lvgl 和 SDL2 是否就位来选：
//   src/ui/window_lvgl.c        —— 真窗口
//   src/ui/window_placeholder.c —— 依赖未就位时的占位实现
// 除这两个文件外，其余代码不知道窗口是用什么画出来的。
int app_window_run(struct Progress* progress);

#endif
