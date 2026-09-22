#include "pocket_cube/view.h"

#include "color.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <numbers>
#include <optional>
#include <string>
#include <utility>
#include <vector>

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

// 每个贴纸的调试编号——数字集合跟"状态空间"环形图节点编号是同一套
// （绿=2/4/6/8、蓝=1/3/5/7、橙=10/12/14/16、红=9/11/13/15、
// 黄=17/19/21/23，U 面白色没有对应的环节点颜色，借用剩下没用到的
// 黑色那组 18/20/22/24）。编号绑定的是贴纸本身（参照已复原状态时它
// 在展开图上的位置），不是画面上的槽位——魔方转动之后同一张贴纸会
// 换到别的槽位，编号跟着贴纸一起换过去，不会留在原地；调用方传入
// 的 face/u_sign/v_sign 已经是 sticker_home() 转换过的"贴纸原始槽位"，
// 不是当前槽位。
int sticker_label(Face face, int u_sign, int v_sign) {
    constexpr array<int, 4> kU{18, 20, 22, 24};
    constexpr array<int, 4> kD{17, 19, 21, 23};
    constexpr array<int, 4> kF{2, 4, 6, 8};
    constexpr array<int, 4> kB{1, 3, 5, 7};
    constexpr array<int, 4> kL{10, 12, 14, 16};
    constexpr array<int, 4> kR{9, 11, 13, 15};
    const int idx = (v_sign > 0 ? 2 : 0) + (u_sign > 0 ? 1 : 0);
    switch (face) {
    case Face::U: return kU[idx];
    case Face::D: return kD[idx];
    case Face::F: return kF[idx];
    case Face::B: return kB[idx];
    case Face::L: return kL[idx];
    case Face::R: return kR[idx];
    }
    return 0;
}

// 在格子中心画编号文字——用 get_text_extents() 量出文字包围盒再居中，
// 不是凭经验挪偏移量，格子大小变化时数字始终居中。
void draw_cell_label(
    const Cairo::RefPtr<Cairo::Context>& cr, const Vec2& center, int label,
    double font_size) {
    cairo_select_font_face(
        cr->cobj(), "sans-serif", CAIRO_FONT_SLANT_NORMAL,
        CAIRO_FONT_WEIGHT_BOLD);
    cr->set_font_size(font_size);
    const string text = to_string(label);
    Cairo::TextExtents extents;
    cr->get_text_extents(text, extents);
    cr->move_to(
        center.x - extents.width / 2.0 - extents.x_bearing,
        center.y - extents.height / 2.0 - extents.y_bearing);
    cr->set_source_rgba(0, 0, 0, 0.75);
    cr->show_text(text);
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
    const double radians = degrees * std::numbers::pi / 180.0;
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
    int label;
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

            const StickerHome home = sticker_home(state, face.face, u_sign, v_sign);
            out.push_back(StickerDraw{
                screen, sticker_color(sticker_at(state, face.face, u_sign, v_sign)),
                depth, sticker_label(home.face, home.u_sign, home.v_sign)});
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

    const double label_font_size = max(8.0, scale * 0.16);
    for (const auto& sticker : stickers) {
        fill_grid_cell(cr, sticker.screen, sticker.color);
        Vec2 center{0, 0};
        for (const auto& corner : sticker.screen) {
            center.x += corner.x / sticker.screen.size();
            center.y += corner.y / sticker.screen.size();
        }
        draw_cell_label(cr, center, sticker.label, label_font_size);
    }
}

// 展开图每一格该查 sticker_at()/sticker_home() 的哪个 (u_sign, v_sign)，
// 不能直接照搬屏幕格子的 (ui, vi)——face_layout() 的 u_axis/v_axis 是给
// "状态怎么存"用的空间坐标系，对六个面各自独立定义，并不是为"摊平在
// 十字形网格里、边跟边要对得上物理折叠关系"这件事设计的。以 F 为例：
// F 与 U 的公共棱是 F 的 v(=Y)=+1 那条边，十字形网格里 U 画在 F 上方，
// 这条棱理应落在 F 格子的顶排，但 v_sign=+1 直接映射到屏幕下排（vi=1）
// 会把它画到底排——跟正上方的 U 对不上，物理折叠不起来。L/R 更极端：
// 它们的 u_axis 是 Y（上下）、v_axis 是 Z（前后），如果照搬 ui→u_sign、
// vi→v_sign，就是把"上下"画成了格子的左右列、"前后"画成了格子的
// 上下行——整个转了 90°。下面这套映射是按标准十字形展开图（F 不转、
// U/D/L/R/B 各自绕与 F 的公共棱转 90° 摊平）实际算出来的，跟 3D 视图
// （collect_face_stickers()，靠真正的 3D 投影，不存在这个问题）能对上：
// 比如修好之后 F 顶排是 6、8，R 顶排是 15、11，横着读正好是
// "6 8 15 11"，不是当前 (ui,vi) 直接套 (u_sign,v_sign) 时算出来的
// "6 8 13 15"。
void net_cell_sign(Face face, int ui, int vi, int& u_sign, int& v_sign) {
    const int a = ui * 2 - 1;
    const int b = vi * 2 - 1;
    switch (face) {
    case Face::U: u_sign = a; v_sign = b; break;
    case Face::D: u_sign = a; v_sign = -b; break;
    case Face::F: u_sign = a; v_sign = -b; break;
    case Face::B: u_sign = -a; v_sign = -b; break;
    case Face::L: u_sign = -b; v_sign = a; break;
    case Face::R: u_sign = -b; v_sign = -a; break;
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
                int u_sign = 0;
                int v_sign = 0;
                net_cell_sign(face, ui, vi, u_sign, v_sign);
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
                const Vec2 center{
                    origin_x + (ui + 0.5) * cell / 2, origin_y + (vi + 0.5) * cell / 2};
                const StickerHome home = sticker_home(state, face, u_sign, v_sign);
                draw_cell_label(
                    cr, center, sticker_label(home.face, home.u_sign, home.v_sign),
                    cell * 0.32);
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

// 一组同心圆的两个半径比例（相对 max_radius）——内圈 0.62、外圈 1.0，
// 三组共用同一套比例（"同样大小方式"），画在不同圆心上。
constexpr double kInnerRadiusRatio = 0.72;
constexpr double kOuterRadiusRatio = 1.0;
constexpr double kRingLineWidth = 5.5; // 线宽些，参考视频里那种粗环

struct RingGroupSpec {
    Vec2 origin;
    ChartColor inner_color;
    ChartColor outer_color;
};

void draw_ring_group(
    const Cairo::RefPtr<Cairo::Context>& cr, const RingGroupSpec& group,
    double max_radius) {
    const array<pair<double, ChartColor>, 2> rings = {{
        {kInnerRadiusRatio, group.inner_color},
        {kOuterRadiusRatio, group.outer_color},
    }};
    for (const auto& [ratio, color] : rings) {
        cr->set_source_rgba(color.r, color.g, color.b, 0.9);
        cr->set_line_width(kRingLineWidth);
        cr->arc(
            group.origin.x, group.origin.y, max_radius * ratio, 0,
            2 * std::numbers::pi);
        cr->stroke();
    }
}

// 三组同心圆，圆心呈"奔驰标"式三等分布（各间隔 120°），整体绕公共
// 中心 M 慢慢转（phase 每帧递增）——三点始终两两等距（等边三角形绕
// 自己外接圆心转动，边长不变），所以"两圆有两个交点"这条件不会因为
// 转动而在某个瞬间失效，24 个交点全程都在。
constexpr double kCenterDistanceRatio = 0.8; // 相对 max_radius；(ro-ri, 2ri) = (0.38, 1.24)，取中段的 0.8
constexpr double kOrbitRatio =
    kCenterDistanceRatio / 1.7320508075688772; // /√3：三点两两间距 = 轨道半径×√3

// 反解 max_radius：整幅图（三个圆心的轨道 + 各自外圈半径）转动起来
// 会扫出一个以 M 为圆心、半径 = orbit_radius + max_radius 的圆盘，
// 这个圆盘必须整个落在画布内，否则转到某些角度时就会有圆弧被裁掉
// （固定角度时按"上/左下/右下"分别核算边界的算法，一转动就不成立了，
// 换成转动无关的各向同性上界）。
double solve_max_radius(int width, int height, const Vec2& center) {
    const double nearest_edge =
        min({center.x, width - center.x, center.y, height - center.y});
    return 0.9 * nearest_edge / (1.0 + kOrbitRatio);
}

// 标准两圆求交点公式：圆心距超出 [|r1-r2|, r1+r2] 时无解（不该发生在
// 我们这 12 对圆上，因为 kCenterDistanceRatio 已经保证落在区间内，
// 但公式本身对任意输入负责，返回 optional 而不是假设调用方一定合法）。
optional<pair<Vec2, Vec2>> circle_intersections(
    const Vec2& c1, double r1, const Vec2& c2, double r2) {
    const double dx = c2.x - c1.x;
    const double dy = c2.y - c1.y;
    const double d = sqrt(dx * dx + dy * dy);
    if (d < 1e-9 || d > r1 + r2 || d < abs(r1 - r2)) {
        return nullopt;
    }
    const double a = (r1 * r1 - r2 * r2 + d * d) / (2 * d);
    const double h = sqrt(max(0.0, r1 * r1 - a * a));
    const Vec2 p{c1.x + a * dx / d, c1.y + a * dy / d};
    return make_pair(
        Vec2{p.x + h * dy / d, p.y - h * dx / d},
        Vec2{p.x - h * dy / d, p.y + h * dx / d});
}

// 两组同心圆（各 2 个圆）两两组合出的 4 对圆，各自最多 2 个交点，
// 按"g1/g2 各自哪一圈参与"拆成 4 个原始子列表——ii=g1 内×g2 内，
// io=g1 内×g2 外，oi=g1 外×g2 内，oo=g1 外×g2 外。拆到这个粒度是
// 因为"哪一环转动"要按"活动组自己的外圈是否参与"来判断，活动组
// 可能是 g1 也可能是 g2，只有拆到 4 个原始子列表才能两种情况都
// 处理（见 draw_state_space_rings() 的用法：先按需要旋转某些子
// 列表，再合并成 g1_outer/g1_inner 两组配色用）。
struct PairIntersections {
    vector<Vec2> inner_inner;
    vector<Vec2> inner_outer;
    vector<Vec2> outer_inner;
    vector<Vec2> outer_outer;
};

PairIntersections collect_pair_intersections(
    const RingGroupSpec& g1, const RingGroupSpec& g2, double max_radius) {
    const double ri = max_radius * kInnerRadiusRatio;
    const double ro = max_radius * kOuterRadiusRatio;
    const auto add = [](vector<Vec2>& out, optional<pair<Vec2, Vec2>> pts) {
        if (pts) {
            out.push_back(pts->first);
            out.push_back(pts->second);
        }
    };
    PairIntersections result;
    add(result.inner_inner, circle_intersections(g1.origin, ri, g2.origin, ri));
    add(result.inner_outer, circle_intersections(g1.origin, ri, g2.origin, ro));
    add(result.outer_inner, circle_intersections(g1.origin, ro, g2.origin, ri));
    add(result.outer_outer, circle_intersections(g1.origin, ro, g2.origin, ro));
    return result;
}

// 把点 p 绕 center 转 delta_radians（标准数学定义，逆时针为正），
// 半径（到 center 的距离）保持不变——"环绕自己圆心旋转"就是拿这个
// 函数对落在这个环上的交点做的，不重新算两个圆的真实几何交点，故意
// 忽略旋转过程中跟另一个环的真实距离关系（只有静止角度 0 时才代表
// 真交点，动画中间帧只是视觉上的"跟着转"）。
Vec2 rotate_around(const Vec2& p, const Vec2& center, double delta_radians) {
    const double dx = p.x - center.x;
    const double dy = p.y - center.y;
    const double radius = sqrt(dx * dx + dy * dy);
    const double angle = atan2(dy, dx) + delta_radians;
    return Vec2{center.x + radius * cos(angle), center.y + radius * sin(angle)};
}

// 编号是临时调试手段：截图配色时肉眼没法准确对应"这几个点具体是哪
// 种几何组合"，编号之后可以直接说"3、7、12 号统一红色"，不会认错
// 点。确认最终配色方案之后这个标号可以整个删掉，不是长期要留的
// 功能。一个点一份颜色（不再是"一组 4 个点共用一色"），因为实际
// 反馈是按编号单点指定的，不是按"外圈/内圈"这种整组指定的。
void draw_node(
    const Cairo::RefPtr<Cairo::Context>& cr, const Vec2& p,
    const ChartColor& color, double node_radius, int label) {
    // arc() 不会自己开新路径——如果上一个点画完文字之后 current point
    // 留在文字末尾，arc() 会先从那里画一条线连过来。每个点开始前显式
    // 起个新路径，断开这条隐式连线。
    cr->begin_new_path();
    cr->arc(p.x, p.y, node_radius, 0, 2 * std::numbers::pi);
    cr->set_source_rgb(color.r, color.g, color.b);
    cr->fill_preserve();
    // 深色描边让节点在浅色环线上更"明显"，不是纯色块糊在一起。
    cr->set_source_rgba(0, 0, 0, 0.35);
    cr->set_line_width(1.0);
    cr->stroke();

    // cairomm 不同版本的字体粗细/斜体枚举名不稳定，直接用底层 C API
    // 绕开（cairomm::Context::cobj() 拿原始 cairo_t*），避免猜命名空间。
    cairo_select_font_face(
        cr->cobj(), "sans-serif", CAIRO_FONT_SLANT_NORMAL,
        CAIRO_FONT_WEIGHT_BOLD);
    cr->set_font_size(max(10.0, node_radius * 1.1));
    cr->set_source_rgb(0, 0, 0);
    cr->move_to(p.x + node_radius + 2, p.y - node_radius - 2);
    cr->show_text(to_string(label));
}

// 三组圆的静止角度（弧度，标准数学定义，从正 x 轴逆时针为正）：上
// （U）在 -90°，左下（R）、右下（F）各偏 ±120°，跟 draw_ring_group()
// 里 groups 数组的下标一一对应（0=上/U, 1=左下/R, 2=右下/F），
// RingAnimation::active_group 也用这套下标，两边不会对不上。
constexpr double kGroupRestAngle[3] = {
    -std::numbers::pi / 2.0,
    -std::numbers::pi / 2.0 + 2.0 * std::numbers::pi / 3.0,
    -std::numbers::pi / 2.0 - 2.0 * std::numbers::pi / 3.0,
};

void draw_state_space_rings(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height,
    const RingAnimation* animation) {
    // 靠上一点：公共中心 M 的 y 取高度的 0.42 而不是正中间 0.5。
    const Vec2 center{width / 2.0, height * 0.42};
    const double max_radius = solve_max_radius(width, height, center);
    const double orbit_radius = max_radius * kOrbitRatio;

    // 圆心永远停在静止角度——"旋转"不是圆心绕公共中心 M 公转，是圆
    // 自己的 8 个交点绕这个圆自己的圆心转（见下面 group_pairs 循环），
    // 圆心本身不用动画状态。
    const auto orbit_point = [&](int group_index) {
        const double angle = kGroupRestAngle[group_index];
        return Vec2{
            center.x + orbit_radius * cos(angle),
            center.y + orbit_radius * sin(angle)};
    };

    // 同一组的内外两环改成同一个颜色——组内颜色一致，一眼就能看出
    // 6 个圆分属哪 3 组，不需要再靠"内圈/外圈"这层区分去认颜色。原来
    // 上/左下两组用的橙、绿（0xffc48a/0xa7ddb6）跟节点配色表里的饱和
    // 橙(0xF39C12)、饱和绿(0x27AE60) 同色系，容易把"环本身的颜色"和
    // "交点的颜色"看混——换成节点配色表里完全没用到的淡青、淡粉，
    // 右下角的淡紫本来就没跟任何节点颜色撞，不用动。
    const array<RingGroupSpec, 3> groups = {{
        {orbit_point(0), chart_color(0x9AD6D6), chart_color(0x9AD6D6)},
        {orbit_point(1), chart_color(0xF0AFC7), chart_color(0xF0AFC7)},
        {orbit_point(2), chart_color(0xc9a8e8), chart_color(0xc9a8e8)},
    }};

    for (const auto& group : groups) {
        draw_ring_group(cr, group, max_radius);
    }

    // 24 个交点的配色，按编号（1~24，见 draw_node() 标出来的号）直接
    // 指定——反馈是按单点编号给的（比如"10 12 14 16 用红色"），不是
    // 按"外圈/内圈"整组给的，量到这个粒度就不适合再按组配色了，直接
    // 用一张编号表最不容易认错点。(0,1)（橙×绿）单数(1/3/5/7)=蓝、
    // 双数(2/4/6/8)=绿；(0,2)（橙×紫）单数(9/11/13/15)=红、双数
    // (10/12/14/16)=橙——这两对都来回改过好几次，以这版编号表为准；
    // (1,2)（绿×紫）单数(17/19/21/23)=黄、双数(18/20/22/24)=黑（原则
    // 上该用白色，但白色在浅色背景上不合适，换成黑色）。
    constexpr array<ChartColor, 24> kLabelColors = {{
        chart_color(0x2E86DE), chart_color(0x27AE60), chart_color(0x2E86DE),
        chart_color(0x27AE60), chart_color(0x2E86DE), chart_color(0x27AE60),
        chart_color(0x2E86DE), chart_color(0x27AE60), // 1-8: (0,1)，单蓝双绿
        chart_color(0xE74C3C), chart_color(0xF39C12), chart_color(0xE74C3C),
        chart_color(0xF39C12), chart_color(0xE74C3C), chart_color(0xF39C12),
        chart_color(0xE74C3C), chart_color(0xF39C12), // 9-16: (0,2)，单红双橙
        chart_color(0xF1C40F), chart_color(0x1A1A1A), chart_color(0xF1C40F),
        chart_color(0x1A1A1A), chart_color(0xF1C40F), chart_color(0x1A1A1A),
        chart_color(0xF1C40F), chart_color(0x1A1A1A), // 17-24: (1,2)，单黄双黑
    }};
    const double node_radius = max(5.0, max_radius * 0.055);
    const array<pair<int, int>, 3> group_pairs = {{{0, 1}, {0, 2}, {1, 2}}};

    // 每个点标一下"落在 i 的外圈还是内圈上""落在 j 的外圈还是内圈
    // 上"——活动组可能是这一对里的 i 也可能是 j，只有点一级记清楚
    // 两边各自的内外归属，才能不管活动组是谁都能正确判断"这个点该不
    // 该跟着转"（只转活动组自己外圈参与的点，见下面 spin 那段）。
    struct LabeledPoint {
        Vec2 pos;
        bool i_outer;
        bool j_outer;
    };

    int label = 1;
    for (const auto& [i, j] : group_pairs) {
        PairIntersections pts = collect_pair_intersections(groups[i], groups[j], max_radius);

        vector<LabeledPoint> points;
        const auto append = [&](vector<Vec2>& src, bool i_outer, bool j_outer) {
            for (auto& p : src) {
                points.push_back({p, i_outer, j_outer});
            }
        };
        append(pts.outer_inner, true, false);
        append(pts.outer_outer, true, true);
        append(pts.inner_inner, false, false);
        append(pts.inner_outer, false, true);

        if (animation) {
            const int active = animation->active_group;
            const Vec2& pivot = groups[active].origin;
            const double delta = animation->angle_offset_radians;
            for (auto& lp : points) {
                const bool active_outer_here =
                    (active == i && lp.i_outer) || (active == j && lp.j_outer);
                if (active_outer_here) {
                    lp.pos = rotate_around(lp.pos, pivot, delta);
                }
            }
        }

        for (const auto& lp : points) {
            draw_node(cr, lp.pos, kLabelColors[label - 1], node_radius, label);
            ++label;
        }
    }
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
    auto yaw = make_shared<double>(-std::numbers::pi / 4);
    auto pitch = make_shared<double>(std::numbers::pi / 6.5);

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

// 只画一个面的 2x2 格子，没有透视、不用背面剔除——跟 draw_cube_net()
// 里单个面那块用的是同一个 net_cell_sign()，数字跟展开图上那一块的
// 编号完全一致，不是另起一套。
void draw_cube_face(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height,
    const CubeState& state, Face face) {
    const double cell = min(width / 2.0, height / 2.0);
    const double margin_x = (width - cell * 2) / 2;
    const double margin_y = (height - cell * 2) / 2;
    for (int ui = 0; ui < 2; ++ui) {
        for (int vi = 0; vi < 2; ++vi) {
            int u_sign = 0;
            int v_sign = 0;
            net_cell_sign(face, ui, vi, u_sign, v_sign);
            const double origin_x = margin_x + ui * cell;
            const double origin_y = margin_y + vi * cell;
            const array<Vec2, 4> screen = {
                Vec2{origin_x, origin_y},
                Vec2{origin_x + cell, origin_y},
                Vec2{origin_x + cell, origin_y + cell},
                Vec2{origin_x, origin_y + cell},
            };
            fill_grid_cell(cr, screen, sticker_color(sticker_at(state, face, u_sign, v_sign)));
            const Vec2 center{origin_x + cell / 2, origin_y + cell / 2};
            const StickerHome home = sticker_home(state, face, u_sign, v_sign);
            draw_cell_label(
                cr, center, sticker_label(home.face, home.u_sign, home.v_sign),
                cell * 0.32);
        }
    }
}

Gtk::Widget* make_cube_face_view(
    function<CubeState()> state_provider, Face face, int width, int height) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(width);
    area->set_content_height(height);
    area->set_draw_func(
        [state_provider, face](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_cube_face(cr, width, height, state_provider(), face);
        });
    return area;
}

Gtk::Widget* make_state_space_rings_view(
    long long state_space_size, int size,
    function<optional<RingAnimation>()> animation_provider) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    // content_width/height 只是"最小自然尺寸"，不是固定尺寸——真正
    // 决定画多大的是 draw_func 每次拿到的 width/height（由 GTK 布局
    // 分配决定），draw_state_space_rings() 本来就是按这两个参数动态
    // 反解半径，不是按固定像素画的，所以这里放开 hexpand/vexpand 让
    // 它跟着所在的 Frame 一起变大，配合 window.blp 里 host 容器改成
    // halign/valign: fill，才能在窗口开大时图像跟着放大，而不是固定
    // 320×320 缩在一个大面板中间，四周全是空的。
    area->set_content_width(size);
    area->set_content_height(size);
    area->set_hexpand(true);
    area->set_vexpand(true);

    // 静止时不转——只有对应面的按钮点下去、animation_provider() 返回
    // 非空的那段时间，对应那一组圆才会偏离静止角度；平时三组都停在
    // kGroupRestAngle 定义的位置。拉模型跟 make_cube_3d_view() 的
    // animation_provider 同一套用法。
    area->set_draw_func(
        [animation_provider](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const optional<RingAnimation> animation =
                animation_provider ? animation_provider() : nullopt;
            draw_state_space_rings(
                cr, width, height, animation ? &*animation : nullptr);
        });

    area->set_tooltip_text(
        "状态空间约有 " + to_string(state_space_size) + " 种");

    return area;
}
