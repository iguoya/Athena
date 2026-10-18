#include "view.hh"

#include <algorithm>
#include <cmath>
#include <numbers>

namespace view {

using cube::Face;

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

// ---- 立体图的三维小工具 ----

struct V3 {
    double x = 0, y = 0, z = 0;
};
V3 operator+(V3 a, V3 b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
V3 operator*(double k, V3 v) { return {k * v.x, k * v.y, k * v.z}; }
double dot(V3 a, V3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
V3 cross(V3 a, V3 b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
V3 unit(V3 v) {
    const double n = std::sqrt(dot(v, v));
    return {v.x / n, v.y / n, v.z / n};
}
V3 to_v3(cube::Vec v) { return {double(v.x), double(v.y), double(v.z)}; }

// 绕单位轴 a 右手转 phi（Rodrigues 公式）。顺时针转动对应负角度。
V3 rotate_about(V3 v, V3 a, double phi) {
    return std::cos(phi) * v + std::sin(phi) * cross(a, v) + (dot(a, v) * (1 - std::cos(phi))) * a;
}

struct Poly {
    std::array<V3, 4> body;     // 角块的这个面（深色）
    std::array<V3, 4> sticker;  // 贴纸（比面小一圈）
    V3 center;
    double depth = 0;
    int color = -1;     // -1：内侧面，没有贴纸
    bool marked = false;
};

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

// ---- CubeView ----

CubeView::CubeView() {
    set_draw_func(sigc::mem_fun(*this, &CubeView::draw));
    set_size_request(380, 340);
    auto drag = Gtk::GestureDrag::create();
    drag->signal_drag_update().connect([this](double dx, double dy) {
        drag_yaw_ = dx * 0.01;
        drag_pitch_ = -dy * 0.01;
        queue_draw();
    });
    drag->signal_drag_end().connect([this](double, double) {
        yaw_ += drag_yaw_;
        pitch_ = std::clamp(pitch_ + drag_pitch_, -1.4, 1.4);
        drag_yaw_ = drag_pitch_ = 0;
    });
    add_controller(drag);
}

void CubeView::show(const cube::Stickers& state, const Marks& marks) {
    state_ = state;
    marks_ = marks;
    turning_.reset();
    queue_draw();
}

void CubeView::show_turning(const cube::Stickers& before, cube::Move move, double progress) {
    state_ = before;
    marks_ = {};
    turning_ = move;
    progress_ = progress;
    queue_draw();
}

// 画法：8 个角块各有 6 个面，全部先转到当前姿势（正在转的那一层多转一个角度），
// 背对观察者的面丢掉，剩下的从远到近画。每个面先画深色的角块本体，外侧的面再盖一块
// 小一圈的贴纸。内侧面也画成深色：转动中间那一刻能看见魔方的"切面"，是黑的。
void CubeView::draw(const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
    const double yaw = yaw_ + drag_yaw_;
    const double pitch = std::clamp(pitch_ + drag_pitch_, -1.4, 1.4);
    const V3 toward = {std::sin(yaw) * std::cos(pitch), std::sin(pitch), std::cos(yaw) * std::cos(pitch)};
    const V3 right = unit(cross({0, 1, 0}, toward));
    const V3 up = cross(toward, right);
    const double scale = std::min(width, height) / 8.4;
    const double cx = width / 2.0, cy = height / 2.0;

    auto project = [&](V3 p) { return std::pair<double, double>{cx + scale * dot(p, right), cy - scale * dot(p, up)}; };

    V3 axis{};
    double phi = 0;
    if (turning_) {
        axis = to_v3(cube::face_normal(turning_->face));
        phi = -progress_ * turning_->turns * std::numbers::pi / 2;
    }

    static const cube::Vec dirs[6] = {{0, 1, 0}, {1, 0, 0}, {0, 0, 1}, {0, -1, 0}, {-1, 0, 0}, {0, 0, -1}};
    std::vector<Poly> polys;
    for (int c = 0; c < 8; ++c) {
        // 8 个角块的中心：每个坐标是 -1 或 1。
        const cube::Vec p{(c & 1) ? 1 : -1, (c & 2) ? 1 : -1, (c & 4) ? 1 : -1};
        const bool in_layer = turning_ && cube::face_normal(turning_->face).x * p.x +
                                                  cube::face_normal(turning_->face).y * p.y +
                                                  cube::face_normal(turning_->face).z * p.z ==
                                              1;
        for (const cube::Vec n : dirs) {
            V3 normal = to_v3(n);
            const bool outer = n.x * p.x + n.y * p.y + n.z * p.z == 1;
            const V3 t1 = n.x != 0 ? V3{0, 1, 0} : V3{1, 0, 0};
            const V3 t2 = cross(normal, t1);
            Poly poly;
            const V3 centre = to_v3(p) + normal;
            auto corner = [&](double k, double a, double b) {
                V3 v = centre + (k * a) * t1 + (k * b) * t2;
                return in_layer ? rotate_about(v, axis, phi) : v;
            };
            poly.body = {corner(1, 1, 1), corner(1, 1, -1), corner(1, -1, -1), corner(1, -1, 1)};
            poly.sticker = {corner(0.84, 1, 1), corner(0.84, 1, -1), corner(0.84, -1, -1), corner(0.84, -1, 1)};
            if (in_layer) {
                normal = rotate_about(normal, axis, phi);
            }
            if (dot(normal, toward) <= 1e-6) {
                continue;
            }
            poly.center = in_layer ? rotate_about(centre, axis, phi) : centre;
            poly.depth = dot(poly.center, toward);
            if (outer) {
                const int slot = cube::slot_index(p, n);
                poly.color = state_[slot];
                poly.marked = marks_[slot];
            }
            polys.push_back(poly);
        }
    }
    std::sort(polys.begin(), polys.end(), [](const Poly& a, const Poly& b) { return a.depth < b.depth; });

    cr->set_line_join(Cairo::Context::LineJoin::ROUND);
    auto trace = [&](const std::array<V3, 4>& pts) {
        for (int i = 0; i < 4; ++i) {
            const auto [x, y] = project(pts[i]);
            if (i == 0) {
                cr->move_to(x, y);
            } else {
                cr->line_to(x, y);
            }
        }
        cr->close_path();
    };
    for (const Poly& poly : polys) {
        trace(poly.body);
        cr->set_source_rgb(0.09, 0.10, 0.12);
        cr->fill_preserve();
        cr->set_line_width(1.4);
        cr->stroke();
        if (poly.color >= 0) {
            trace(poly.sticker);
            set_color(cr, poly.color);
            cr->fill_preserve();
            if (poly.marked) {
                cr->set_source_rgb(0.85, 0.15, 0.55);
                cr->set_line_width(3.2);
            } else {
                cr->set_source_rgba(0, 0, 0, 0.55);
                cr->set_line_width(1.0);
            }
            cr->stroke();
        }
    }
}

}  // namespace view
