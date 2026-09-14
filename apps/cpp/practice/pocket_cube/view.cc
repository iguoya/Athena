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

// 淡色版六面配色：U 白、D 黄、F 绿、B 蓝、L 橙、R 红——这是魔方圈最
// 通用的西方配色方案（Western/BOY scheme，蓝-橙-黄三色角块顺时针排列
// 是这个方案的识别特征），WCA 比赛虽然不强制统一配色，但绝大多数速拧
// 魔方厂商和教学资料都用这一套，不是本项目自定的。颜色本身比标准魔方
// 的高饱和色都调淡（更高明度、更低饱和度），跟 style.css 里其它偏柔和
// 的界面配色更协调，也不会在小小的贴纸格里显得刺眼。
ChartColor sticker_color(Face face) {
    switch (face) {
    case Face::U: return chart_color(0xf7f7f4); // 白（略带暖调，不是死白）
    case Face::D: return chart_color(0xffe79a); // 黄
    case Face::F: return chart_color(0xa7ddb6); // 绿
    case Face::B: return chart_color(0x9dc4f2); // 蓝
    case Face::L: return chart_color(0xffc48a); // 橙
    case Face::R: return chart_color(0xf3a3ae); // 红
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

// 这个格子（face 面上 (u_sign, v_sign) 那一格）对应的角块，在 axis
// 这根轴上的坐标符号——用来判断这一格是否处于正在播放动画的那一层
// （跟 face_layout(face) 三根轴里，法向轴/u 轴/v 轴哪一根跟 axis 一致，
// 就取对应的符号）。三根轴里必然有且只有一根匹配 axis。
int corner_axis_sign(Face face, int u_sign, int v_sign, Axis axis) {
    const FaceLayout layout = face_layout(face);
    if (layout.normal_axis == axis) {
        return layout.normal_sign;
    }
    if (layout.u_axis == axis) {
        return u_sign;
    }
    return v_sign;
}

// 把一个模型空间的点绕 axis 轴转 degrees 度（标准数学定义，右手定则，
// 从轴正方向看过去逆时针为正）——跟 tests/pocket_cube_state_test.cc
// 里 TurnAngleDegreesMatchesActualCoordinateChange 验证过的是同一套
// 公式，跟 turn_angle_degrees() 配合使用时，动画播到终点角度正好落在
// apply_move() 算出的真实坐标上，不会跟状态跳变错位。
Vec3 rotate_around_axis(const Vec3& p, Axis axis, double degrees) {
    const double radians = degrees * M_PI / 180.0;
    const double c = cos(radians);
    const double s = sin(radians);
    switch (axis) {
    case Axis::X: return {p.x, p.y * c - p.z * s, p.y * s + p.z * c};
    case Axis::Y: return {p.x * c + p.z * s, p.y, -p.x * s + p.z * c};
    case Axis::Z: return {p.x * c - p.y * s, p.x * s + p.y * c, p.z};
    }
    return p;
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

// 待画的一格贴纸：屏幕坐标 + 颜色 + 深度（4 个角点旋转后、投影前的
// 平均 z，越大越靠近观察者）。旧实现按“整面固定法向量”一次性判断
// 3 个面的可见性和前后顺序，理由是“转动的那一层里，跟转轴同向的那个
// 面法向量不变，其余面只有半边格子参与转动，面本身固定法向量不受
// 影响”——这个理由只覆盖了“面会不会被错误剔除”，没考虑到转到 90°~180°
// 之间时，动画格子的屏幕位置会明显偏出所在面原来的平面、跟另一个静态
// 面产生实际的前后遮挡，而静态整面排序完全不知道这件事，会把正在转动
// 的格子画在不该被挡住的静态面后面——尤其转 180° 时格子要转到正对面，
// 偏移量最大，最容易被整面挡住，看起来就是“这几格没渲染出来”。
// 现在改成逐格（而不是逐面）计算法向量和深度：动画中那一层的格子用
// 旋转到当前角度之后的法向量做背面剔除、用旋转后 4 个角点的平均深度
// 参与全局排序，没在转的格子仍然用所在面的固定法向量——跟旧结果完全
// 一致，因为同一面 4 格法向量本来就相同、彼此又不重叠，排序谁先谁后
// 都无所谓；只有正在转动、跟原来所在面不再共面的格子才会因此在深度
// 排序里换到正确的位置。
struct StickerDraw {
    array<Vec2, 4> screen;
    ChartColor color;
    double depth;
};

void collect_face_stickers(
    const CubeFace& face, const CubeState& state, double yaw, double pitch,
    double scale, const Vec2& origin, const TurnAnimation* animation,
    vector<StickerDraw>& out) {
    for (int ui = 0; ui < 2; ++ui) {
        for (int vi = 0; vi < 2; ++vi) {
            const double u0 = ui * 0.5;
            const double v0 = vi * 0.5;
            const int u_sign = ui * 2 - 1;
            const int v_sign = vi * 2 - 1;

            const bool animating = animation != nullptr &&
                corner_axis_sign(face.face, u_sign, v_sign, animation->axis) ==
                    animation->layer_coord;

            const auto model_point = [&](double u, double v) {
                Vec3 point = face_point(face, u, v);
                if (animating) {
                    point = rotate_around_axis(
                        point, animation->axis, animation->current_degrees);
                }
                return point;
            };

            // 背面剔除用这一格“此刻真正”的法向量：没在转就是所在面
            // 固定的法向量，正在转就跟着模型坐标一起绕动画轴转到当前
            // 角度——这一步就是修复的关键，静态法向量在转到 90° 以后
            // 已经不能代表这格真实朝向哪边了。
            Vec3 normal = face.normal;
            if (animating) {
                normal = rotate_around_axis(
                    normal, animation->axis, animation->current_degrees);
            }
            if (rotate(normal, yaw, pitch).z <= 0) {
                continue;
            }

            const array<Vec3, 4> rotated_corners = {
                rotate(model_point(u0, v0), yaw, pitch),
                rotate(model_point(u0 + 0.5, v0), yaw, pitch),
                rotate(model_point(u0 + 0.5, v0 + 0.5), yaw, pitch),
                rotate(model_point(u0, v0 + 0.5), yaw, pitch),
            };
            array<Vec2, 4> screen;
            double depth = 0.0;
            for (size_t i = 0; i < rotated_corners.size(); ++i) {
                screen[i] = project(rotated_corners[i], scale, origin);
                depth += rotated_corners[i].z;
            }
            depth /= static_cast<double>(rotated_corners.size());

            out.push_back(StickerDraw{
                screen, sticker_color(sticker_at(state, face.face, u_sign, v_sign)),
                depth});
        }
    }
}

void draw_cube_3d(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height,
    const CubeState& state, double yaw, double pitch,
    const TurnAnimation* animation) {
    const double scale = min(width, height) * 0.28;
    const Vec2 origin{width / 2.0, height / 2.0};

    vector<StickerDraw> stickers;
    stickers.reserve(24);
    for (const auto& face : cube_faces()) {
        collect_face_stickers(face, state, yaw, pitch, scale, origin, animation, stickers);
    }

    // 画家算法：按深度从远到近画——现在是全部待画贴纸一起排序，不是
    // 先按面分组、组内固定顺序，动画中的格子才能正确插到该在的前后
    // 位置。
    sort(stickers.begin(), stickers.end(), [](const StickerDraw& a, const StickerDraw& b) {
        return a.depth < b.depth;
    });

    for (const auto& sticker : stickers) {
        fill_grid_cell(cr, sticker.screen, sticker.color);
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

Gtk::Widget* make_cube_3d_view(
    function<CubeState()> state_provider, int size,
    function<optional<TurnAnimation>()> animation_provider) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(size);
    area->set_content_height(size);

    // 初始视角：能同时看到 U/F/R 三个面——是俯视（视线从上往下看，能
    // 看见顶面 U），不是仰视。pitch 必须取正值：draw_cube_3d() 的可见
    // 性判断是“旋转后 z 分量为正才画”，而 rotate() 对 U 面法向量
    // (0,1,0) 算出的 z 分量正好是 sin(pitch)——pitch 为负会让 U 面转
    // 到背面被剔除、露出对面的 D，看起来就成了仰视（此前这里错写成了
    // 负值，见 review 记录）。
    auto yaw = make_shared<double>(-M_PI / 4);
    auto pitch = make_shared<double>(M_PI / 6.5);

    area->set_draw_func(
        [state_provider, animation_provider, yaw, pitch](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const optional<TurnAnimation> animation =
                animation_provider ? animation_provider() : nullopt;
            draw_cube_3d(
                cr, width, height, state_provider(), *yaw, *pitch,
                animation ? &*animation : nullptr);
        });

    // 鼠标拖拽旋转：拖动过程中的位移量换算成 yaw/pitch 增量；俯仰角
    // 限制在正负约 75°，避免转到正对某条棱、视觉上完全失去立体感。
    // pitch 是 +offset_y（不是 -offset_y）：手指往上拖，应该像用手指
    // 从下往上托着魔方底部一样，把底面往观察者方向翻上来、露出更多
    // 顶面，符合“拖拽=用手指推动物体表面朝同一方向走”这个直觉；原来
    // 写成减号，上下方向是反的（左右方向的 yaw 本来就没有这个问题）。
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
            *pitch = clamp(*drag_start_pitch + offset_y * sensitivity, -1.3, 1.3);
            area->queue_draw();
        });
    area->add_controller(drag);
    area->set_cursor("grab");
    area->set_tooltip_text("按住拖动可以旋转查看");

    return area;
}

Gtk::Widget* make_cube_net_view(
    function<CubeState()> state_provider, int width, int height) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(width);
    area->set_content_height(height);
    area->set_draw_func(
        [state_provider](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_cube_net(cr, width, height, state_provider());
        });
    area->set_tooltip_text("六面展开图：六个面一次性摊开，没有遮挡");
    return area;
}
