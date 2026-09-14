#pragma once

#include "registry/progress_stats.h"

#include <gtkmm.h>

#include <string>

using namespace std;

// 分类学习进度的概览区：统计卡片、建议接下来学什么、完成度与熟练度分布
// 两张图。它嵌在学习图谱页顶部，不再是独立页面——章节与知识点的逐条进度
// 本来就画在图谱的章节卡片上，再单开一页会让同一件事有两个入口。
//
// 统计口径和数据读取不属于该模块。
Gtk::Widget* make_progress_overview(const CategoryProgress& progress);
