#include "../logic.hh"

#include <cassert>

// 蛇的规则不开窗口也能测——这正是逻辑与渲染分离换来的东西。
// 相对第九章的测试，多了一条加速断言：规则演化到哪，测试跟到哪。

int main() {
    snake::Game game;
    snake::reset(game);

    // 起步朝右：直接掉头是无效输入，第一步继续向右。
    snake::press(game, snake::Dir::Left);
    snake::step(game);
    assert(game.body.front().x == 6 && game.body.front().y == 12);

    // 输入是队列：一帧内压「上、左」，两步之内先上后左，不会只认后一键。
    snake::press(game, snake::Dir::Up);
    snake::press(game, snake::Dir::Left);
    snake::step(game);
    assert(game.body.front().x == 6 && game.body.front().y == 11);
    snake::step(game);
    assert(game.body.front().x == 5 && game.body.front().y == 11);

    // 把食物摆到前进方向上：吃到就变长、得分、加速。
    auto length = game.body.size();
    game.food = snake::Cell{4, 11};
    snake::step(game);
    assert(game.body.size() == length + 1);
    assert(game.score == 10);
    assert(game.stepTime < 0.12f);

    // 一路向左，撞到墙为止；撞死那一步头不入队。
    while (game.body.front().x > 0) snake::step(game);
    snake::step(game);
    assert(game.dead);
    assert(game.body.front().x == 0);

    return 0;
}
