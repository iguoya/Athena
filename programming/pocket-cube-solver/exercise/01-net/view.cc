#include "view.hh"

#include <algorithm>
#include <cmath>
#include <numbers>

namespace view {

std::array<double, 3> rgb(int face) {
    // 白下绿前时的真实配色：U 黄、R 橙、F 绿、D 白、L 红、B 蓝。
    static const std::array<std::array<double, 3>, 6> palette = {{
        {1.000, 0.835, 0.000},  // U 黄
        {1.000, 0.345, 0.000},  // R 橙
        {0.000, 0.608, 0.282},  // F 绿
        {0.957, 0.957, 0.957},  // D 白
        {0.718, 0.071, 0.204},  // L 红
        {0.000, 0.275, 0.678},  // B 蓝
    }};
    if (face < 0 || face >= 6) {
        return {0.55, 0.57, 0.60};
    }
    return palette[face];
}

namespace {

void set_color(const Cairo::RefPtr<Cairo::Context>& cr, int face, double alpha = 1.0) {
    const auto c = rgb(face);
    cr->set_source_rgba(c[0], c[1], c[2], alpha);
}

void rounded_rect(const Cairo::RefPtr<Cairo::Context>& cr, double x, double y, double w, double h,
                  double r) {
    cr->begin_new_sub_path();
    cr->arc(x + w - r, y + r, r, -std::numbers::pi / 2, 0);
    cr->arc(x + w - r, y + h - r, r, 0, std::numbers::pi / 2);
    cr->arc(x + r, y + h - r, r, std::numbers::pi / 2, std::numbers::pi);
    cr->arc(x + r, y + r, r, std::numbers::pi, 3 * std::numbers::pi / 2);
    cr->close_path();
}

// ---- 展开图的布局 ----
// 十字形：U 在上，L F R B 一排，D 在下。每个面 2×2 格，面与面之间留一点缝。
constexpr double kGap = 0.28;
struct FaceSpot {
    int col, row;
};
constexpr FaceSpot kSpots[6] = {{1, 0}, {2, 1}, {1, 1}, {1, 2}, {0, 1}, {3, 1}};  // U R F D L B

struct NetGeometry {
    double cell = 0, ox = 0, oy = 0;
    double face_x(int face) const { return ox + kSpots[face].col * (2 + kGap) * cell; }
    double face_y(int face) const { return oy + kSpots[face].row * (2 + kGap) * cell; }
};

NetGeometry net_geometry(int width, int height) {
    const double total_w = 4 * 2 + 3 * kGap;
    const double total_h = 3 * 2 + 2 * kGap;
    NetGeometry g;
    g.cell = std::min(width * 0.94 / total_w, height * 0.9 / total_h);
    g.ox = (width - total_w * g.cell) / 2;
    g.oy = (height - total_h * g.cell) / 2 + 0.12 * g.cell;  // 给面名留一点位置
    return g;
}

}  // namespace

// ---- NetView ----

NetView::NetView() {
    set_draw_func(sigc::mem_fun(*this, &NetView::draw));
    set_size_request(300, 230);
    auto click = Gtk::GestureClick::create();
    click->signal_released().connect(sigc::mem_fun(*this, &NetView::on_click));
    add_controller(click);
}

void NetView::show(const cube::Stickers& state, const Marks& marks) {
    state_ = state;
    marks_ = marks;
    queue_draw();
}

// 把点击换算成第几格；点在缝里或外面不算。
void NetView::on_click(int, double x, double y) {
    const NetGeometry g = net_geometry(get_width(), get_height());
    for (int face = 0; face < 6; ++face) {
        const double lx = (x - g.face_x(face)) / g.cell;
        const double ly = (y - g.face_y(face)) / g.cell;
        if (lx >= 0 && lx < 2 && ly >= 0 && ly < 2) {
            picked_.emit(face * 4 + static_cast<int>(ly) * 2 + static_cast<int>(lx));
            return;
        }
    }
}

void NetView::draw(const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
    const NetGeometry g = net_geometry(width, height);
    static const char* letters[6] = {"U", "R", "F", "D", "L", "B"};
    for (int face = 0; face < 6; ++face) {
        cr->set_source_rgba(0.5, 0.52, 0.56, 0.9);
        cr->set_font_size(g.cell * 0.34);
        cr->move_to(g.face_x(face) + g.cell * 0.02, g.face_y(face) - g.cell * 0.04);
        cr->show_text(letters[face]);
        for (int k = 0; k < 4; ++k) {
            const int i = face * 4 + k;
            const double x = g.face_x(face) + (k % 2) * g.cell;
            const double y = g.face_y(face) + (k / 2) * g.cell;
            const double inset = g.cell * 0.05;
            rounded_rect(cr, x + inset, y + inset, g.cell - 2 * inset, g.cell - 2 * inset, g.cell * 0.14);
            set_color(cr, state_[i]);
            cr->fill_preserve();
            cr->set_source_rgba(0.1, 0.1, 0.12, 0.9);
            cr->set_line_width(std::max(1.0, g.cell * 0.035));
            cr->stroke();
            if (marks_[i]) {
                rounded_rect(cr, x + inset * 0.2, y + inset * 0.2, g.cell - 0.4 * inset,
                             g.cell - 0.4 * inset, g.cell * 0.17);
                cr->set_source_rgba(0.85, 0.15, 0.55, 1.0);
                cr->set_line_width(std::max(2.0, g.cell * 0.08));
                cr->stroke();
            }
        }
    }
}

}  // namespace view
