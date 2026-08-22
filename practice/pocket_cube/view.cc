#include "practice/pocket_cube/view.h"

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

// 淡色版六面配色：F 白、L 橙、U 蓝、R 红、B 黄、D 绿——比标准魔方的
// 高饱和色都调淡（更高明度、更低饱和度），跟 style.css 里其它偏柔和
// 的界面配色更协调，也不会在小小的贴纸格里显得刺眼。
ChartColor sticker_color(Face face) {
    switch (face) {
    case Face::F: return chart_color(0xf7f7f4); // 白（略带暖调，不是死白）
    case Face::L: return chart_color(0xffc48a); // 橙
    case Face::U: return chart_color(0x9dc4f2); // 蓝
    case Face::R: return chart_color(0xf3a3ae); // 红
    case Face::B: return chart_color(0xffe79a); // 黄
    case Face::D: return chart_color(0xa7ddb6); // 绿
    }
    return chart_color(0xffffff);
}

// 一个面在 3D 空间里的 4 个角点，由 face_layout() 的轴信息生成——跟
// sticker_at() 用的是同一套 (u_axis, v_axis, 符号) 定义，几何位置和
// 状态查询天然对得上，不需要另外维护一张“格子顺序对照表”。
struct CubeFace {
    Face face;
    array<Vec3, 4> corners; // (u,v) = (-1,-1)(1,-1)(1,1)(-1,1) 四个角
    Vec3 normal;
};

Vec3 axis_point(Axis axis, int value, Vec3 base) {
    switch (axis) {
    case Axis::X: base.x = value; break;
    case Axis::Y: base.y = value; break;
    case Axis::Z: base.z = value; break;
    }
    return base;
}

Vec3 axis_point3(
    Axis normal_axis, int normal_sign, Axis u_axis, int u_sign, Axis v_axis,
    int v_sign) {
    Vec3 p{0, 0, 0};
    p = axis_point(normal_axis, normal_sign, p);
    p = axis_point(u_axis, u_sign, p);
    p = axis_point(v_axis, v_sign, p);
    return p;
}

CubeFace make_cube_face(Face face) {
    const FaceLayout layout = face_layout(face);
    CubeFace result;
    result.face = face;
    result.corners[0] = axis_point3(
        layout.normal_axis, layout.normal_sign, layout.u_axis, -1, layout.v_axis, -1);
    result.corners[1] = axis_point3(
        layout.normal_axis, layout.normal_sign, layout.u_axis, 1, layout.v_axis, -1);
    result.corners[2] = axis_point3(
        layout.normal_axis, layout.normal_sign, layout.u_axis, 1, layout.v_axis, 1);
    result.corners[3] = axis_point3(
        layout.normal_axis, layout.normal_sign, layout.u_axis, -1, layout.v_axis, 1);
    result.normal = axis_point3(
        layout.normal_axis, layout.normal_sign, layout.u_axis, 0, layout.v_axis, 0);
    return result;
}

array<CubeFace, 6> cube_faces() {
    return {
        make_cube_face(Face::U), make_cube_face(Face::D), make_cube_face(Face::F),
        make_cube_face(Face::B), make_cube_face(Face::R), make_cube_face(Face::L),
    };
}

// 绕 Y 轴转 yaw、再绕 X 轴转 pitch。
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

void fill_grid_cell(
    const Cairo::RefPtr<Cairo::Context>& cr, const array<Vec2, 4>& screen,
    const ChartColor& color) {
    cr->move_to(screen[0].x, screen[0].y);
    for (size_t i = 1; i < screen.size(); ++i) {
        cr->line_to(screen[i].x, screen[i].y);
    }
    cr->close_path();
    cr->set_source_rgb(color.r, color.g, color.b);
    cr->fill_preserve();
    cr->set_source_rgba(0, 0, 0, 0.4);
    cr->set_line_width(1.5);
    cr->stroke();
}

void draw_face_3d(
    const Cairo::RefPtr<Cairo::Context>& cr, const CubeFace& face,
    const CubeState& state, double yaw, double pitch, double scale,
    const Vec2& origin) {
    for (int ui = 0; ui < 2; ++ui) {
        for (int vi = 0; vi < 2; ++vi) {
            const double u0 = ui * 0.5;
            const double v0 = vi * 0.5;
            const array<Vec2, 4> screen = {
                project(
                    rotate(face_point(face, u0, v0), yaw, pitch), scale, origin),
                project(
                    rotate(face_point(face, u0 + 0.5, v0), yaw, pitch), scale,
                    origin),
                project(
                    rotate(face_point(face, u0 + 0.5, v0 + 0.5), yaw, pitch), scale,
                    origin),
                project(
                    rotate(face_point(face, u0, v0 + 0.5), yaw, pitch), scale,
                    origin),
            };
            const int u_sign = ui * 2 - 1;
            const int v_sign = vi * 2 - 1;
            fill_grid_cell(
                cr, screen, sticker_color(sticker_at(state, face.face, u_sign, v_sign)));
        }
    }
}

void draw_cube_3d(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height,
    const CubeState& state, double yaw, double pitch) {
    const double scale = min(width, height) * 0.28;
    const Vec2 origin{width / 2.0, height / 2.0};

    // 背面剔除：只画法向朝向观察者（旋转后 z 分量为正）的面；再按旋转
    // 后的深度从远到近排序，用画家算法处理最多 3 个可见面之间的前后
    // 关系（立方体的可见面只沿棱边相邻、不会互相穿插，排序足够正确，
    // 不需要真正的深度缓冲）。
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
        draw_face_3d(cr, *face, state, yaw, pitch, scale, origin);
    }
}

// 展开图：U 在上、D 在下，L F R B 横排在中间一行——标准的十字形网格。
void draw_cube_net(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height,
    const CubeState& state) {
    const double cell = min(width / 4.0, height / 3.0);
    const double margin_x = (width - cell * 4) / 2;
    const double margin_y = (height - cell * 3) / 2;

    const auto draw_one_face = [&](Face face, int col, int row) {
        const double origin_x = margin_x + col * cell;
        const double origin_y = margin_y + row * cell;
        for (int ui = 0; ui < 2; ++ui) {
            for (int vi = 0; vi < 2; ++vi) {
                const int u_sign = ui * 2 - 1;
                const int v_sign = vi * 2 - 1;
                const array<Vec2, 4> screen = {
                    Vec2{origin_x + ui * cell / 2, origin_y + vi * cell / 2},
                    Vec2{origin_x + (ui + 1) * cell / 2, origin_y + vi * cell / 2},
                    Vec2{
                        origin_x + (ui + 1) * cell / 2,
                        origin_y + (vi + 1) * cell / 2},
                    Vec2{origin_x + ui * cell / 2, origin_y + (vi + 1) * cell / 2},
                };
                fill_grid_cell(
                    cr, screen, sticker_color(sticker_at(state, face, u_sign, v_sign)));
            }
        }
    };

    draw_one_face(Face::U, 1, 0);
    draw_one_face(Face::L, 0, 1);
    draw_one_face(Face::F, 1, 1);
    draw_one_face(Face::R, 2, 1);
    draw_one_face(Face::B, 3, 1);
    draw_one_face(Face::D, 1, 2);
}

} // namespace

Gtk::Widget* make_cube_3d_view(function<CubeState()> state_provider) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(240);
    area->set_content_height(240);

    // 初始视角：能同时看到 U/F/R 三个面。
    auto yaw = make_shared<double>(-M_PI / 4);
    auto pitch = make_shared<double>(-M_PI / 6.5);

    area->set_draw_func(
        [state_provider, yaw, pitch](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_cube_3d(cr, width, height, state_provider(), *yaw, *pitch);
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
            *pitch = clamp(*drag_start_pitch - offset_y * sensitivity, -1.3, 1.3);
            area->queue_draw();
        });
    area->add_controller(drag);
    area->set_cursor("grab");
    area->set_tooltip_text("按住拖动可以旋转查看");

    return area;
}

Gtk::Widget* make_cube_net_view(function<CubeState()> state_provider) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(240);
    area->set_content_height(180);
    area->set_draw_func(
        [state_provider](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_cube_net(cr, width, height, state_provider());
        });
    area->set_tooltip_text("六面展开图：六个面一次性摊开，没有遮挡");
    return area;
}
