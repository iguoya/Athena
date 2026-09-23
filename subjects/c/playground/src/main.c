#include "app_window.h"
#include "progress.h"

#include <stdio.h>
#include <string.h>

static void print_usage(const char* program) {
    printf("用法：%s [--store <学习库路径>]\n\n", program);
    printf("  --store <路径>  与主程序共用的 SQLite 学习库；由启动方传入。\n");
    printf("  --version       输出版本号。\n");
    printf("  --help          显示这段说明。\n");
}

int main(int argc, char** argv) {
    const char* store_path = NULL;

    for (int index = 1; index < argc; ++index) {
        const char* argument = argv[index];
        if (strcmp(argument, "--store") == 0 && index + 1 < argc) {
            store_path = argv[++index];
        } else if (strcmp(argument, "--version") == 0) {
            printf("athena-c 0.1.0\n");
            return 0;
        } else if (strcmp(argument, "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "无法识别的参数：%s\n", argument);
            print_usage(argv[0]);
            return 2;
        }
    }

    struct Progress progress;
    progress_open(&progress, store_path);
    const int status = app_window_run(&progress);
    progress_close(&progress);
    return status;
}
