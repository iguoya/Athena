#pragma once

#include "registry/domain_graph.h"

#include <gtkmm.h>

#include <functional>
#include <string>

using namespace std;

// 首页学科知识图谱：层号即行，层内节点按 slot 水平分列，前置关系用向下
// 箭头连接。Cairo 只画连线；每个节点是真实 GTK Button——已开放领域展示
// 图标、简介、知识点数量和完成进度并可点击，规划中 / 理论参考领域灰显、
// 不可点，只给出定位与依赖。
//
// 布局思路与 render/knowledge_graph_view 一致（等宽层轨道 + Overlay 上的
// DrawingArea 画边），因为两张图同构、只差一个层级。不引图表库理由同
// render/chart_view。
//
// on_open 只会收到 kind == Available 的领域 id（分类 name）。
Gtk::Widget* make_domain_graph_view(
    const DomainGraph& graph,
    function<void(const string& domain_id)> on_open);
