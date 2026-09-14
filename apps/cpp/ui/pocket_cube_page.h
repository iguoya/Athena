#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"

#include <gtkmm.h>

#include <functional>

using namespace std;

// 2 阶魔方实践页的状态、控件树和交互。它不走标准无状态实验执行器；
// MainWindow 只在页面创建时传入“说明文档”跨页请求。
class PocketCubePage final {
public:
    PocketCubePage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        const ContentLoader& content_loader,
        function<void()> on_overview_requested);
};
