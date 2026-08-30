#pragma once

#include "registry/chapter_catalog.h"

#include <gtkmm.h>

#include <functional>
#include <string>
#include <vector>

using namespace std;

// 分类索引页：进入一个分类后的默认页面，用自适应网格列出全部章节，
// 每格一章（图标 + 标题 + 简介），点击进入该章。学习进度、手册作为
// 末尾的工具卡片。页面数据由 MainWindow 从 ChapterCatalog 派生，本模块
// 只负责把它渲染成控件树（与 make_progress_page 同类）。
struct ChapterIndexEntry {
    string key; // 章节页面键；回调按它定位目标
    string title;
    string description;
    IconSpec icon;
};

// 分类学习路线里的一个阶段：只是进入章节前的一段全局印象，不是入口，
// 不对应任何页面键，因此和 ChapterIndexEntry 分开。accent 是图标强调色的
// CSS class（route-icon-blue 等），由调用方给定。
struct ChapterIndexStage {
    IconSpec icon;
    string accent;
    string title;
    string summary;
};

struct ChapterIndexSpec {
    string category_title;
    // 可空；非空时在章节网格上方渲染成一条“学习路线”预览条。
    vector<ChapterIndexStage> roadmap;
    vector<ChapterIndexEntry> chapters;
    vector<ChapterIndexEntry> tools;
    function<void(const string& key)> on_open;
};

Gtk::Widget* make_chapter_index_page(const ChapterIndexSpec& spec);
