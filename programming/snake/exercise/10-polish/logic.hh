// 蛇的全部规则。不含任何 raylib 类型——不开窗口也能编译、能测试。
// 相对第八、九版的 logic.hh，这一版有一处演化：吃到加速（stepTime 乘 0.98，有下限）。
// 加速属于规则而不是渲染——关掉窗口它依然成立；下一个长出来的规则（道具、传送门）
// 也该长在这里。测试跟着规则一起长：本章的断言比第九章多一条加速。

#pragma once

#include <algorithm>
#include <deque>
#include <random>

namespace snake {

constexpr int COLS = 32;
constexpr int ROWS = 24;

struct Cell {
    int x = 0;
    int y = 0;
    bool operator==(const Cell& other) const = default;
};

enum class Dir { Right, Left, Up, Down };

constexpr Cell DELTA[4] = {{1, 0}, {-1, 0}, {0, -1}, {0, 1}};
constexpr Dir OPPOSITE[4] = {Dir::Left, Dir::Right, Dir::Down, Dir::Up};
constexpr int dir_index(Dir d) { return static_cast<int>(d); }

struct Game {
    std::deque<Cell> body;      // 头在 front
    std::deque<Dir> pending;    // 输入缓冲
    Dir heading = Dir::Right;
    Cell food{20, 12};
    int score = 0;
    float stepTime = 0.12f;     // 每吃一节乘 0.98，下限见 step
    bool dead = false;
    std::mt19937 rng{std::random_device{}()};
};

inline bool occupies(const Game& game, Cell cell) {
    for (const Cell& part : game.body) {
        if (part == cell) return true;
    }
    return false;
}

inline void spawn_food(Game& game) {
    std::uniform_int_distribution<int> col(0, COLS - 1);
    std::uniform_int_distribution<int> row(0, ROWS - 1);
    do {
        game.food = Cell{col(game.rng), row(game.rng)};
    } while (occupies(game, game.food));
}

inline void reset(Game& game) {
    game.body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};
    game.pending.clear();
    game.heading = Dir::Right;
    game.score = 0;
    game.stepTime = 0.12f;
    game.dead = false;
    spawn_food(game);
}

inline void press(Game& game, Dir dir) {
    Dir last = game.pending.empty() ? game.heading : game.pending.back();
    if (dir == last || dir == OPPOSITE[dir_index(last)]) return;
    if (game.pending.size() >= 3) return;
    game.pending.push_back(dir);
}

inline void step(Game& game) {
    if (game.dead) return;
    if (!game.pending.empty()) {
        game.heading = game.pending.front();
        game.pending.pop_front();
    }
    Cell head{game.body.front().x + DELTA[dir_index(game.heading)].x,
              game.body.front().y + DELTA[dir_index(game.heading)].y};
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS || occupies(game, head)) {
        game.dead = true;
        return;
    }
    game.body.push_front(head);
    if (head == game.food) {
        game.score += 10;
        game.stepTime = std::max(0.06f, game.stepTime * 0.98f);  // 越吃越快，但有下限
        spawn_food(game);
    } else {
        game.body.pop_back();
    }
}

}  // namespace snake
