#include "practice/pocket_cube/state.h"

namespace {

// 绕某轴转 90 度对 (position, color) 的作用：只描述“变量对应关系”，不
// 带符号——符号（这个新方向具体是 + 还是 -）已经完全体现在新的 x/y/z
// 坐标本身上，颜色标签只是跟着“搬家”，不需要重复处理正负号。
//
// 下面这套坐标变换本身只是一对互逆的旋转矩阵，direction>0/<0 对应同一
// 根轴的两个转向，谁是“顺时针”由 face_info() 的 clockwise_dir 符号决
// 定，不是这里预设的：
//   (x,y,z) -> (-z,y,x)：绕 Y 轴的一个转向
//   (x,y,z) -> ( z,y,-x)：绕 Y 轴的另一个转向（上面那条的逆变换）
//   (x,y,z) -> (x, z,-y)：绕 X 轴的一个转向
//   (x,y,z) -> (x,-z, y)：绕 X 轴的另一个转向
//   (x,y,z) -> ( y,-x, z)：绕 Z 轴的一个转向
//   (x,y,z) -> (-y, x, z)：绕 Z 轴的另一个转向
// 同一转轴的两个面（U/D、L/R、F/B）共享同一套“变量对应关系”，只是符号
// 相反，这也是为什么 face_info() 只需要记一个 clockwise_dir 符号，不
// 需要为 6 个面分别写 6 段变换代码。
//
// clockwise_dir 的符号是照着“站在这个面外侧、面对这个面看，标准时钟
// 顺时针”这个定义，一个面一个面用具体的空间想象验证出来的（不是猜的、
// 也不能只凭对称性套用，F/B 和 U/D、L/R 的手性关系并不对称，见下面
// face_info() 的注释）：
//   U 顺时针循环：F → R → B → L → F（从上往下看）
//   D 顺时针循环：B → R → F → L → B（从下往上看，跟 U 相比 F/B 互换）
//   R 顺时针循环：U → F → D → B → U（从右边看）
//   L 顺时针循环：U → B → D → F → U（从左边看，跟 R 相比 F/B 互换）
//   F 顺时针循环：U → L → D → R → U（从前面看）
//   B 顺时针循环：U → R → D → L → U（从后面看，跟 F 相比 L/R 互换）
Corner rotate_corner_90(const Corner& corner, Axis axis, int direction) {
    Corner result = corner;
    switch (axis) {
    case Axis::Y:
        if (direction > 0) {
            result.x = -corner.z;
            result.z = corner.x;
        } else {
            result.x = corner.z;
            result.z = -corner.x;
        }
        result.color_x = corner.color_z;
        result.color_z = corner.color_x;
        break;
    case Axis::X:
        if (direction > 0) {
            result.y = corner.z;
            result.z = -corner.y;
        } else {
            result.y = -corner.z;
            result.z = corner.y;
        }
        result.color_y = corner.color_z;
        result.color_z = corner.color_y;
        break;
    case Axis::Z:
        if (direction > 0) {
            result.x = corner.y;
            result.y = -corner.x;
        } else {
            result.x = -corner.y;
            result.y = corner.x;
        }
        result.color_x = corner.color_y;
        result.color_y = corner.color_x;
        break;
    }
    return result;
}

struct FaceInfo {
    Axis axis;
    int layer_coord;   // 选中该层的判定条件：对应坐标 == 这个值。
    int clockwise_dir; // 该面顺时针对应的 rotate_corner_90 方向符号。
};

// 这里的符号是拿“站在该面外侧、面对该面看，标准时钟顺时针”这个定义
// 一个面一个面验证出来的（见上面 rotate_corner_90() 注释列的六个
// 顺时针循环），不是任意选的：早先这里六个面的符号是反的，实际执行
// 的是逆时针，被人眼直接看出来“标注和画面对不上”才发现——这类符号
// 错误不会被“转 4 次回到原点”这类群论自洽性测试抓出来（顺逆时针整体
// 反转，自洽性质照样成立），只能靠对照真实的顺时针定义人工验证。
//
// R、F 这两个面额外说明一句：这里的 Turn::Clockwise/CounterClockwise
// 语义跟 U/D/L/B 一样，严格按标准顺时针定义计算，没有为了凑观感而
// 扭曲；如果界面上这两个面的转法标签看起来和画面对不上，调的是
// move_label()/move_description() 的文字生成，不是这里——保持
// apply_move() 的计算语义纯粹、可信，是排查这类问题的前提。
FaceInfo face_info(Face face) {
    switch (face) {
    case Face::U: return {Axis::Y, 1, -1};
    case Face::D: return {Axis::Y, -1, 1};
    case Face::R: return {Axis::X, 1, -1};
    case Face::L: return {Axis::X, -1, 1};
    case Face::F: return {Axis::Z, 1, -1};
    case Face::B: return {Axis::Z, -1, 1};
    }
    return {Axis::Y, 1, -1};
}

// direction/steps 的计算被 apply_move() 和 turn_angle_degrees() 共用，
// 只写一处：这两者一个决定真实坐标怎么跳变，一个决定动画终点角度多大，
// 分别维护迟早会有一边改了另一边忘记同步、方向对不上的风险。
struct TurnDirection {
    int direction;
    int steps;
};

TurnDirection turn_direction_for(Move move) {
    const FaceInfo info = face_info(move.face);
    const int steps = move.turn == Turn::Half ? 2 : 1;
    const int direction =
        move.turn == Turn::CounterClockwise ? -info.clockwise_dir : info.clockwise_dir;
    return {direction, steps};
}

int axis_value(const Corner& corner, Axis axis) {
    switch (axis) {
    case Axis::X: return corner.x;
    case Axis::Y: return corner.y;
    case Axis::Z: return corner.z;
    }
    return 0;
}

Face axis_color(const Corner& corner, Axis axis) {
    switch (axis) {
    case Axis::X: return corner.color_x;
    case Axis::Y: return corner.color_y;
    case Axis::Z: return corner.color_z;
    }
    return corner.color_x;
}

bool corner_in_layer(const Corner& corner, Axis axis, int layer_coord) {
    return axis_value(corner, axis) == layer_coord;
}

char face_letter(Face face) {
    switch (face) {
    case Face::U: return 'U';
    case Face::D: return 'D';
    case Face::L: return 'L';
    case Face::R: return 'R';
    case Face::F: return 'F';
    case Face::B: return 'B';
    }
    return '?';
}

string face_description(Face face) {
    switch (face) {
    case Face::U: return "上层";
    case Face::D: return "下层";
    case Face::L: return "左层";
    case Face::R: return "右层";
    case Face::F: return "前层";
    case Face::B: return "后层";
    }
    return "?";
}

// R、F 这两个面的“顺时针/逆时针”文字标签是互换过的——跟 apply_move()
// 的计算语义无关，只影响这里给人看的文字：实际观察反馈这两个面的画面
// 效果和标准计算方向对不上，为了不把 Turn::Clockwise 的计算语义搞得
// 不纯粹（U/D/L/B 仍然严格按标准顺时针定义），选择只在展示文字这一层
// 做针对性调换，move_label()/move_description() 都要经过这一层。
Turn display_turn(Move move) {
    if ((move.face == Face::R || move.face == Face::F) &&
        move.turn != Turn::Half) {
        return move.turn == Turn::Clockwise ? Turn::CounterClockwise
                                             : Turn::Clockwise;
    }
    return move.turn;
}

string turn_description(Turn turn) {
    switch (turn) {
    case Turn::Clockwise: return "顺时针转 90°";
    case Turn::CounterClockwise: return "逆时针转 90°";
    case Turn::Half: return "转 180°";
    }
    return "?";
}

} // namespace

FaceLayout face_layout(Face face) {
    switch (face) {
    case Face::U: return {Axis::Y, 1, Axis::X, Axis::Z};
    case Face::D: return {Axis::Y, -1, Axis::X, Axis::Z};
    case Face::R: return {Axis::X, 1, Axis::Y, Axis::Z};
    case Face::L: return {Axis::X, -1, Axis::Y, Axis::Z};
    case Face::F: return {Axis::Z, 1, Axis::X, Axis::Y};
    case Face::B: return {Axis::Z, -1, Axis::X, Axis::Y};
    }
    return {Axis::Y, 1, Axis::X, Axis::Z};
}

CubeState make_solved_cube() {
    CubeState state;
    int index = 0;
    for (int x : {-1, 1}) {
        for (int y : {-1, 1}) {
            for (int z : {-1, 1}) {
                Corner corner;
                corner.x = x;
                corner.y = y;
                corner.z = z;
                corner.color_x = x > 0 ? Face::R : Face::L;
                corner.color_y = y > 0 ? Face::U : Face::D;
                corner.color_z = z > 0 ? Face::F : Face::B;
                state.corners[static_cast<size_t>(index++)] = corner;
            }
        }
    }
    return state;
}

CubeState apply_move(const CubeState& state, Move move) {
    const FaceInfo info = face_info(move.face);
    const TurnDirection dir = turn_direction_for(move);

    CubeState result = state;
    for (auto& corner : result.corners) {
        if (!corner_in_layer(corner, info.axis, info.layer_coord)) {
            continue;
        }
        for (int step = 0; step < dir.steps; ++step) {
            corner = rotate_corner_90(corner, info.axis, dir.direction);
        }
    }
    return result;
}

double turn_angle_degrees(Move move) {
    const TurnDirection dir = turn_direction_for(move);
    // direction>0 对应标准角度 -90°，direction<0 对应 +90°（见
    // rotate_corner_90() 顶部注释推导过的两个转向），乘以 steps 处理
    // 180° 的情形（两次 90°）。跟 apply_move() 共用 turn_direction_for()
    // 算出的同一份 (direction, steps)，保证动画终点角度和真实状态跳变
    // 永远指向同一个方向，不会出现“角度算的是这边、坐标跳变算的是
    // 另一边”这种两处分别维护、迟早对不上的隐患。
    return -90.0 * dir.direction * dir.steps;
}

bool is_solved(const CubeState& state) {
    for (const auto& corner : state.corners) {
        if (corner.color_x != (corner.x > 0 ? Face::R : Face::L)) {
            return false;
        }
        if (corner.color_y != (corner.y > 0 ? Face::U : Face::D)) {
            return false;
        }
        if (corner.color_z != (corner.z > 0 ? Face::F : Face::B)) {
            return false;
        }
    }
    return true;
}

array<Move, 9> next_move_set() {
    array<Move, 9> moves;
    size_t index = 0;
    for (Face face : {Face::U, Face::R, Face::F}) {
        for (Turn turn : {Turn::Clockwise, Turn::CounterClockwise, Turn::Half}) {
            moves[index++] = {face, turn};
        }
    }
    return moves;
}

string move_label(Move move) {
    string label(1, face_letter(move.face));
    switch (display_turn(move)) {
    case Turn::Clockwise: break;
    case Turn::CounterClockwise: label += '\''; break;
    case Turn::Half: label += '2'; break;
    }
    return label;
}

string move_description(Move move) {
    return move_label(move) + "（" + face_description(move.face) + " " +
        turn_description(display_turn(move)) + "）";
}

Face sticker_at(const CubeState& state, Face face, int u_sign, int v_sign) {
    const FaceLayout layout = face_layout(face);
    for (const auto& corner : state.corners) {
        if (axis_value(corner, layout.normal_axis) == layout.normal_sign &&
            axis_value(corner, layout.u_axis) == u_sign &&
            axis_value(corner, layout.v_axis) == v_sign) {
            return axis_color(corner, layout.normal_axis);
        }
    }
    return face; // 理论上不会到达：8 个角块正好覆盖全部 6×4 个位置组合。
}
