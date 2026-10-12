// 规则的设计验证：把 docs/design/overview.md 里的需求、不变式逐条变成可执行的检查。
// 与 logic_test.cc 的分工：logic_test 是第九、十章一路长出来的「冒烟测试」，讲法不动；
// 这一份按需求编号铺开边界，每个用例上方的 @covers 标出它验证哪条需求，
// scripts/check.py 会核对这些标记与总览里的追溯矩阵一致。
//
// 不用 assert：Release 构建定义 NDEBUG 后 assert 整个消失，测试就成了空壳。

#include "../logic.hh"

#include <cstdio>
#include <cstdlib>
#include <initializer_list>
#include <random>

#define CHECK(cond)                                                              \
    do {                                                                         \
        if (!(cond)) {                                                           \
            std::fprintf(stderr, "%s:%d: CHECK 失败: %s\n", __FILE__, __LINE__, #cond); \
            std::exit(1);                                                        \
        }                                                                        \
    } while (0)

using snake::Cell;
using snake::Dir;
using snake::Game;

namespace {

// 摆一个确定的局面：食物放在远处，免得被无关的一步吃到。
void place(Game& game, std::initializer_list<Cell> cells, Dir heading) {
    snake::reset(game);
    game.body.assign(cells.begin(), cells.end());
    game.heading = heading;
    game.pending.clear();
    game.food = Cell{20, 20};
}

// 设计总览「数据与不变式」一节的 I-1 ~ I-7，任何时刻都必须成立。
void check_invariants(const Game& game) {
    // I-1 蛇身非空，相邻两节恰好相接
    CHECK(!game.body.empty());
    for (size_t i = 1; i < game.body.size(); ++i) {
        int dx = game.body[i].x - game.body[i - 1].x;
        int dy = game.body[i].y - game.body[i - 1].y;
        CHECK((dx < 0 ? -dx : dx) + (dy < 0 ? -dy : dy) == 1);
    }
    // I-2 每一节都在界内
    for (const Cell& part : game.body) {
        CHECK(part.x >= 0 && part.x < snake::COLS && part.y >= 0 && part.y < snake::ROWS);
    }
    // I-3 蛇身没有重叠的两节
    for (size_t i = 0; i < game.body.size(); ++i) {
        for (size_t j = i + 1; j < game.body.size(); ++j) CHECK(!(game.body[i] == game.body[j]));
    }
    // I-4 食物在界内，且不压在蛇身上
    CHECK(game.food.x >= 0 && game.food.x < snake::COLS && game.food.y >= 0 && game.food.y < snake::ROWS);
    CHECK(!snake::occupies(game, game.food));
    // I-5 缓冲不超过三格，且每一格相对前一格既不重复也不反向
    CHECK(game.pending.size() <= 3);
    Dir previous = game.heading;
    for (Dir d : game.pending) {
        CHECK(d != previous && d != snake::OPPOSITE[snake::dir_index(previous)]);
        previous = d;
    }
    // I-6 步长始终在 [0.06, 0.12]
    CHECK(game.stepTime >= 0.06f && game.stepTime <= 0.12f);
    // I-7 长度与得分同步：初始三节，每吃一口多一节、多十分
    CHECK(static_cast<int>(game.body.size()) == 3 + game.score / 10);
}

// @covers FR-1
void test_advance_one_cell() {
    Game game;
    place(game, {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}}, Dir::Right);
    snake::step(game);
    CHECK(game.body.front() == (Cell{6, 12}));
    CHECK(game.body.size() == 3);        // 没吃到，尾巴出队，长度不变
    CHECK(game.body.back() == (Cell{4, 12}));
    CHECK(!game.dead);
}

// @covers FR-2
void test_input_rejects_reverse_and_duplicate() {
    Game game;
    place(game, {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}}, Dir::Right);
    snake::press(game, Dir::Right);  // 与当前朝向相同
    snake::press(game, Dir::Left);   // 与当前朝向相反
    CHECK(game.pending.empty());

    snake::press(game, Dir::Up);
    snake::press(game, Dir::Down);   // 相对队尾（Up）是反向
    snake::press(game, Dir::Up);     // 相对队尾是重复
    CHECK(game.pending.size() == 1);
}

// @covers FR-2
void test_input_capacity_and_one_per_step() {
    Game game;
    place(game, {Cell{10, 10}, Cell{9, 10}, Cell{8, 10}}, Dir::Right);
    snake::press(game, Dir::Up);
    snake::press(game, Dir::Left);
    snake::press(game, Dir::Down);
    snake::press(game, Dir::Right);  // 队列已满三格，第四个被丢弃
    CHECK(game.pending.size() == 3);

    snake::step(game);               // 每步只消费一格
    CHECK(game.pending.size() == 2);
    CHECK(game.heading == Dir::Up);
    snake::press(game, Dir::Right);  // 腾出一格，又能收
    CHECK(game.pending.size() == 3);
}

// @covers FR-3
void test_eat_grows_scores_speeds_up() {
    Game game;
    place(game, {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}}, Dir::Right);
    game.food = Cell{6, 12};
    snake::step(game);
    CHECK(game.body.size() == 4);
    CHECK(game.score == 10);
    CHECK(game.stepTime < 0.1177f && game.stepTime > 0.1175f);  // 0.12 * 0.98
    CHECK(!snake::occupies(game, game.food));                    // 新食物不在蛇身上
    check_invariants(game);
}

// @covers FR-4
void test_wall_kills_on_all_four_sides() {
    struct Case { Cell head; Cell next; Cell tail; Dir dir; };
    const Case cases[] = {
        {{0, 5}, {1, 5}, {2, 5}, Dir::Left},
        {{31, 5}, {30, 5}, {29, 5}, Dir::Right},
        {{5, 0}, {5, 1}, {5, 2}, Dir::Up},
        {{5, 23}, {5, 22}, {5, 21}, Dir::Down},
    };
    for (const Case& c : cases) {
        Game game;
        place(game, {c.head, c.next, c.tail}, c.dir);
        snake::step(game);
        CHECK(game.dead);
        CHECK(game.body.front() == c.head);  // 撞死那一步头不入队
        CHECK(game.body.size() == 3);
    }
}

// @covers FR-4
void test_self_bite_kills() {
    Game game;
    // 头 (5,5) 向左，目标 (4,5) 是蛇身中间一节，不是尾巴。
    place(game, {Cell{5, 5}, Cell{5, 6}, Cell{4, 6}, Cell{4, 5}, Cell{4, 4}}, Dir::Left);
    snake::step(game);
    CHECK(game.dead);
    CHECK(game.body.front() == (Cell{5, 5}));
}

// @covers FR-4
void test_head_into_current_tail_cell_kills() {
    // 设计决策 D-3：判定先于尾巴出队，头进入「当前尾格」算撞死。
    // 这里用测试把它钉住；想改成允许追尾，要同时改 step 的顺序和这条测试。
    Game game;
    place(game, {Cell{1, 1}, Cell{1, 2}, Cell{2, 2}, Cell{2, 1}}, Dir::Right);
    snake::step(game);
    CHECK(game.dead);
}

// @covers FR-4
void test_step_after_death_is_noop() {
    Game game;
    place(game, {Cell{0, 5}, Cell{1, 5}, Cell{2, 5}}, Dir::Left);
    snake::step(game);
    CHECK(game.dead);
    auto frozen = game.body;
    int score = game.score;
    // 死后再按一个本来合法的转向：没有 dead 的早退，这一步就会沿墙活动起来。
    snake::press(game, Dir::Up);
    snake::step(game);
    CHECK(game.body == frozen);
    CHECK(game.score == score);
}

// @covers FR-5
void test_food_never_spawns_on_body() {
    Game game;
    game.rng.seed(1);
    // 只留一个空格：拒绝采样必须落在这唯一的空格上。
    const Cell holes[] = {{7, 7}, {0, 0}, {31, 23}, {0, 23}, {31, 0}};
    for (const Cell& hole : holes) {
        game.body.clear();
        for (int y = 0; y < snake::ROWS; ++y) {
            for (int x = 0; x < snake::COLS; ++x) {
                if (!(Cell{x, y} == hole)) game.body.push_back(Cell{x, y});
            }
        }
        snake::spawn_food(game);
        CHECK(game.food == hole);
    }
}

// @covers FR-6
void test_reset_restores_initial_state() {
    Game game;
    game.rng.seed(2);
    snake::reset(game);
    game.food = Cell{6, 12};
    snake::step(game);                  // 吃一口：分数、速度、长度都变了
    snake::press(game, Dir::Up);
    snake::reset(game);
    CHECK(game.body.size() == 3);
    CHECK(game.body.front() == (Cell{5, 12}));
    CHECK(game.heading == Dir::Right);
    CHECK(game.pending.empty());
    CHECK(game.score == 0);
    CHECK(game.stepTime == 0.12f);
    CHECK(!game.dead);
    check_invariants(game);
}

// @covers NFR-3
void test_speed_floor() {
    Game game;
    place(game, {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}}, Dir::Right);
    game.stepTime = 0.0601f;
    game.food = Cell{6, 12};
    snake::step(game);
    CHECK(game.stepTime >= 0.06f);
    game.stepTime = 0.06f;               // 已在下限：再吃也不会更小
    game.food = Cell{7, 12};
    snake::step(game);
    CHECK(game.stepTime >= 0.06f);
}

// @covers NFR-4
void test_invariants_hold_under_random_play() {
    // 固定种子的半贪心游走：七成时间朝食物拐，三成乱按。
    // 既能吃到（走过变长、加速、重刷食物），也会撞墙、咬自己。
    Game game;
    game.rng.seed(20261012);
    std::mt19937 pick(7);
    const Dir all[4] = {Dir::Right, Dir::Left, Dir::Up, Dir::Down};
    int eats = 0;
    int deaths = 0;
    for (int round = 0; round < 300; ++round) {
        snake::reset(game);
        for (int i = 0; i < 3000 && !game.dead; ++i) {
            if (pick() % 10 < 7) {
                const Cell head = game.body.front();
                Dir wanted[2];
                int n = 0;
                if (game.food.x > head.x) wanted[n++] = Dir::Right;
                if (game.food.x < head.x) wanted[n++] = Dir::Left;
                if (game.food.y > head.y) wanted[n++] = Dir::Down;
                if (game.food.y < head.y) wanted[n++] = Dir::Up;
                if (n > 0) snake::press(game, wanted[pick() % n]);
            } else {
                snake::press(game, all[pick() % 4]);
            }
            check_invariants(game);
            int before = game.score;
            snake::step(game);
            check_invariants(game);
            if (game.score > before) ++eats;
        }
        if (game.dead) ++deaths;
    }
    CHECK(eats > 0);    // 游走真的覆盖到了「吃到」
    CHECK(deaths > 0);  // 也覆盖到了「死亡」
}

}  // namespace

int main() {
    test_advance_one_cell();
    test_input_rejects_reverse_and_duplicate();
    test_input_capacity_and_one_per_step();
    test_eat_grows_scores_speeds_up();
    test_wall_kills_on_all_four_sides();
    test_self_bite_kills();
    test_head_into_current_tail_cell_kills();
    test_step_after_death_is_noop();
    test_food_never_spawns_on_body();
    test_reset_restores_initial_state();
    test_speed_floor();
    test_invariants_hold_under_random_play();
    std::puts("rules_test: 全部通过");
    return 0;
}
