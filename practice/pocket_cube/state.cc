#include "practice/pocket_cube/state.h"

namespace {

// 绕某轴转 90 度对 (position, color) 的作用：只描述“变量对应关系”，不
// 带符号——符号（这个新方向具体是 + 还是 -）已经完全体现在新的 x/y/z
// 坐标本身上，颜色标签只是跟着“搬家”，不需要重复处理正负号。
//
// 下面这套坐标变换是从标准旋转矩阵手推出来的（面对着某个面看、顺时针
// 为正）：
//   U 顺时针：(x,y,z) -> (-z,y,x)
//   D 顺时针：(x,y,z) -> ( z,y,-x)
//   R 顺时针：(x,y,z) -> (x, z,-y)
//   L 顺时针：(x,y,z) -> (x,-z, y)
//   F 顺时针：(x,y,z) -> ( y,-x, z)
//   B 顺时针：(x,y,z) -> (-y, x, z)
// direction>0 对应上面这一组；direction<0 是它的逆变换。同一转轴的两
// 个面（U/D、L/R、F/B）共享同一套“变量对应关系”，只是符号相反，这也
// 是为什么 face_info() 只需要记一个 clockwise_dir 符号，不需要为 6 个
// 面分别写 6 段变换代码。
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

FaceInfo face_info(Face face) {
    switch (face) {
    case Face::U: return {Axis::Y, 1, 1};
    case Face::D: return {Axis::Y, -1, -1};
    case Face::R: return {Axis::X, 1, 1};
    case Face::L: return {Axis::X, -1, -1};
    case Face::F: return {Axis::Z, 1, 1};
    case Face::B: return {Axis::Z, -1, -1};
    }
    return {Axis::Y, 1, 1};
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
    const int steps = move.turn == Turn::Half ? 2 : 1;
    const int direction =
        move.turn == Turn::CounterClockwise ? -info.clockwise_dir : info.clockwise_dir;

    CubeState result = state;
    for (auto& corner : result.corners) {
        if (!corner_in_layer(corner, info.axis, info.layer_coord)) {
            continue;
        }
        for (int step = 0; step < steps; ++step) {
            corner = rotate_corner_90(corner, info.axis, direction);
        }
    }
    return result;
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
