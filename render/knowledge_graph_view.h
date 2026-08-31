#pragma once

#include "registry/knowledge_graph.h"

#include <gtkmm.h>

#include <functional>
#include <string>

using namespace std;

// C++ 分类索引使用的知识图谱：层号即行，层内节点按 slot 水平居中，
// 前置关系用向下箭头连接。Cairo 只绘制连线；每个节点是真实 GTK Button，
// 展示章节图标、标题、简介、汇总重要度、掌握数量和完成进度。
//
// 不引图表库，理由同 render/chart_view：数据规模很小、图形种类单一，Cairo
// 直接画比接一套 JS 图表栈划算，也不必为此让页面依赖 WebView。
//
// 返回图谱与右侧说明栏；外层分类索引页负责滚动和学习工具入口。
// on_open 收到被点击章节的稳定 name。
Gtk::Widget* make_knowledge_graph_view(
    const KnowledgeGraph& graph,
    function<void(const string& chapter_name)> on_open);
