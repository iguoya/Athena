#include "chapter_overview.h"

#include <gdkmm/clipboard.h>
#include <gdkmm/display.h>
#include <giomm/appinfo.h>
#include <glib.h>

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
    // 交给 GIO 按系统的默认处理器打开：有装豆包 App 的机器会被 doubao://
    // 接走，没有的退回网页版。两者都不需要知道当前是什么平台——
    // "用什么打开这个 URI"本来就是系统的事（ADR 0047）。
    // ATHENA_AI_URI 可以覆盖成自己习惯的助手地址。
    string uri = "doubao://";
    if (const char* custom = g_getenv("ATHENA_AI_URI")) {
        uri = custom;
    }
    try {
        Gio::AppInfo::launch_default_for_uri(uri);
    } catch (const Glib::Error&) {
        try {
            Gio::AppInfo::launch_default_for_uri("https://www.doubao.com");
        } catch (const Glib::Error& error) {
            cerr << "Failed to launch AI assistant: " << error.what() << endl;
        }
    }
}
