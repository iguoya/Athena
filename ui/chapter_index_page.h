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

struct ChapterIndexSpec {
    string category_title;
    vector<ChapterIndexEntry> chapters;
    vector<ChapterIndexEntry> tools;
    function<void(const string& key)> on_open;
};

Gtk::Widget* make_chapter_index_page(const ChapterIndexSpec& spec);
