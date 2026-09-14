#pragma once

#include "registry/chapter_catalog.h"
#include "registry/knowledge_graph.h"
#include "registry/progress_stats.h"

#include <gtkmm.h>

#include <functional>
#include <optional>
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
    // C++ 分类提供时，以带前置关系的知识图谱代替普通章节网格；其他分类
    // 保持 FlowBox。图谱仍由 catalog/prerequisites 派生，不新增导航数据源。
    optional<KnowledgeGraph> knowledge_graph;
    // 与图谱一起提供时，在图谱上方渲染学习进度概览（统计、建议、两张图）。
    // 进度不再单开一页：章节与知识点的逐条进度画在图谱的章节卡片上，
    // 概览放在同一页顶部，一个入口看完。
    optional<CategoryProgress> progress;
    function<void(const string& key)> on_open;
    function<void(const string& chapter_name)> on_open_chapter;
};

Gtk::Widget* make_chapter_index_page(const ChapterIndexSpec& spec);
