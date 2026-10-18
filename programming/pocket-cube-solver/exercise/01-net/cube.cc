#include "cube.hh"

namespace cube {

const char* color_name(int color) {
    static constexpr const char* names[6] = {"黄", "橙", "绿", "白", "红", "蓝"};
    return color >= 0 && color < 6 ? names[color] : "未涂";
}

const char* face_name(int face) {
    static constexpr const char* names[6] = {"U 面（上）", "R 面（右）", "F 面（前）",
                                             "D 面（下）", "L 面（左）", "B 面（后）"};
    return names[face];
}

Stickers solved() {
    Stickers s{};
    for (int i = 0; i < kStickers; ++i) {
        s[i] = static_cast<std::uint8_t>(i / 4);
    }
    return s;
}

Stickers sample() {
    return {0, 4, 0, 2, 1, 0, 0, 1, 2, 3, 2, 2, 3, 1, 3, 3, 5, 4, 4, 4, 5, 1, 5, 5};
}

const std::array<std::array<int, 3>, kCorners>& corner_slots() {
    static const std::array<std::array<int, 3>, kCorners> table = {{
        {3, 4, 9},    // URF：上右前
        {2, 8, 17},   // UFL：上前左
        {0, 16, 21},  // ULB：上左后
        {1, 20, 5},   // UBR：上后右
        {13, 11, 6},  // DFR：下前右
        {12, 19, 10}, // DLF：下左前
        {14, 23, 18}, // DBL：下后左
        {15, 7, 22},  // DRB：下右后
    }};
    return table;
}

const char* corner_name(int corner) {
    static constexpr const char* names[kCorners] = {"URF", "UFL", "ULB", "UBR",
                                                    "DFR", "DLF", "DBL", "DRB"};
    return names[corner];
}

int corner_of(int slot) {
    for (int c = 0; c < kCorners; ++c) {
        for (int s : corner_slots()[c]) {
            if (s == slot) {
                return c;
            }
        }
    }
    return -1;
}

}  // namespace cube
