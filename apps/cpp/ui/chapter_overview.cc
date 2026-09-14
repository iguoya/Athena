#include "chapter_overview.h"

#include <gdkmm/clipboard.h>
#include <gdkmm/display.h>
#include <glib.h>
#include <glibmm/spawn.h>

#include <exception>
#include <iostream>
#include <string>

using namespace std;

void launch_local_chapter_overview(const ChapterMeta& chapter) {
    string prompt = "请给出 C++ 章节「" + chapter.title + "」的学习总纲："
        + chapter.description;
    if (!chapter.subchapters.empty()) {
        prompt += "\n\n本章知识点：";
        for (const auto& subchapter : chapter.subchapters) {
            prompt += "\n- " + subchapter.title + "：" + subchapter.description;
        }
    }
    Gdk::Display::get_default()->get_clipboard()->set_text(prompt);

    // 提示词已复制到剪贴板；再尽力唤起一个助手入口方便用户粘贴。
    // macOS 用 `open` 拉起本机豆包 App 的 doubao:// scheme；其他平台
    // （Linux）没有这个 scheme 处理器，退回用默认浏览器打开豆包网页版。
    // 两个平台都可用 ATHENA_AI_COMMAND 覆盖成本机习惯的助手命令。
#ifdef __APPLE__
    string command = "open doubao://";
#else
    string command = "xdg-open https://www.doubao.com";
#endif
    if (const char* custom = g_getenv("ATHENA_AI_COMMAND")) {
        command = custom;
    }
    try {
        Glib::spawn_command_line_async(command);
    } catch (const exception& error) {
        cerr << "Failed to launch AI assistant (" << command
             << "): " << error.what() << endl;
    }
}
