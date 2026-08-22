#pragma once

#include "practice/pocket_cube/state.h"

#include <gtkmm.h>

using namespace std;

// 2 阶魔方的两种可视化，都吃同一个 CubeState，都是纯 Cairo 手绘（跟
// render/chart_view.h 一样，不引入 OpenGL/3D 或图表库）：
//
// - make_cube_3d_view()：可拖拽旋转的正交投影视图，直觉的立体印象，
//   但任意时刻最多同时看到 3 个面。
// - make_cube_net_view()：六面展开图（十字形网格），六个面一次性摊
//   开、没有遮挡，精确读状态用这个。
//
// state_provider 是“拉”模型：每次重绘时才调用一次取当前状态，不是把
// 状态值直接传进来存起来——状态会在外部变化（应用了一次转动），视图
// 自己不知道，需要调用方在状态变了以后主动对返回的 Gtk::Widget*
// （实际都是 Gtk::DrawingArea*）调用 queue_draw() 触发重绘。
//
// 样例用法：
//   auto state = make_shared<CubeState>(make_solved_cube());
//   auto* view_3d = make_cube_3d_view([state] { return *state; });
//   auto* view_net = make_cube_net_view([state] { return *state; });
//   canvas_host->append(*view_3d);
//   net_host->append(*view_net);
//   ...
//   *state = apply_move(*state, {Face::U, Turn::Clockwise});
//   view_3d->queue_draw();
//   view_net->queue_draw();
Gtk::Widget* make_cube_3d_view(function<CubeState()> state_provider);
Gtk::Widget* make_cube_net_view(function<CubeState()> state_provider);
