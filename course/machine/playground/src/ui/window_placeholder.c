#include "../app_window.h"
#include "../progress.h"

#include <stdio.h>

// vendor/lvgl 或 SDL2 还没就位时编译这一份：不开窗口，只把当前状态说清楚，
// 让"主程序 → 启动独立应用 → 读到共用学习库"这条链路能先跑通并被验证。
int app_window_run(struct Progress* progress) {
    printf("Athena · C 语言编程（独立应用）\n");
    printf("窗口后端尚未就位：vendor/lvgl 缺失，或没有找到 SDL2。\n");
    printf("放好 LVGL 源码后重新构建，这里就会换成真正的窗口。\n\n");

    if (progress->handle != NULL) {
        printf("学习库已连接，进度会记在主程序同一个库里。\n");
        const int mastery = progress_load_mastery(progress, "c.Sample.hello");
        printf("示例知识点 c.Sample.hello 当前熟练度：%d / 5\n", mastery);
    } else {
        printf("未连接学习库（没有 --store 参数或文件不可用），本次不记录进度。\n");
    }
    return 0;
}
