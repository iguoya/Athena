#pragma once
#include "practice/pocket_cube/state.h"

#include <iostream>

using namespace std;

// 2 阶魔方（Pocket Cube）：只有 8 个角块，没有棱块和中心块。这才是这个
// 知识点真正的实现——魔方的状态表示和转动代数在
// practice/pocket_cube/state.h 里（不依赖 GTK，可以脱离渲染层单独
// 测试）；这个类持有一份当前状态，供界面直接调用，“运行”按钮点了
// 以后执行的就是这里的代码，不是界面代码里另外藏一份。
//
// run() 是对外统一的知识点入口（跟其它章节一样，subchapter.name 对应
// 的成员函数名），具体干什么事交给 turn() 这个内部方法——现在 run()
// 只是转发给 turn()，以后如果这个知识点要加别的动作（比如打乱、单步
// 求解演示），可以在 run() 里按需要调度到不同的内部方法，不用改
// athena.json 里已经约定好的入口名字。
//
// 目前 turn() 只固定转 U（上层）顺时针这一步，用来演示状态该怎么驱动
// 界面；真正的打乱和求解算法还没做。
class PocketCube {
public:
    void run(ostream& os) {
        turn(os);
    }

    void turn(ostream& os) {
        m_state = apply_move(m_state, {Face::U, Turn::Clockwise});
        os << "执行了一次 U（上层）顺时针转动。" << endl;
        os << (is_solved(m_state) ? "当前已复原。" : "当前尚未复原。") << endl;
    }

    const CubeState& state() const { return m_state; }

private:
    CubeState m_state = make_solved_cube();
};
