#pragma once

#include "pocket_cube/state.h"

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

// 展开图的十字形网格天生只跟"折叠轴垂直的那两个极面"贴合：默认这版
// （make_cube_net_view()）极面是 U/D，中间一排 L-F-R-B 刚好是绕 U/D
// 轴转动时会动的那一圈，看 U/D 转法很直观；但看 R 转法时受影响的是
// U-F-D-B 这一圈，在这版布局里被拆散在四个角落，不直观。下面两个是
// 分别以 L/R、F/B 为极面重新摊开的十字形展开图，跟默认版是同一个
// CubeState、同一套 sticker_at()/sticker_home()/sticker_label()，只是
// 摊开方式（每个面该转到十字网格哪一格、贴纸编号怎么摆）不同——具体
// 摊法是把六个面绕各自跟极面的公共棱转 90° 展平算出来的（跟默认版
// net_cell_sign() 用的是同一套方法），不是另编的一套规则。
Gtk::Widget* make_cube_net_view_lr_axis(
    function<CubeState()> state_provider, int width = 240, int height = 180);
Gtk::Widget* make_cube_net_view_fb_axis(
    function<CubeState()> state_provider, int width = 240, int height = 180);

// 单面视角：只画 face 这一个面的 2x2 格子（配色 + 调试编号），不做任何
// 3D 投影或透视判断——跟 make_cube_net_view() 里对应那一块用的是同一套
// net_cell_sign() 映射，数字跟展开图上那一块完全一致。给"这个操作面现在
// 长什么样"这种只关心单个面、不需要立体感的场景用（比如按 U/R/F 分开
// 摆三块，替代逐格摆 3D 透视图）。
Gtk::Widget* make_cube_face_view(
    function<CubeState()> state_provider, Face face, int width = 140,
    int height = 140);

// 状态空间可视化：三组同心圆（各 2 圈，组内同色），圆心呈"奔驰标"式
// 三等分布，两两相交，24 个交点按"3 对组合 × 对齐/交叉 2 类"分成 6 组
// 配色——呼应抖音"数学为王时代"第90集《降维理解立体秒解魔方复原》
// 里的环形点阵画面，只是视觉复刻，不追求同一种数学含义。
//
// 三组圆分别对应 U/R/F 三个面：上（橙）= U，左下（绿）= R，右下（紫）
// = F——"操作区"点哪个面的按钮，对应那一组圆的圆心就绕公共中心转过
// 那次转法的角度，跟 3D 魔方视图的转动动画同步播放，animation_provider
// 是拉模型（同 make_cube_3d_view() 的 animation_provider 那一套）：
// 每次重绘取一次当前动画状态，调用方在播放期间持续更新、播完后清空。
struct RingAnimation {
    int active_group; // 0=上/U, 1=左下/R, 2=右下/F
    double angle_offset_radians; // 相对静止角度的偏移，随动画推进变化
};

Gtk::Widget* make_state_space_rings_view(
    long long state_space_size = kCubeStateSpaceSizeIgnoringOrientation,
    int size = 320,
    function<optional<RingAnimation>()> animation_provider = nullptr);
