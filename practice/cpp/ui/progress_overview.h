#pragma once

#include "registry/progress_stats.h"
#include "storage/learning_store.h"

#include <gtkmm.h>

#include <string>

using namespace std;

// 分类学习进度的概览区：统计卡片、建议接下来学什么、完成度与熟练度分布
// 两张图。它嵌在学习图谱页顶部，不再是独立页面——章节与知识点的逐条进度
// 本来就画在图谱的章节卡片上，再单开一页会让同一件事有两个入口。
//
// 统计口径和数据读取不属于该模块。
// stats 是由作答流水派生的量（仓库 ADR 0052）：记了就要给使用者看，
// 否则等于没记。它与 progress 的区别是——progress 说「会了多少」，
// stats 说「最近做了多少、坚持了几天」。
Gtk::Widget* make_progress_overview(
    const CategoryProgress& progress, const LearningStore::LearningStats& stats);
