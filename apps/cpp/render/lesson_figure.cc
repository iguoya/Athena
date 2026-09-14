#include "render/lesson_figure.h"

#include "render/cairo_shapes.h"
#include "render/cairo_text.h"

#include <string>

using namespace std;

namespace {

// 配色与 resources/style.css 的 @athena_* 同源（本身就是 Bootstrap 色板）：
// 这里是 Cairo 侧的副本，改一边要记得改另一边。
constexpr ChartColor kInk{0.129, 0.145, 0.161};      // #212529
constexpr ChartColor kMuted{0.424, 0.459, 0.490};    // #6c757d
constexpr ChartColor kLine{0.678, 0.710, 0.741};     // #adb5bd
constexpr ChartColor kBorder{0.871, 0.886, 0.902};   // #dee2e6
constexpr ChartColor kSurface{1.0, 1.0, 1.0};
constexpr ChartColor kSubtle{0.973, 0.976, 0.980};   // #f8f9fa

constexpr ChartColor kPrimary{0.039, 0.345, 0.792};  // #0a58ca
constexpr ChartColor kPrimarySoft{0.812, 0.886, 1.0};// #cfe2ff
constexpr ChartColor kPrimaryText{0.020, 0.173, 0.396}; // #052c65
constexpr ChartColor kSuccess{0.094, 0.529, 0.329};  // #198754
constexpr ChartColor kSuccessSoft{0.820, 0.906, 0.867}; // #d1e7dd
constexpr ChartColor kSuccessText{0.059, 0.318, 0.196}; // #0f5132
constexpr ChartColor kWarning{0.788, 0.608, 0.031};  // #c99b08
constexpr ChartColor kWarningSoft{1.0, 0.953, 0.804};// #fff3cd
constexpr ChartColor kWarningText{0.400, 0.302, 0.012}; // #664d03
constexpr ChartColor kDanger{0.863, 0.208, 0.271};   // #dc3545
constexpr ChartColor kDangerSoft{0.973, 0.843, 0.855};  // #f8d7da
constexpr ChartColor kDangerText{0.518, 0.125, 0.161};  // #842029
constexpr ChartColor kPurple{0.435, 0.259, 0.757};   // #6f42c1
constexpr ChartColor kPurpleSoft{0.910, 0.867, 0.973};  // #e8ddf8
constexpr ChartColor kInfo{0.812, 0.957, 0.988};     // #cff4fc
constexpr ChartColor kInfoText{0.020, 0.318, 0.376}; // #055160

void dashed_guide(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double x,
    double from_y,
    double to_y,
    const ChartColor& color) {
    cr->set_source_rgb(color.r, color.g, color.b);
    cr->set_line_width(1.2);
    cr->set_dash(vector<double>{4.0, 4.0}, 0.0);
    cr->move_to(x, from_y);
    cr->line_to(x, to_y);
    cr->stroke();
    cr->unset_dash();
}

// 流程图里的一个节点：圆角框加两行居中文字。
void flow_node(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double x,
    double y,
    double width,
    double height,
    const ChartColor& border,
    const ChartColor& fill,
    const ChartColor& title_color,
    const string& title,
    const string& note) {
    shapes::rounded_box(cr, x, y, width, height, border, fill);
    const double center_x = x + width / 2.0;
    if (note.empty()) {
        draw_cairo_text(
            cr, title, center_x, y + height / 2.0, 16.0, title_color, true, 0.5);
        return;
    }
    draw_cairo_text(
        cr, title, center_x, y + height * 0.36, 16.0, title_color, true, 0.5);
    draw_cairo_text(
        cr, note, center_x, y + height * 0.70, 14.0, kMuted, false, 0.5);
}

} // namespace

namespace lesson_figure {

void object_lifetime_timeline(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
    constexpr double kWidth = 880.0;
    constexpr double kHeight = 420.0;
    shapes::begin_design_space(cr, width, height, kWidth, kHeight);

    draw_cairo_text(
        cr, "同一个函数里，三个对象各自活多久", 32.0, 34.0, 20.0, kInk, true);

    // 时间轴
    const double axis_y = 368.0;
    shapes::arrow(cr, 120.0, axis_y, 836.0, axis_y, kLine, false, 2.0);
    draw_cairo_text(cr, "函数开始", 120.0, axis_y + 24.0, 14.0, kMuted);
    draw_cairo_text(cr, "函数返回", 836.0, axis_y + 24.0, 14.0, kMuted, false, 1.0);

    // ① 有名字的局部对象：活到块结束
    draw_cairo_text(cr, "块内对象", 32.0, 100.0, 16.0, kInk);
    draw_cairo_text(cr, "{ ... }", 32.0, 124.0, 14.0, kMuted);
    shapes::rounded_box(cr, 150.0, 80.0, 200.0, 40.0, kSuccess, kSuccessSoft);
    draw_cairo_text(cr, "存在", 250.0, 100.0, 16.0, kInk, false, 0.5);
    dashed_guide(cr, 150.0, 72.0, axis_y, kSuccess);
    dashed_guide(cr, 350.0, 72.0, axis_y, kSuccess);
    draw_cairo_text(cr, "进入块", 150.0, 62.0, 14.0, kMuted, false, 0.5);
    draw_cairo_text(cr, "离开块 → 析构", 350.0, 62.0, 14.0, kMuted, false, 0.5);

    // ② 没有名字的临时对象：活到分号
    draw_cairo_text(cr, "语句里的临时对象", 32.0, 190.0, 16.0, kInk);
    shapes::rounded_box(cr, 404.0, 170.0, 46.0, 40.0, kWarning, kWarningSoft);
    dashed_guide(cr, 450.0, 162.0, axis_y, kWarningText);
    draw_cairo_text(cr, "创建", 404.0, 156.0, 14.0, kMuted);
    draw_cairo_text(
        cr, "分号处（完整表达式末尾）就结束", 470.0, 190.0, 16.0, kInk);

    // ③ 被 const 引用绑定的临时对象：寿命延长
    draw_cairo_text(
        cr, "被 const 引用绑定的临时对象", 32.0, 270.0, 16.0, kInk);
    shapes::rounded_box(cr, 500.0, 250.0, 290.0, 40.0, kPrimary, kPrimarySoft);
    draw_cairo_text(
        cr, "寿命延长到 kept 的作用域结束", 645.0, 270.0, 16.0, kInk, false, 0.5);
    dashed_guide(cr, 500.0, 242.0, axis_y, kPrimary);
    dashed_guide(cr, 790.0, 242.0, axis_y, kPrimary);
    draw_cairo_text(cr, "绑定", 500.0, 236.0, 14.0, kMuted, false, 0.5);

    draw_cairo_text(
        cr,
        "绿 = 有名字的局部对象　黄 = 没有名字的临时对象　蓝 = 被 const 引用延长的临时对象",
        32.0, 330.0, 14.0, kMuted);

    cr->restore();
}

void auto_selection_flow(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
    constexpr double kWidth = 760.0;
    constexpr double kHeight = 430.0;
    shapes::begin_design_space(cr, width, height, kWidth, kHeight);

    draw_cairo_text(
        cr, "选 auto / auto& / const auto&：先定意图，再定写法", 28.0, 30.0,
        18.0, kInk, true);

    shapes::rounded_box(cr, 28.0, 48.0, 704.0, 34.0, kBorder, kSubtle);
    draw_cairo_text(
        cr, "前提：x 是已经存在、且在使用期间一直存活的普通对象（非代理引用）。",
        42.0, 65.0, 14.0, kMuted);

    // 判断一
    shapes::diamond(cr, 150.0, 138.0, 130.0, 38.0, kPrimary, kPrimarySoft);
    draw_cairo_text(cr, "需要一份可以", 150.0, 126.0, 14.0, kInk, false, 0.5);
    draw_cairo_text(cr, "单独修改的值？", 150.0, 148.0, 14.0, kInk, false, 0.5);

    shapes::arrow(cr, 280.0, 138.0, 428.0, 138.0, kMuted);
    draw_cairo_text(cr, "是", 350.0, 126.0, 14.0, kMuted, true, 0.5);
    shapes::rounded_box(cr, 432.0, 112.0, 300.0, 52.0, kSuccess, kSuccessSoft);
    draw_cairo_text(cr, "auto copy = x;", 448.0, 130.0, 15.0, kInk, true);
    draw_cairo_text(
        cr, "独立副本 · 改 copy 不动 x · 有一次复制成本", 448.0, 152.0, 13.0,
        kSuccessText);

    shapes::arrow(cr, 150.0, 176.0, 150.0, 212.0, kMuted);
    draw_cairo_text(cr, "否", 164.0, 196.0, 14.0, kMuted, true);

    // 判断二
    shapes::diamond(cr, 150.0, 254.0, 140.0, 40.0, kPrimary, kPrimarySoft);
    draw_cairo_text(cr, "需要通过这个名字", 150.0, 242.0, 14.0, kInk, false, 0.5);
    draw_cairo_text(cr, "修改原对象？", 150.0, 264.0, 14.0, kInk, false, 0.5);

    shapes::arrow(cr, 290.0, 254.0, 428.0, 254.0, kMuted);
    draw_cairo_text(cr, "是", 355.0, 242.0, 14.0, kMuted, true, 0.5);
    shapes::rounded_box(cr, 432.0, 228.0, 300.0, 52.0, kWarning, kWarningSoft);
    draw_cairo_text(cr, "auto& ref = x;", 448.0, 246.0, 15.0, kInk, true);
    draw_cairo_text(
        cr, "可写别名 · 改 ref 就是改 x · 要求 x 仍存活", 448.0, 268.0, 13.0,
        kWarningText);

    shapes::arrow(cr, 150.0, 294.0, 150.0, 330.0, kMuted);
    draw_cairo_text(cr, "否", 164.0, 314.0, 14.0, kMuted, true);

    // 第三种写法
    shapes::rounded_box(cr, 60.0, 332.0, 672.0, 52.0, kPrimary, kInfo);
    draw_cairo_text(cr, "const auto& view = x;", 78.0, 350.0, 15.0, kInk, true);
    draw_cairo_text(
        cr,
        "只读别名 · 不复制 · 只观察 x 的当前值，不能经 view 赋值 · 要求 x 仍存活",
        78.0, 372.0, 13.0, kInfoText);

    draw_cairo_text(
        cr, "「引用总是更快」不是规则：选型要同时权衡意图、复制成本和对象寿命。",
        28.0, 410.0, 14.0, kMuted);

    cr->restore();
}

void reading_loop(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
    constexpr double kWidth = 960.0;
    constexpr double kHeight = 620.0;
    shapes::begin_design_space(cr, width, height, kWidth, kHeight);

    draw_cairo_text(cr, "读代码时的判断流程", 36.0, 36.0, 22.0, kInk, true);
    draw_cairo_text(
        cr, "五个检查点形成预期，再让证据推动回查", 36.0, 66.0, 15.0, kMuted);

    // 第一行：起点 → 三个检查点
    shapes::rounded_box(cr, 36.0, 104.0, 170.0, 76.0, kWarning, kWarningSoft);
    draw_cairo_text(cr, "看到一段", 121.0, 128.0, 16.0, kWarningText, true, 0.5);
    draw_cairo_text(cr, "陌生代码", 121.0, 154.0, 16.0, kWarningText, true, 0.5);

    shapes::arrow(cr, 210.0, 142.0, 254.0, 142.0, kMuted, false, 2.2);
    flow_node(
        cr, 262.0, 104.0, 178.0, 76.0, kPrimary, kPrimarySoft, kPrimaryText,
        "1 · 认类型", "约束了什么");
    shapes::arrow(cr, 444.0, 142.0, 488.0, 142.0, kMuted, false, 2.2);
    flow_node(
        cr, 496.0, 104.0, 178.0, 76.0, kSuccess, kSuccessSoft, kSuccessText,
        "2 · 看初始化", "状态可靠吗");
    shapes::arrow(cr, 678.0, 142.0, 722.0, 142.0, kMuted, false, 2.2);
    flow_node(
        cr, 730.0, 104.0, 178.0, 76.0, kPurple, kPurpleSoft, kPurple,
        "3 · 查有效期", "对象还在吗");

    // 折回第二行
    cr->set_source_rgb(kMuted.r, kMuted.g, kMuted.b);
    cr->set_line_width(2.2);
    cr->move_to(819.0, 180.0);
    cr->line_to(819.0, 218.0);
    cr->line_to(674.0, 218.0);
    cr->stroke();
    shapes::arrow(cr, 674.0, 218.0, 664.0, 218.0, kMuted, false, 2.2);

    flow_node(
        cr, 484.0, 232.0, 178.0, 76.0, kPrimary, kInfo, kInfoText,
        "4 · 辨表达式", "怎样参与操作");
    shapes::arrow(cr, 484.0, 270.0, 440.0, 270.0, kMuted, false, 2.2);
    flow_node(
        cr, 250.0, 232.0, 178.0, 76.0, kDanger, kDangerSoft, kDangerText,
        "5 · 找转换", "信息丢失了吗");

    // 折回第三行
    cr->set_source_rgb(kMuted.r, kMuted.g, kMuted.b);
    cr->set_line_width(2.2);
    cr->move_to(250.0, 270.0);
    cr->line_to(206.0, 270.0);
    cr->line_to(206.0, 372.0);
    cr->line_to(252.0, 372.0);
    cr->stroke();
    shapes::arrow(cr, 252.0, 372.0, 262.0, 372.0, kMuted, false, 2.2);

    flow_node(
        cr, 262.0, 336.0, 178.0, 72.0, kPrimary, kSubtle, kPrimaryText,
        "形成预期", "说明依据与前提");
    shapes::arrow(cr, 444.0, 372.0, 488.0, 372.0, kMuted, false, 2.2);
    flow_node(
        cr, 496.0, 336.0, 178.0, 72.0, kSuccess, kSubtle, kSuccessText,
        "取得证据", "编译、运行、诊断");
    shapes::arrow(cr, 678.0, 372.0, 722.0, 372.0, kMuted, false, 2.2);
    shapes::rounded_box(cr, 730.0, 336.0, 150.0, 72.0, kWarning, kWarningSoft);
    draw_cairo_text(cr, "符合", 805.0, 358.0, 16.0, kWarningText, true, 0.5);
    draw_cairo_text(cr, "预期？", 805.0, 384.0, 16.0, kWarningText, true, 0.5);

    // 不符合预期：虚线回到起点
    cr->set_source_rgb(kDanger.r, kDanger.g, kDanger.b);
    cr->set_line_width(2.2);
    cr->set_dash(vector<double>{9.0, 7.0}, 0.0);
    cr->move_to(805.0, 408.0);
    cr->line_to(805.0, 470.0);
    cr->line_to(121.0, 470.0);
    cr->line_to(121.0, 192.0);
    cr->stroke();
    cr->unset_dash();
    shapes::arrow(cr, 121.0, 192.0, 121.0, 182.0, kDanger, false, 2.2);
    draw_cairo_text(
        cr, "不符合：回查规则、前提与对象有效期", 463.0, 456.0, 15.0,
        kDangerText, true, 0.5);

    shapes::rounded_box(cr, 36.0, 500.0, 888.0, 84.0, kBorder, kSurface);
    draw_cairo_text(
        cr, "一次运行正常不能证明代码总是正确", 60.0, 528.0, 16.0, kInk, true);
    draw_cairo_text(
        cr,
        "尤其不能据此排除未定义行为：它可能这次恰好给出期望的结果，换个编译器、换个优化级别就不再是。",
        60.0, 556.0, 14.0, kMuted);

    cr->restore();
}

} // namespace lesson_figure
