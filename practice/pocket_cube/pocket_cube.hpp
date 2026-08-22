#pragma once
#include "practice/pocket_cube/state.h"

#include <iostream>

using namespace std;

// 2 阶魔方（Pocket Cube）：只有 8 个角块，没有棱块和中心块。这才是这个
// 知识点真正的实现——魔方的状态表示和转动代数在
// practice/pocket_cube/state.h 里（不依赖 GTK，可以脱离渲染层单独
// 测试）；这个类只是持有一份当前状态、每次调用转一步，供界面直接调用，
// “运行”按钮点了以后执行的就是这个函数，不是界面代码里另外藏一份。
//
// 目前只固定转 U（上层）顺时针这一步，用来演示状态该怎么驱动界面；
// 真正的打乱和求解算法还没做。
class PocketCube {
public:
    void turn(ostream& os) {
        m_state = apply_move(m_state, {Face::U, Turn::Clockwise});
        os << "执行了一次 U（上层）顺时针转动。" << endl;
        os << (is_solved(m_state) ? "当前已复原。" : "当前尚未复原。") << endl;
    }

    const CubeState& state() const { return m_state; }

private:
    CubeState m_state = make_solved_cube();
};
