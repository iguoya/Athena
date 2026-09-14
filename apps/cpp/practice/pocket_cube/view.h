#pragma once

#include "practice/pocket_cube/state.h"

#include <gtkmm.h>

#include <optional>

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
//
// 两个函数都带默认尺寸参数，调用方可以按需要缩小——比如同一份状态既要
// 当“当前状态”大块展示，也要在下一步穷举的九宫格里以小尺寸重复展示
// 好几份，缩放交给调用方决定，视图本身不关心自己被放在多大的格子里。
//
// make_cube_3d_view() 额外带一个可选的 animation_provider（同样是拉
// 模型）：每次重绘时如果返回非空的 TurnAnimation，就把 state_provider()
// 给出的状态渲染成“正在转动过程中”的中间画面（那一层的格子按动画角度
// 临时偏移），而不是 state_provider() 本身的静态离散状态——调用方在
// 播放一次转动动画时，state_provider 应该继续返回“转动开始前”的旧
// 状态，animation_provider 返回随时间推进的角度，动画播完后把
// animation_provider 换回返回 nullopt、state_provider 换成真正的新
// 状态，最后一帧就能跟真实状态无缝衔接（不会跳一下）。只有 3D 视图
// 支持动画——展开图没有“转动”的空间概念，做动画反而奇怪，保持瞬间
// 刷新，精确读结果用这个。
Gtk::Widget* make_cube_3d_view(
    function<CubeState()> state_provider, int size = 240,
    function<optional<TurnAnimation>()> animation_provider = nullptr);
Gtk::Widget* make_cube_net_view(
    function<CubeState()> state_provider, int width = 240, int height = 180);
