#pragma once

#include <cairomm/context.h>

using namespace std;

// 学习页里的示意图，纯 Cairo 绘制（ADR 0038）。
//
// 为什么不再用 SVG 图片：图片要经 gdk-pixbuf 的外部解码器，缺 SVG loader 时
// Gtk::Picture 既不报错也不显示，页面上只剩一块空白；图片里的字也不再是字，
// 选不中、不跟随系统字号与主题。表格和卡片式的内容改用 .blp 控件承载，
// **只有位置本身带信息的图**——时间轴、分支流程、回环——留在这里自绘。
//
// 每个函数不持有任何状态：给一块画布，按自己的设计坐标画完，内部负责等比
// 缩放与居中，因此同一张图可以挂在任何页面的 DrawingArea 上。
namespace lesson_figure {

// 「同一个函数里，三个对象各自活多久」：块内对象、语句里的临时对象、被
// const 引用延长的临时对象，三段寿命画在同一条时间轴上。
void object_lifetime_timeline(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height);

// 「选 auto / auto& / const auto&」：两次判断分出三种写法，分支结构本身
// 就是这张图要讲的东西。
void auto_selection_flow(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height);

// 「读代码时的判断流程」：五个检查点依次推进，形成预期、取得证据，不符合
// 预期时沿虚线回到起点重查。回环是这张图的主语。
void reading_loop(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height);

} // namespace lesson_figure
