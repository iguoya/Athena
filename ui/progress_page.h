#pragma once

#include "registry/progress_stats.h"

#include <gtkmm.h>

#include <string>

using namespace std;

// 把已经聚合好的分类进度渲染成 GTK 页面。统计口径和数据读取不属于该模块。
Gtk::Widget* make_progress_page(
    const string& category_title,
    const CategoryProgress& progress);
