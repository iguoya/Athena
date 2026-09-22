#pragma once
#include "practice/pocket_cube/state.h"

#include <array>
#include <iostream>
#include <utility>
#include <vector>

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
        const Move move = next_turn_move();
        m_state = apply_move(m_state, move);
        m_move_history.push_back(move);
        os << "执行了一次 " << move_description(move) << "。" << endl;
        os << (is_solved(m_state) ? "当前已复原。" : "当前尚未复原。") << endl;
    }

    // turn() 下一次会真正执行的转法：供界面先看一眼要转哪个层、哪个
    // 方向，用来驱动“运行”按钮点击后的转动动画（动画播完才真正调用
    // turn()）——跟 turn() 内部执行的 move 共用同一个来源，不在界面
    // 代码里另外写死一份，两处容易不同步。
    Move next_turn_move() const { return {Face::U, Turn::Clockwise}; }

    const CubeState& state() const { return m_state; }

    // 从复原状态出发、依次执行到当前状态的转法序列，每次 turn() 调用
    // 追加一项——用于界面展示“当前魔方的路径”，不是运行历史文字日志
    // 那种一次性提示，而是可以完整回放的转法记录。
    const vector<Move>& move_history() const { return m_move_history; }

    // 把魔方重置回初始（已复原）状态，清空转动路径——给“复原”按钮用，
    // 不经过 apply_move() 一步步转回去，直接回到 make_solved_cube() 这个
    // 已知起点；跟 turn() 一样只改状态和路径，不做任何界面相关的事。
    void reset() {
        m_state = make_solved_cube();
        m_move_history.clear();
    }

    // 下一步穷举：把 next_move_set() 给出的 9 种非冗余转法（U/R/F 三个
    // 面各转顺时针/逆时针/180°）分别应用到当前状态，返回 (转法, 转后
    // 状态) 列表，不修改 m_state——供界面画“下一步穷举”九宫格用；真正
    // 驱动状态变化的仍然只有 run()/turn()。
    array<pair<Move, CubeState>, 9> next_states() const {
        array<pair<Move, CubeState>, 9> result;
        const array<Move, 9> moves = next_move_set();
        for (size_t i = 0; i < moves.size(); ++i) {
            result[i] = {moves[i], apply_move(m_state, moves[i])};
        }
        return result;
    }

private:
    CubeState m_state = make_solved_cube();
    vector<Move> m_move_history;
    //unordered_set<CubeState> m_visited_states;
};
