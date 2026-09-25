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

Vec3 operator+(const Vec3& a, const Vec3& b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
Vec3 operator-(const Vec3& a, const Vec3& b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
Vec3 operator*(const Vec3& a, double k) { return {a.x * k, a.y * k, a.z * k}; }
double dot(const Vec3& a, const Vec3& b) { return a.x * b.x + a.y * b.y + a.z * b.z; }

Vec3 normalized(const Vec3& a) {
    const double n = sqrt(dot(a, a));
    return n > 0 ? a * (1.0 / n) : a;
}

constexpr array<Axis, 3> kAxes{Axis::X, Axis::Y, Axis::Z};

double component(const Vec3& p, Axis axis) {
    switch (axis) {
    case Axis::X: return p.x;
    case Axis::Y: return p.y;
    case Axis::Z: return p.z;
    }
    return 0;
}

Vec3 axis_unit(Axis axis) {
    switch (axis) {
    case Axis::X: return {1, 0, 0};
    case Axis::Y: return {0, 1, 0};
    case Axis::Z: return {0, 0, 1};
    }
    return {};
}

// 法向轴 + 朝向唯一确定一个面；反查 face_layout()，不另写一张对照表。
Face face_on(Axis axis, int sign) {
    for (Face face : {Face::U, Face::D, Face::L, Face::R, Face::F, Face::B}) {
        const FaceLayout layout = face_layout(face);
        if (layout.normal_axis == axis && layout.normal_sign == sign) {
            return face;
        }
    }
    return Face::U;
}

// 绕 Y 轴转 yaw、再绕 X 轴转 pitch：世界坐标 → 观察坐标（z 朝向观察者）。
// yaw 绕的是世界竖直轴，所以拖动是“转台”式环绕，地面始终水平。
Vec3 rotate(const Vec3& p, double yaw, double pitch) {
    const double x1 = p.x * cos(yaw) + p.z * sin(yaw);
    const double z1 = -p.x * sin(yaw) + p.z * cos(yaw);
    const double y1 = p.y;
    const double y2 = y1 * cos(pitch) - z1 * sin(pitch);
    const double z2 = y1 * sin(pitch) + z1 * cos(pitch);
    return {x1, y2, z2};
}

// rotate() 的逆变换：观察坐标 → 世界坐标，用来求相机在世界里的位置。
Vec3 unrotate(const Vec3& p, double yaw, double pitch) {
    const double y1 = p.y * cos(pitch) + p.z * sin(pitch);
    const double z1 = -p.y * sin(pitch) + p.z * cos(pitch);
    return {p.x * cos(yaw) - z1 * sin(yaw), y1, p.x * sin(yaw) + z1 * cos(yaw)};
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

// ===== 3D 视图：8 个角块实体 + 光照 + 地面投影 =====
//
// 立体感靠的是单眼线索（遮挡、透视、明暗、阴影、转动），普通屏幕全都
// 给得出来，不需要 VR：
// - 每个角块是一个深色塑料块体，贴纸内缩贴在外表面上，块与块之间留缝，
//   转动时露出块体侧面——遮挡关系和“这是实心块”的印象都来自这里；
// - 轻度透视，近大远小；
// - 主光固定在世界坐标里，拖动视角时各面明暗随之变化（转动中的明暗
//   变化是最强的形状线索），另有一盏跟着相机走的补光，保证正对观察者
//   的面不会黑掉；
// - 魔方悬在地面上方，沿主光方向投下软阴影，地面网格给出水平参照。
//
// 不动点：2 阶魔方只转 U/R/F（next_move_set()），D/L/B 交界的那个角块
// 从头到尾不动。这里把它画成“支在一根立柱上”——立柱在那个角块正下方，
// U/R/F 三个转动层在几何上都碰不到它，画面本身就说明了这个约定。

constexpr double kCubieHalf = 0.485;     // 角块半边长；相邻两块之间留 0.03 的缝
constexpr double kStickerHalf = 0.40;    // 贴纸半边长，四周露出一圈块体
constexpr double kStickerChamfer = 0.10; // 贴纸切角，读起来像实物贴纸而不是色块
constexpr double kFloorY = -2.05;        // 地面高度：魔方悬空，阴影与本体分开，默认视角能从底下看到立柱
constexpr double kFloorRadius = 2.0;
constexpr double kCameraDistance = 7.5;  // 越小透视越强；7.5 ≈ 中长焦，不变形
constexpr double kStandRadius = 0.08;

// 不动的那个角块：D/L/B 交界，坐标符号 (-1,-1,-1)，见 state.h next_move_set()。
constexpr array<int, 3> kFixedCubie{-1, -1, -1};

// 主光从左上前方打过来：默认视角下 U 最亮、F 次之、R 最暗，三个可见面
// 明暗分明；阴影落在右后方，从默认视角看得到。
const Vec3 kKeyLight = normalized({-0.5, 1.0, 0.45});
// 配色本身是淡色，明暗只在 [0.7, 1] 左右浮动：乘得太狠淡色会发灰发脏。
constexpr double kAmbient = 0.62;
constexpr double kKeyStrength = 0.38;
constexpr double kFillStrength = 0.12;

constexpr ChartColor kBodyColor = chart_color(0x2a2a31);

struct Camera {
    double yaw;
    double pitch;
    double scale;
    Vec2 origin;
    Vec3 eye; // 相机在世界坐标里的位置

    Camera(double yaw_, double pitch_, double scale_, Vec2 origin_)
        : yaw(yaw_), pitch(pitch_), scale(scale_), origin(origin_),
          eye(unrotate({0, 0, kCameraDistance}, yaw_, pitch_)) {}

    // 透视缩放系数：观察坐标 z 越大（越近）越大，z=0 处恰好是 1。
    double perspective(const Vec3& world) const {
        return kCameraDistance / (kCameraDistance - rotate(world, yaw, pitch).z);
    }

    Vec2 project(const Vec3& world) const {
        const Vec3 v = rotate(world, yaw, pitch);
        const double f = kCameraDistance / (kCameraDistance - v.z);
        // 屏幕 y 向下为正，3D 的 y 向上为正，取反。
        return {origin.x + v.x * scale * f, origin.y - v.y * scale * f};
    }

    bool faces_camera(const Vec3& point, const Vec3& normal) const {
        return dot(normal, eye - point) > 0;
    }
};

ChartColor scaled(const ChartColor& c, double k, double add = 0) {
    return {
        clamp(c.r * k + add, 0.0, 1.0), clamp(c.g * k + add, 0.0, 1.0),
        clamp(c.b * k + add, 0.0, 1.0)};
}

// Lambert 漫反射（主光 + 补光）+ Blinn-Phong 高光。按面平涂：块面是
// 平面，逐像素算和逐面算结果一样，Cairo 也没有逐像素着色。
ChartColor shade(
    const ChartColor& base, const Vec3& normal, const Vec3& point, const Camera& camera,
    double gloss) {
    const Vec3 to_eye = normalized(camera.eye - point);
    const double diffuse = kAmbient + kKeyStrength * max(0.0, dot(normal, kKeyLight)) +
                           kFillStrength * max(0.0, dot(normal, to_eye));
    const Vec3 half = normalized(kKeyLight + to_eye);
    const double specular = gloss * pow(max(0.0, dot(normal, half)), 40.0);
    return scaled(base, diffuse, specular);
}

void fill_polygon(
    const Cairo::RefPtr<Cairo::Context>& cr, const vector<Vec2>& points,
    const ChartColor& color) {
    cr->begin_new_path();
    cr->move_to(points[0].x, points[0].y);
    for (size_t i = 1; i < points.size(); ++i) {
        cr->line_to(points[i].x, points[i].y);
    }
    cr->close_path();
    cr->set_source_rgb(color.r, color.g, color.b);
    // 同色细描边盖住相邻多边形之间的抗锯齿接缝，否则块面之间会透出背景细线。
    cr->fill_preserve();
    cr->set_line_width(0.8);
    cr->stroke();
}

// 某个角块在转动动画里的刚体变换：属于正在转的那一层就绕层轴转到当前
// 角度，否则原样返回。点和法向量都走这一个函数。
struct CubieTransform {
    const TurnAnimation* animation = nullptr;

    Vec3 operator()(const Vec3& p) const {
        return animation ? rotate_around_axis(p, animation->axis, animation->current_degrees)
                         : p;
    }
};

// 角块 pos 在第 a 根轴上朝外那张贴纸所在的槽位：面由轴和坐标符号决定，
// 面内格子由 face_layout() 的 u/v 轴取同一个 pos 的符号。3D 块体和拓扑
// 图都按这个查颜色，两边不会对不上。
struct StickerSlot {
    Face face;
    int u_sign;
    int v_sign;
};

StickerSlot outward_slot(const array<int, 3>& pos, size_t a) {
    const Face face = face_on(kAxes[a], pos[a]);
    const FaceLayout layout = face_layout(face);
    return {
        face, pos[static_cast<size_t>(layout.u_axis)],
        pos[static_cast<size_t>(layout.v_axis)]};
}

// 画一个角块：块体 6 个面里朝向相机的那几个（凸体，彼此不遮挡，不用
// 排序），外表面再贴上贴纸和编号。
void draw_cubie(
    const Cairo::RefPtr<Cairo::Context>& cr, const CubeState& state,
    const array<int, 3>& pos, const CubieTransform& transform, const Camera& camera) {
    const Vec3 center{pos[0] * 0.5, pos[1] * 0.5, pos[2] * 0.5};
    for (size_t a = 0; a < kAxes.size(); ++a) {
        const Axis axis = kAxes[a];
        const Axis tangent_b = kAxes[(a + 1) % 3];
        const Axis tangent_c = kAxes[(a + 2) % 3];
        for (int sign : {-1, 1}) {
            const Vec3 normal = transform(axis_unit(axis) * sign);
            const Vec3 face_center = transform(center + axis_unit(axis) * (sign * kCubieHalf));
            if (!camera.faces_camera(face_center, normal)) {
                continue;
            }
            // 面内一点：(b, c) 是沿两根切向轴、相对面中心的偏移。
            const auto face_point = [&](double b, double c) {
                return transform(
                    center + axis_unit(axis) * (sign * kCubieHalf) + axis_unit(tangent_b) * b +
                    axis_unit(tangent_c) * c);
            };

            vector<Vec2> body;
            for (const auto& [b, c] :
                 {pair{-1, -1}, pair{1, -1}, pair{1, 1}, pair{-1, 1}}) {
                body.push_back(camera.project(face_point(b * kCubieHalf, c * kCubieHalf)));
            }
            fill_polygon(cr, body, shade(kBodyColor, normal, face_center, camera, 0.18));

            // 只有朝外的那一面（朝向跟角块自己在这根轴上的坐标符号一致）才有贴纸。
            if (sign != pos[a]) {
                continue;
            }
            const auto [face, u_sign, v_sign] = outward_slot(pos, a);

            // 切角八边形，逆时针走一圈。
            constexpr double s = kStickerHalf;
            constexpr double k = kStickerHalf - kStickerChamfer;
            vector<Vec2> sticker;
            for (const auto& [b, c] :
                 {pair{-k, -s}, pair{k, -s}, pair{s, -k}, pair{s, k}, pair{k, s}, pair{-k, s},
                  pair{-s, k}, pair{-s, -k}}) {
                sticker.push_back(camera.project(face_point(b, c)));
            }
            fill_polygon(
                cr, sticker,
                shade(sticker_color(sticker_at(state, face, u_sign, v_sign)), normal,
                      face_center, camera, 0.35));

            const StickerHome home = sticker_home(state, face, u_sign, v_sign);
            const double font_size =
                max(8.0, camera.scale * camera.perspective(face_center) * 0.15);
            draw_cell_label(
                cr, camera.project(face_center),
                sticker_label(home.face, home.u_sign, home.v_sign), font_size);
        }
    }
}

// 画家算法的排序键：8 个等大的块排成网格，对每根轴，跟相机不在同一侧
// 的那一块一定在后面；把三根轴的“远近”加起来排序就满足所有约束——两块
// 在某根轴上被分隔平面隔开时，相机那一侧的后画；如果两根分隔平面给出
// 相反结论，说明两块互不遮挡，谁先谁后都行。比按中心距离排序可靠：
// 透视下中心距离在块大小相近时会排错。
int far_to_near_key(const array<int, 3>& pos, const Vec3& eye) {
    int key = 0;
    for (size_t a = 0; a < kAxes.size(); ++a) {
        const double e = component(eye, kAxes[a]);
        key += pos[a] * (e > 0 ? 1 : (e < 0 ? -1 : 0));
    }
    return key;
}

void sort_far_to_near(vector<array<int, 3>>& cubies, const Vec3& eye) {
    sort(cubies.begin(), cubies.end(), [&](const auto& a, const auto& b) {
        return far_to_near_key(a, eye) < far_to_near_key(b, eye);
    });
}

// 立柱：从不动角块底面中心垂直落到地面。
Vec3 stand_top() { return {kFixedCubie[0] * 0.5, -1.0 + (0.5 - kCubieHalf), kFixedCubie[2] * 0.5}; }
Vec3 stand_bottom() { return {kFixedCubie[0] * 0.5, kFloorY, kFixedCubie[2] * 0.5}; }

void draw_stand(const Cairo::RefPtr<Cairo::Context>& cr, const Camera& camera) {
    const Vec2 top = camera.project(stand_top());
    const Vec2 bottom = camera.project(stand_bottom());
    const double width =
        2 * kStandRadius * camera.scale *
        camera.perspective((stand_top() + stand_bottom()) * 0.5);

    // 圆柱的明暗用横向线性渐变模拟：中间偏左一道亮带，两侧暗。
    double dx = bottom.x - top.x;
    double dy = bottom.y - top.y;
    const double len = max(1e-6, sqrt(dx * dx + dy * dy));
    dx /= len;
    dy /= len;
    const Vec2 perp{-dy * width / 2, dx * width / 2};
    const Vec2 mid{(top.x + bottom.x) / 2, (top.y + bottom.y) / 2};
    auto gradient = Cairo::LinearGradient::create(
        mid.x - perp.x, mid.y - perp.y, mid.x + perp.x, mid.y + perp.y);
    gradient->add_color_stop_rgb(0.0, 0.30, 0.31, 0.34);
    gradient->add_color_stop_rgb(0.35, 0.78, 0.79, 0.82);
    gradient->add_color_stop_rgb(1.0, 0.22, 0.23, 0.26);

    cr->begin_new_path();
    cr->move_to(top.x, top.y);
    cr->line_to(bottom.x, bottom.y);
    cr->set_source(gradient);
    cr->set_line_width(width);
    cr->set_line_cap(Cairo::Context::LineCap::BUTT);
    cr->stroke();
}

// 沿主光方向把世界坐标里的点压到地面上。
Vec3 project_to_floor(const Vec3& p) {
    const double t = (p.y - kFloorY) / kKeyLight.y;
    return {p.x - kKeyLight.x * t, kFloorY, p.z - kKeyLight.z * t};
}

// 平面点集的凸包（Andrew 单调链），在地面的 (x, z) 平面里算。
vector<Vec3> floor_convex_hull(vector<Vec3> points) {
    sort(points.begin(), points.end(), [](const Vec3& a, const Vec3& b) {
        return a.x < b.x || (a.x == b.x && a.z < b.z);
    });
    const auto cross = [](const Vec3& o, const Vec3& a, const Vec3& b) {
        return (a.x - o.x) * (b.z - o.z) - (a.z - o.z) * (b.x - o.x);
    };
    vector<Vec3> hull(points.size() * 2);
    size_t k = 0;
    for (size_t i = 0; i < points.size(); ++i) {
        while (k >= 2 && cross(hull[k - 2], hull[k - 1], points[i]) <= 0) --k;
        hull[k++] = points[i];
    }
    for (size_t i = points.size() - 1, t = k + 1; i > 0; --i) {
        while (k >= t && cross(hull[k - 2], hull[k - 1], points[i - 1]) <= 0) --k;
        hull[k++] = points[i - 1];
    }
    hull.resize(k > 0 ? k - 1 : 0);
    return hull;
}

// 地面上以原点正下方为圆心的一个圆，投影后的路径（留在 cr 里待填充）。
void trace_floor_circle(
    const Cairo::RefPtr<Cairo::Context>& cr, const Camera& camera, double radius) {
    cr->begin_new_path();
    constexpr int kSegments = 72;
    for (int i = 0; i <= kSegments; ++i) {
        const double t = 2 * std::numbers::pi * i / kSegments;
        const Vec2 p = camera.project({radius * cos(t), kFloorY, radius * sin(t)});
        i == 0 ? cr->move_to(p.x, p.y) : cr->line_to(p.x, p.y);
    }
    cr->close_path();
}

void draw_floor(const Cairo::RefPtr<Cairo::Context>& cr, const Camera& camera, double alpha) {
    // 几层同心圆叠出由中心向外淡出的地面，边缘不留生硬的圆圈。
    for (double ratio : {1.0, 0.82, 0.64, 0.46}) {
        trace_floor_circle(cr, camera, kFloorRadius * ratio);
        cr->set_source_rgba(0.45, 0.47, 0.52, 0.05 * alpha);
        cr->fill();
    }

    // 网格线只画在圆盘内：直线投影后仍是直线，两端算好直接连。
    cr->set_line_width(1.0);
    constexpr double kStep = 0.5;
    const double inner = kFloorRadius * 0.92;
    for (double v = -inner + fmod(inner, kStep); v <= inner; v += kStep) {
        const double half = sqrt(max(0.0, inner * inner - v * v));
        for (const auto& [a, b] :
             {pair{Vec3{v, kFloorY, -half}, Vec3{v, kFloorY, half}},
              pair{Vec3{-half, kFloorY, v}, Vec3{half, kFloorY, v}}}) {
            const Vec2 pa = camera.project(a);
            const Vec2 pb = camera.project(b);
            cr->begin_new_path();
            cr->move_to(pa.x, pa.y);
            cr->line_to(pb.x, pb.y);
            cr->set_source_rgba(0.40, 0.42, 0.48, 0.10 * alpha);
            cr->stroke();
        }
    }
}

// 软阴影：Cairo 没有模糊，用若干层“凸包 + 不同宽度的圆角描边”叠出
// 由内向外渐淡的半影。每层先画进一个不透明的 group 再整体按固定透明度
// 贴回去，填充和描边重叠的部分才不会被算两次。
//
// 阴影只落在地面圆盘上：整张阴影再用“圆盘由中心向外渐隐”的蒙版贴回去，
// 跟地面一起淡出。否则视角压低时透视会把影子拉得很长，越出取景框被
// 截断——圆盘本身已经计入取景包围框，贴在盘上的影子就永远完整。
void draw_shadow(
    const Cairo::RefPtr<Cairo::Context>& cr, const Camera& camera,
    const vector<Vec3>& caster_points, double alpha) {
    vector<Vec3> floor_points;
    floor_points.reserve(caster_points.size());
    for (const auto& p : caster_points) {
        floor_points.push_back(project_to_floor(p));
    }
    const vector<Vec3> hull = floor_convex_hull(floor_points);
    if (hull.size() < 3) {
        return;
    }

    const Vec2 stand_a = camera.project(project_to_floor(stand_top()));
    const Vec2 stand_b = camera.project(stand_bottom());
    const double stand_width =
        2 * kStandRadius * camera.scale * camera.perspective(stand_bottom());

    cr->push_group();
    constexpr int kLayers = 12;
    const double penumbra = camera.scale * 0.22;
    for (int i = kLayers; i >= 1; --i) {
        cr->push_group();
        cr->set_source_rgb(0.05, 0.06, 0.10);
        cr->begin_new_path();
        for (size_t j = 0; j < hull.size(); ++j) {
            const Vec2 p = camera.project(hull[j]);
            j == 0 ? cr->move_to(p.x, p.y) : cr->line_to(p.x, p.y);
        }
        cr->close_path();
        cr->set_line_join(Cairo::Context::LineJoin::ROUND);
        cr->fill_preserve();
        cr->set_line_width(2 * penumbra * i / kLayers);
        cr->stroke();

        // 立柱的影子：主光下是地面上的一条细线，从柱脚伸向远离光源的一侧。
        cr->set_line_cap(Cairo::Context::LineCap::ROUND);
        cr->move_to(stand_a.x, stand_a.y);
        cr->line_to(stand_b.x, stand_b.y);
        cr->set_line_width(stand_width + 2 * penumbra * i / kLayers * 0.5);
        cr->stroke();

        cr->pop_group_to_source();
        cr->paint_with_alpha(0.028 * alpha);
    }
    const auto shadow = cr->pop_group();

    // 蒙版：从盘缘往里 8 圈，每圈 0.4 的不透明度叠上去，盘缘淡、0.6 半径
    // 以内基本全不透明——魔方正下方的本影不受影响。
    cr->push_group();
    for (int ring = 0; ring < 8; ++ring) {
        trace_floor_circle(cr, camera, kFloorRadius * (1.0 - 0.05 * ring));
        cr->set_source_rgba(0, 0, 0, 0.4);
        cr->fill();
    }
    const auto mask = cr->pop_group();
    cr->set_source(shadow);
    cr->mask(mask);
}

struct Rect {
    double x = 0;
    double y = 0;
    double w = 0;
    double h = 0;
};

void draw_cube_3d(
    const Cairo::RefPtr<Cairo::Context>& cr, const Rect& region,
    const CubeState& state, double yaw, double pitch,
    const TurnAnimation* animation) {
    // 按“任何视角都完整显示”定缩放：遍历全部 yaw 和 ±kPitchLimit 内的
    // pitch，魔方（含转动中的层）加地面圆盘投影后的最大范围是横向 ±2.23、
    // 向上 2.16、向下 3.10（单位 = 魔方半边长）。按这个包围框取景，拖到
    // 哪个角度都不会被裁；不随视角动态缩放，否则一边转一边忽大忽小。
    // 阴影是半透明的淡出区域，不计入包围框。
    constexpr double kFitHalfWidth = 2.3;
    constexpr double kFitAbove = 2.2;
    constexpr double kFitBelow = 3.15;
    const double scale =
        0.96 * min(region.w / (2 * kFitHalfWidth), region.h / (kFitAbove + kFitBelow));
    const Camera camera(
        yaw, pitch, scale,
        {region.x + region.w / 2.0,
         region.y + region.h / 2.0 - scale * (kFitBelow - kFitAbove) / 2});

    const auto in_turning_layer = [&](const array<int, 3>& pos) {
        return animation != nullptr &&
               pos[static_cast<size_t>(animation->axis)] == animation->layer_coord;
    };
    const auto transform_for = [&](const array<int, 3>& pos) {
        return CubieTransform{in_turning_layer(pos) ? animation : nullptr};
    };

    vector<array<int, 3>> resting;
    vector<array<int, 3>> turning;
    for (int x : {-1, 1}) {
        for (int y : {-1, 1}) {
            for (int z : {-1, 1}) {
                (in_turning_layer({x, y, z}) ? turning : resting).push_back({x, y, z});
            }
        }
    }

    // 地面与阴影：相机降到地面以下时淡出，否则会从底下看到一张盖在魔方
    // 前面的“天花板”。
    const double floor_alpha = clamp((camera.eye.y - kFloorY) / 1.5, 0.0, 1.0);
    if (floor_alpha > 0) {
        vector<Vec3> caster_points;
        for (const auto* group : {&resting, &turning}) {
            for (const auto& pos : *group) {
                const CubieTransform transform = transform_for(pos);
                const Vec3 center{pos[0] * 0.5, pos[1] * 0.5, pos[2] * 0.5};
                for (int dx : {-1, 1}) {
                    for (int dy : {-1, 1}) {
                        for (int dz : {-1, 1}) {
                            caster_points.push_back(transform(
                                center + Vec3{dx * kCubieHalf, dy * kCubieHalf, dz * kCubieHalf}));
                        }
                    }
                }
            }
        }
        draw_floor(cr, camera, floor_alpha);
        draw_shadow(cr, camera, caster_points, floor_alpha);
    }

    // 两组之间用转动层的分隔平面排序：转动层绕层轴转，始终待在自己那半边，
    // 相机那一侧的组后画。组内各按自己的坐标系排序——转动层要把相机位置
    // 反转回层的局部坐标里再比较。立柱在不动角块下方，只属于静止组：
    // 跟静止组的块隔着 y = -1 平面，相机在平面上方就先画立柱。
    const auto draw_resting = [&] {
        sort_far_to_near(resting, camera.eye);
        const bool stand_first = camera.eye.y > -1.0;
        if (stand_first) {
            draw_stand(cr, camera);
        }
        for (const auto& pos : resting) {
            draw_cubie(cr, state, pos, CubieTransform{}, camera);
        }
        if (!stand_first) {
            draw_stand(cr, camera);
        }
    };
    const auto draw_turning = [&] {
        if (turning.empty()) {
            return;
        }
        sort_far_to_near(
            turning,
            rotate_around_axis(camera.eye, animation->axis, -animation->current_degrees));
        for (const auto& pos : turning) {
            draw_cubie(cr, state, pos, CubieTransform{animation}, camera);
        }
    };

    const bool camera_on_turning_side =
        animation != nullptr &&
        component(camera.eye, animation->axis) * animation->layer_coord > 0;
    if (camera_on_turning_side) {
        draw_resting();
        draw_turning();
    } else {
        draw_turning();
        draw_resting();
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

// 以 L/R 为极面重新摊开：L 在上、R 在下，中间一排是 U-F-D-B（R 顺时针
// 循环 U→F→D→B→U 会动的那一圈，见 state.cc face_info() 顶部注释），看
// R/L 转法用这版。跟 net_cell_sign() 一样，是把六个面绕各自跟 F 的公共
// 棱（F 本身固定不转）转 90° 摊平实际算出来的，不是凭感觉套的。
void net_cell_sign_lr(Face face, int ui, int vi, int& u_sign, int& v_sign) {
    const int a = ui * 2 - 1;
    const int b = vi * 2 - 1;
    switch (face) {
    case Face::L: u_sign = -a; v_sign = b; break;
    case Face::R: u_sign = -a; v_sign = -b; break;
    case Face::U: u_sign = b; v_sign = a; break;
    case Face::F: u_sign = b; v_sign = -a; break;
    case Face::D: u_sign = b; v_sign = -a; break;
    case Face::B: u_sign = b; v_sign = a; break;
    }
}

// 以 F/B 为极面重新摊开：F 在上、B 在下，中间一排是 U-L-D-R（F 顺时针
// 循环 U→L→D→R→U 会动的那一圈），看 F/B 转法用这版。这次固定不转的
// 极面是 L（F/B 本身是极面，不能再当基准），六个面绕各自跟 L 的公共棱
// 转 90° 摊平算出来的，方法跟前两版完全一样。
void net_cell_sign_fb(Face face, int ui, int vi, int& u_sign, int& v_sign) {
    const int a = ui * 2 - 1;
    const int b = vi * 2 - 1;
    switch (face) {
    case Face::F: u_sign = -b; v_sign = -a; break;
    case Face::B: u_sign = b; v_sign = -a; break;
    case Face::U: u_sign = -a; v_sign = -b; break;
    case Face::L: u_sign = -a; v_sign = -b; break;
    case Face::D: u_sign = a; v_sign = -b; break;
    case Face::R: u_sign = a; v_sign = -b; break;
    }
}

// 展开图：三种摊法共用的绘制逻辑，区别只是 sign_fn（每格该查哪个
// (u_sign,v_sign)）和 pole_top/row/pole_bottom（六个面摆在十字网格哪一
// 格）——具体传什么由三个 make_cube_net_view*() 各自决定，画格子、填色、
// 标编号这套逻辑完全一样，不重复三份。
using NetCellSignFn = void (*)(Face, int, int, int&, int&);

void draw_cube_net_generic(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height,
    const CubeState& state, NetCellSignFn sign_fn, Face pole_top,
    const array<Face, 4>& row, Face pole_bottom) {
    const double cell = min(width / 4.0, height / 3.0);
    const double margin_x = (width - cell * 4) / 2;
    const double margin_y = (height - cell * 3) / 2;

    const auto draw_one_face = [&](Face face, int col, int row_index) {
        const double origin_x = margin_x + col * cell;
        const double origin_y = margin_y + row_index * cell;
        for (int ui = 0; ui < 2; ++ui) {
            for (int vi = 0; vi < 2; ++vi) {
                int u_sign = 0;
                int v_sign = 0;
                sign_fn(face, ui, vi, u_sign, v_sign);
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

    draw_one_face(pole_top, 1, 0);
    for (size_t i = 0; i < row.size(); ++i) {
        draw_one_face(row[i], static_cast<int>(i), 1);
    }
    draw_one_face(pole_bottom, 1, 2);
}

// 展开图：U 在上、D 在下，L F R B 横排在中间一行——标准的十字形网格。
void draw_cube_net(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height,
    const CubeState& state) {
    draw_cube_net_generic(
        cr, width, height, state, net_cell_sign, Face::U,
        {Face::L, Face::F, Face::R, Face::B}, Face::D);
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

// ===== 拓扑图：角块缩成点、共面相邻缩成线 =====
//
// 8 个角块各缩成它中心的一个点，两块共用一个接触面就连一条线——得到的
// 是立方体图 Q3：8 点、12 边、每点度数 3。独立控件，跟 3D 视图共用一个
// CubeViewAngle，拖 3D 视图时一起转，看得出点和块一一对应。
//
// 图是活的：
// - 点按当前占着这个位置的角块涂三色，转一步就看得出哪几块换了位置；
//   位置（图的顶点）永远是那 8 个，换的是占位的块——这正是“状态”的含义；
// - 转动中那一层的 4 个点跟着转，跨层的 4 条边改成虚线：这 4 对相邻
//   关系在转动过程中暂时断开，转到位后重新接上，图还是同一张 Q3；
// - 不动的 D/L/B 角块那个点加一圈描边，它的颜色永远不变。

constexpr ChartColor kAccentColor = chart_color(0x6f42c1); // 跟 app.json 图标同一个强调色

void draw_topology(
    const Cairo::RefPtr<Cairo::Context>& cr, const Rect& region,
    const CubeState& state, double yaw, double pitch, const TurnAnimation* animation) {
    const double side = min(region.w, region.h);
    if (side < 40) {
        return;
    }

    // 点在 [-0.5, 0.5]^3 里，转到任何角度都落在半径 √3/2 的球内；再给
    // 透视和点的半径留一点余量。
    const double pad = side * 0.12;
    const Camera camera(
        yaw, pitch, (side / 2 - pad) / 0.95,
        {region.x + region.w / 2, region.y + region.h / 2});

    vector<array<int, 3>> positions;
    for (int x : {-1, 1}) {
        for (int y : {-1, 1}) {
            for (int z : {-1, 1}) {
                positions.push_back({x, y, z});
            }
        }
    }
    const auto turning = [&](const array<int, 3>& pos) {
        return animation != nullptr &&
               pos[static_cast<size_t>(animation->axis)] == animation->layer_coord;
    };
    const auto world_point = [&](const array<int, 3>& pos) {
        const Vec3 center{pos[0] * 0.5, pos[1] * 0.5, pos[2] * 0.5};
        return CubieTransform{turning(pos) ? animation : nullptr}(center);
    };
    const auto depth_of = [&](const Vec3& p) { return rotate(p, yaw, pitch).z; };

    // 边和点统一按深度从远到近画，近处的点能压住远处的边。
    struct Item {
        double depth;
        int a; // 点的下标
        int b; // 边的另一端；点本身为 -1
    };
    vector<Item> items;
    for (size_t i = 0; i < positions.size(); ++i) {
        items.push_back({depth_of(world_point(positions[i])), static_cast<int>(i), -1});
        for (size_t j = i + 1; j < positions.size(); ++j) {
            int differing = 0;
            for (size_t k = 0; k < 3; ++k) {
                differing += positions[i][k] != positions[j][k];
            }
            if (differing == 1) {
                const Vec3 mid = (world_point(positions[i]) + world_point(positions[j])) * 0.5;
                // 边比同深度的点略靠后，端点处由点盖住线头。
                items.push_back({depth_of(mid) - 0.01, static_cast<int>(i), static_cast<int>(j)});
            }
        }
    }
    sort(items.begin(), items.end(), [](const Item& l, const Item& r) {
        return l.depth < r.depth;
    });

    // 远处淡、近处实：深度映射到 [0,1]，点的半径另随透视缩放。
    const auto nearness = [](double depth) { return clamp((depth + 0.9) / 1.8, 0.0, 1.0); };
    // 点要装下三瓣各自的两位数编号，比纯色点大一圈。
    const double node_radius = side * 0.085;

    for (const Item& item : items) {
        const double t = nearness(item.depth);
        if (item.b >= 0) {
            const auto& pa = positions[static_cast<size_t>(item.a)];
            const auto& pb = positions[static_cast<size_t>(item.b)];
            const Vec3 wa = world_point(pa);
            const Vec3 wb = world_point(pb);
            Vec2 sa = camera.project(wa);
            Vec2 sb = camera.project(wb);
            // 线只画在两个圆的边缘之间：点上有编号，线头伸进圆里会压字，
            // 而且边比远端点后画，深度排序管不住这一段。
            const double ra = node_radius * camera.perspective(wa);
            const double rb = node_radius * camera.perspective(wb);
            const double dx = sb.x - sa.x;
            const double dy = sb.y - sa.y;
            const double len = sqrt(dx * dx + dy * dy);
            if (len <= ra + rb) {
                continue;
            }
            sa = {sa.x + dx / len * ra, sa.y + dy / len * ra};
            sb = {sb.x - dx / len * rb, sb.y - dy / len * rb};
            const bool broken = animation != nullptr && turning(pa) != turning(pb);
            cr->begin_new_path();
            cr->move_to(sa.x, sa.y);
            cr->line_to(sb.x, sb.y);
            cr->set_source_rgba(0.25, 0.27, 0.32, 0.30 + 0.45 * t);
            cr->set_line_width(1.2 + 1.3 * t);
            if (broken) {
                cr->set_dash(vector<double>{4.0, 3.0}, 0);
            }
            cr->stroke();
            cr->unset_dash();
            continue;
        }

        const auto& pos = positions[static_cast<size_t>(item.a)];
        const Vec3 p = world_point(pos);
        const Vec2 c = camera.project(p);
        const double r = node_radius * camera.perspective(p);
        const double alpha = 0.55 + 0.45 * t;

        // 三等分扇形：上方一瓣是 U/D 向（Y）的贴纸，另两瓣是 X、Z 向。
        // 每瓣标上那张贴纸的编号——跟 3D 视图、展开图同一套 1~24，同样
        // 跟着贴纸走（sticker_home()），不跟着位置走。
        constexpr array<size_t, 3> kWedgeAxes{1, 0, 2};
        struct WedgeLabel {
            Vec2 at;
            int number;
        };
        array<WedgeLabel, 3> wedge_labels{};
        for (size_t w = 0; w < kWedgeAxes.size(); ++w) {
            const auto [face, u_sign, v_sign] = outward_slot(pos, kWedgeAxes[w]);
            const ChartColor color = sticker_color(sticker_at(state, face, u_sign, v_sign));
            const double start = -std::numbers::pi / 2 - std::numbers::pi / 3 +
                                 w * 2 * std::numbers::pi / 3;
            cr->begin_new_path();
            cr->move_to(c.x, c.y);
            cr->arc(c.x, c.y, r, start, start + 2 * std::numbers::pi / 3);
            cr->close_path();
            cr->set_source_rgba(color.r, color.g, color.b, alpha);
            cr->fill();

            const double mid = start + std::numbers::pi / 3;
            const StickerHome home = sticker_home(state, face, u_sign, v_sign);
            wedge_labels[w] = {
                {c.x + r * 0.55 * cos(mid), c.y + r * 0.55 * sin(mid)},
                sticker_label(home.face, home.u_sign, home.v_sign)};
        }
        // 三瓣之间描细白线分隔，编号各归各瓣。
        for (size_t w = 0; w < kWedgeAxes.size(); ++w) {
            const double edge = -std::numbers::pi / 2 - std::numbers::pi / 3 +
                                w * 2 * std::numbers::pi / 3;
            cr->begin_new_path();
            cr->move_to(c.x, c.y);
            cr->line_to(c.x + r * cos(edge), c.y + r * sin(edge));
            cr->set_source_rgba(1, 1, 1, 0.8 * alpha);
            cr->set_line_width(1.0);
            cr->stroke();
        }
        cairo_select_font_face(
            cr->cobj(), "sans-serif", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
        cr->set_font_size(max(7.0, r * 0.52));
        for (const auto& label : wedge_labels) {
            const string text = to_string(label.number);
            Cairo::TextExtents extents;
            cr->get_text_extents(text, extents);
            cr->move_to(
                label.at.x - extents.width / 2.0 - extents.x_bearing,
                label.at.y - extents.height / 2.0 - extents.y_bearing);
            cr->set_source_rgba(0.1, 0.1, 0.12, 0.85 * alpha);
            cr->show_text(text);
        }
        cr->begin_new_path();
        cr->arc(c.x, c.y, r, 0, 2 * std::numbers::pi);
        cr->set_source_rgba(0.15, 0.15, 0.18, 0.55 + 0.35 * t);
        cr->set_line_width(1.2);
        cr->stroke();

        if (pos == kFixedCubie) {
            cr->begin_new_path();
            cr->arc(c.x, c.y, r + 3.0, 0, 2 * std::numbers::pi);
            cr->set_source_rgba(kAccentColor.r, kAccentColor.g, kAccentColor.b, alpha);
            cr->set_line_width(2.0);
            cr->stroke();
        }
    }
}

// 初始视角：俯视，同时看到 U/F/R 三个转动面。pitch 必须为正（相机在
// 上方）：为负会转到仰视，U 被剔除、露出 D。yaw 从正对 F/R 棱的 -45°
// 往回偏一点，避免左右对称的呆板构图，也让右后方的阴影露出来。
constexpr double kDefaultYaw = -std::numbers::pi / 4 + 0.22;
constexpr double kDefaultPitch = std::numbers::pi / 6.5;
// 俯仰限制在约 ±74°：再往上下就正对某个面，立体感消失。
constexpr double kPitchLimit = 1.3;
constexpr double kDragSensitivity = 0.012; // 弧度/像素

// 视角状态。拖动时按指针位移直接设角度；松手时带着最后的角速度继续转、
// 指数衰减停下——转动过程本身就是立体线索，惯性让“甩一下看看背面”
// 成本更低。
struct OrbitState {
    shared_ptr<CubeViewAngle> angle;
    double drag_start_yaw = 0;
    double drag_start_pitch = 0;
    double yaw_velocity = 0; // 弧度/秒
    double pitch_velocity = 0;
    double last_offset_x = 0;
    double last_offset_y = 0;
    gint64 last_update_us = 0;
    gint64 last_frame_us = 0;
    guint inertia_tick = 0;
};

void stop_inertia(Gtk::DrawingArea* area, OrbitState& orbit) {
    if (orbit.inertia_tick != 0) {
        area->remove_tick_callback(orbit.inertia_tick);
        orbit.inertia_tick = 0;
    }
}

} // namespace

shared_ptr<CubeViewAngle> make_cube_view_angle() {
    auto angle = make_shared<CubeViewAngle>();
    angle->yaw = kDefaultYaw;
    angle->pitch = kDefaultPitch;
    return angle;
}

Gtk::Widget* make_cube_3d_view(
    function<CubeState()> state_provider, int size,
    function<optional<TurnAnimation>()> animation_provider,
    shared_ptr<CubeViewAngle> angle) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(size);
    area->set_content_height(size);

    auto orbit = make_shared<OrbitState>();
    orbit->angle = angle ? angle : make_cube_view_angle();
    // 视角的任何改动都走 changed 信号：自己和订阅了同一视角的拓扑图一起
    // 重绘。Gtk::Widget 是 sigc::trackable，控件销毁时连接自动断开。
    orbit->angle->changed.connect(sigc::mem_fun(*area, &Gtk::Widget::queue_draw));

    area->set_draw_func(
        [state_provider, animation_provider, orbit](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const optional<TurnAnimation> animation =
                animation_provider ? animation_provider() : nullopt;
            draw_cube_3d(
                cr, {0, 0, double(width), double(height)}, state_provider(),
                orbit->angle->yaw, orbit->angle->pitch, animation ? &*animation : nullptr);
        });

    // pitch 取 +offset_y：手指往上拖，像从下往上托着魔方底部，把底面翻向
    // 观察者、露出更多顶面——“拖拽 = 推着物体表面同向走”的直觉。
    auto drag = Gtk::GestureDrag::create();
    drag->signal_drag_begin().connect([area, orbit](double, double) {
        stop_inertia(area, *orbit);
        orbit->drag_start_yaw = orbit->angle->yaw;
        orbit->drag_start_pitch = orbit->angle->pitch;
        orbit->yaw_velocity = 0;
        orbit->pitch_velocity = 0;
        orbit->last_offset_x = 0;
        orbit->last_offset_y = 0;
        orbit->last_update_us = g_get_monotonic_time();
    });
    drag->signal_drag_update().connect([orbit](double offset_x, double offset_y) {
        const gint64 now = g_get_monotonic_time();
        const double dt = (now - orbit->last_update_us) / 1e6;
        if (dt > 0) {
            // 指针事件间隔不均匀，瞬时速度抖得厉害，做一次指数平滑。
            const double vx = (offset_x - orbit->last_offset_x) * kDragSensitivity / dt;
            const double vy = (offset_y - orbit->last_offset_y) * kDragSensitivity / dt;
            orbit->yaw_velocity = 0.6 * vx + 0.4 * orbit->yaw_velocity;
            orbit->pitch_velocity = 0.6 * vy + 0.4 * orbit->pitch_velocity;
        }
        orbit->last_offset_x = offset_x;
        orbit->last_offset_y = offset_y;
        orbit->last_update_us = now;

        orbit->angle->yaw = orbit->drag_start_yaw + offset_x * kDragSensitivity;
        orbit->angle->pitch = clamp(
            orbit->drag_start_pitch + offset_y * kDragSensitivity, -kPitchLimit, kPitchLimit);
        orbit->angle->changed.emit();
    });
    drag->signal_drag_end().connect([area, orbit](double, double) {
        // 停住不动再松手，就不该继续转。
        if (g_get_monotonic_time() - orbit->last_update_us > 80'000) {
            return;
        }
        if (hypot(orbit->yaw_velocity, orbit->pitch_velocity) < 0.3) {
            return;
        }
        orbit->last_frame_us = 0;
        orbit->inertia_tick = area->add_tick_callback(
            [orbit](const Glib::RefPtr<Gdk::FrameClock>& clock) {
                const gint64 now = clock->get_frame_time();
                const double dt =
                    orbit->last_frame_us == 0 ? 0.0 : (now - orbit->last_frame_us) / 1e6;
                orbit->last_frame_us = now;

                CubeViewAngle& angle = *orbit->angle;
                angle.yaw += orbit->yaw_velocity * dt;
                angle.pitch += orbit->pitch_velocity * dt;
                if (abs(angle.pitch) >= kPitchLimit) {
                    angle.pitch = clamp(angle.pitch, -kPitchLimit, kPitchLimit);
                    orbit->pitch_velocity = 0;
                }
                const double decay = exp(-dt * 3.5);
                orbit->yaw_velocity *= decay;
                orbit->pitch_velocity *= decay;
                angle.changed.emit();

                if (hypot(orbit->yaw_velocity, orbit->pitch_velocity) < 0.05) {
                    orbit->inertia_tick = 0;
                    return false;
                }
                return true;
            });
    });
    area->add_controller(drag);

    auto click = Gtk::GestureClick::create();
    click->signal_pressed().connect([area, orbit](int n_press, double, double) {
        if (n_press == 2) {
            stop_inertia(area, *orbit);
            orbit->angle->yaw = kDefaultYaw;
            orbit->angle->pitch = kDefaultPitch;
            orbit->angle->changed.emit();
        }
    });
    area->add_controller(click);

    area->set_cursor("grab");
    area->set_tooltip_text(
        "按住拖动旋转查看，松手会带惯性；双击回到默认视角。"
        "底下立柱托着的是 D/L/B 交界的角块：只转 U/R/F 时它从头到尾不动");

    return area;
}

Gtk::Widget* make_cube_topology_view(
    function<CubeState()> state_provider, shared_ptr<CubeViewAngle> angle, int size,
    function<optional<TurnAnimation>()> animation_provider) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(size);
    area->set_content_height(size);
    angle->changed.connect(sigc::mem_fun(*area, &Gtk::Widget::queue_draw));
    area->set_draw_func(
        [state_provider, animation_provider, angle](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const optional<TurnAnimation> animation =
                animation_provider ? animation_provider() : nullopt;
            draw_topology(
                cr, {0, 0, double(width), double(height)}, state_provider(), angle->yaw,
                angle->pitch, animation ? &*animation : nullptr);
        });
    area->set_tooltip_text(
        "角块缩成点、共面相邻缩成线：立方体图 Q3，8 点 12 边。"
        "点的三瓣是当前占着这个位置的角块的三张贴纸，编号跟 3D 视图、展开图"
        "同一套、跟着贴纸走；紫圈是不动的 D/L/B 角块；"
        "转动中跨层的 4 条边画成虚线。视角跟随 3D 视图");
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

Gtk::Widget* make_cube_net_view_lr_axis(
    function<CubeState()> state_provider, int width, int height) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(width);
    area->set_content_height(height);
    area->set_draw_func(
        [state_provider](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_cube_net_generic(
                cr, width, height, state_provider(), net_cell_sign_lr, Face::L,
                {Face::U, Face::F, Face::D, Face::B}, Face::R);
        });
    area->set_tooltip_text("六面展开图（L/R 极面）：看 R/L 转法用这版");
    return area;
}

Gtk::Widget* make_cube_net_view_fb_axis(
    function<CubeState()> state_provider, int width, int height) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(width);
    area->set_content_height(height);
    area->set_draw_func(
        [state_provider](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_cube_net_generic(
                cr, width, height, state_provider(), net_cell_sign_fb, Face::F,
                {Face::U, Face::L, Face::D, Face::R}, Face::B);
        });
    area->set_tooltip_text("六面展开图（F/B 极面）：看 F/B 转法用这版");
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
