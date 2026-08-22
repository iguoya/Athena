#include "render/cube_view.h"

#include "render/chart_scale.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace {

struct Vec3 {
    double x = 0;
    double y = 0;
    double z = 0;
};

struct Vec2 {
    double x = 0;
    double y = 0;
};

// 立方体一个可见面：4 个角点（按 (u,v) = (0,0)(1,0)(1,1)(0,1) 顺序，
// 用于后面按 2x2 双线性插值切格子）+ 一个用于背面剔除的法向量 + 该面
// 的固定颜色。
struct CubeFace {
    array<Vec3, 4> corners;
    Vec3 normal;
    ChartColor color;
};

// 六个面。约定 +Y 朝上（U）、+Z 朝向初始观察者（F）、+X 朝右（R）；
// 每个面 4 个角点按“回字”顺序排列，保证矩形不自交。用户配色约定：
// F 白、L 橙、U 蓝、R 红、B 黄、D 绿。
array<CubeFace, 6> cube_faces() {
    return {{
        // U（上，蓝色）
        {{{{-1, 1, -1}, {1, 1, -1}, {1, 1, 1}, {-1, 1, 1}}},
         {0, 1, 0},
         chart_color(0x0051ba)},
        // D（下，绿色）
        {{{{-1, -1, 1}, {1, -1, 1}, {1, -1, -1}, {-1, -1, -1}}},
         {0, -1, 0},
         chart_color(0x00a651)},
        // F（前，白色）
        {{{{-1, -1, 1}, {1, -1, 1}, {1, 1, 1}, {-1, 1, 1}}},
         {0, 0, 1},
         chart_color(0xf2f2f2)},
        // B（后，黄色）
        {{{{1, -1, -1}, {-1, -1, -1}, {-1, 1, -1}, {1, 1, -1}}},
         {0, 0, -1},
         chart_color(0xffd500)},
        // R（右，红色）
        {{{{1, -1, 1}, {1, -1, -1}, {1, 1, -1}, {1, 1, 1}}},
         {1, 0, 0},
         chart_color(0xc41e3a)},
        // L（左，橙色）
        {{{{-1, -1, -1}, {-1, -1, 1}, {-1, 1, 1}, {-1, 1, -1}}},
         {-1, 0, 0},
         chart_color(0xff8c1a)},
    }};
}

// 绕 Y 轴转 yaw、再绕 X 轴转 pitch；只是方向向量的旋转就不需要考虑
// 平移（立方体中心固定在原点）。
Vec3 rotate(const Vec3& p, double yaw, double pitch) {
    const double x1 = p.x * cos(yaw) + p.z * sin(yaw);
    const double z1 = -p.x * sin(yaw) + p.z * cos(yaw);
    const double y1 = p.y;
    const double y2 = y1 * cos(pitch) - z1 * sin(pitch);
    const double z2 = y1 * sin(pitch) + z1 * cos(pitch);
    return {x1, y2, z2};
}

Vec2 project(const Vec3& rotated, double scale, const Vec2& origin) {
    // 正交投影：直接丢弃深度分量；屏幕 y 轴向下为正，3D 的 y 轴向上为
    // 正，所以要取反。
    return {origin.x + rotated.x * scale, origin.y - rotated.y * scale};
}

// 双线性插值：面上 (u, v) ∈ [0,1]^2 对应的 3D 点。
Vec3 face_point(const CubeFace& face, double u, double v) {
    const auto& p00 = face.corners[0];
    const auto& p10 = face.corners[1];
    const auto& p11 = face.corners[2];
    const auto& p01 = face.corners[3];
    const auto lerp = [](double a, double b, double t) { return a + (b - a) * t; };
    const auto mix = [&](double Vec3::*axis) {
        const double top = lerp(p00.*axis, p10.*axis, u);
        const double bottom = lerp(p01.*axis, p11.*axis, u);
        return lerp(top, bottom, v);
    };
    return {mix(&Vec3::x), mix(&Vec3::y), mix(&Vec3::z)};
}

void draw_face(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const CubeFace& face,
    double yaw,
    double pitch,
    double scale,
    const Vec2& origin) {
    for (int ui = 0; ui < 2; ++ui) {
        for (int vi = 0; vi < 2; ++vi) {
            const double u0 = ui * 0.5;
            const double v0 = vi * 0.5;
            const array<Vec2, 4> screen = {
                project(rotate(face_point(face, u0, v0), yaw, pitch), scale, origin),
                project(
                    rotate(face_point(face, u0 + 0.5, v0), yaw, pitch), scale, origin),
                project(
                    rotate(face_point(face, u0 + 0.5, v0 + 0.5), yaw, pitch), scale,
                    origin),
                project(
                    rotate(face_point(face, u0, v0 + 0.5), yaw, pitch), scale, origin),
            };
            cr->move_to(screen[0].x, screen[0].y);
            for (size_t i = 1; i < screen.size(); ++i) {
                cr->line_to(screen[i].x, screen[i].y);
            }
            cr->close_path();
            cr->set_source_rgb(face.color.r, face.color.g, face.color.b);
            cr->fill_preserve();
            cr->set_source_rgba(0, 0, 0, 0.4);
            cr->set_line_width(1.6);
            cr->stroke();
        }
    }
}

void draw_cube(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height, double yaw,
    double pitch) {
    const double scale = min(width, height) * 0.28;
    const Vec2 origin{width / 2.0, height / 2.0};

    // 背面剔除：只画法向朝向观察者（旋转后 z 分量为正）的面；再按旋转
    // 后的深度从远到近排序，用画家算法处理三个可见面之间的前后关系
    // （立方体最多同时看到 3 个面，它们只沿棱边相邻、不会互相穿插，
    // 排序足够正确，不需要真正的深度缓冲）。
    auto faces = cube_faces();
    vector<const CubeFace*> visible;
    for (const auto& face : faces) {
        if (rotate(face.normal, yaw, pitch).z > 0) {
            visible.push_back(&face);
        }
    }
    sort(visible.begin(), visible.end(), [&](const CubeFace* a, const CubeFace* b) {
        return rotate(a->normal, yaw, pitch).z < rotate(b->normal, yaw, pitch).z;
    });

    for (const auto* face : visible) {
        draw_face(cr, *face, yaw, pitch, scale, origin);
    }
}

} // namespace

Gtk::Widget* make_cube_3d_view() {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(280);
    area->set_content_height(280);

    // 初始视角：能同时看到 U/F/R 三个面，跟之前固定等距图的观感接近。
    auto yaw = make_shared<double>(-M_PI / 4);
    auto pitch = make_shared<double>(-M_PI / 6.5);

    area->set_draw_func(
        [yaw, pitch](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_cube(cr, width, height, *yaw, *pitch);
        });

    // 鼠标拖拽旋转：拖动过程中的位移量换算成 yaw/pitch 增量；俯仰角
    // 限制在正负约 75°，避免转到正对某条棱、视觉上完全失去立体感。
    auto drag = Gtk::GestureDrag::create();
    auto drag_start_yaw = make_shared<double>(0.0);
    auto drag_start_pitch = make_shared<double>(0.0);
    drag->signal_drag_begin().connect(
        [yaw, pitch, drag_start_yaw, drag_start_pitch](double, double) {
            *drag_start_yaw = *yaw;
            *drag_start_pitch = *pitch;
        });
    drag->signal_drag_update().connect(
        [yaw, pitch, drag_start_yaw, drag_start_pitch, area](
            double offset_x, double offset_y) {
            constexpr double sensitivity = 0.012;
            *yaw = *drag_start_yaw + offset_x * sensitivity;
            *pitch = clamp(
                *drag_start_pitch - offset_y * sensitivity, -1.3, 1.3);
            area->queue_draw();
        });
    area->add_controller(drag);
    area->set_cursor("grab");
    area->set_tooltip_text("按住拖动可以旋转查看");

    return area;
}
