// 第五章：食物让蛇变长，变长让「咬到自己」成为新的死法。
// 吃到的本质不是「加一节」，而是「尾不出队」——少做一个动作，蛇就长了。
// 随机落点用 <random> 的引擎加分布，落在蛇身上就重试。
// 注意自吃判定是什么时候才需要的：固定长度的蛇（第三章）就算折叠也不会「死」，
// 变长之后头撞进身体才成为真实的死法。规则跟着世界的复杂度一起长。
// 撞墙与自吃写在同一个判定处：对蛇来说它们是同一件事——下一步的格子不合法。

#include "raylib.h"

#include <deque>
#include <random>

// 「夜园」主题：全套课程共用的深色配色。每章是独立程序，各自带一份用到的颜色。
constexpr Color NIGHT {22, 27, 21, 255};      // 底色：近黑的绿
constexpr Color GRID {36, 44, 36, 255};       // 网格线：比底色略亮的绿
constexpr Color SNAKE {118, 200, 96, 255};    // 蛇园的草绿
constexpr Color EYE {18, 24, 18, 255};        // 眼睛：近黑
constexpr Color APPLE {228, 92, 78, 255};     // 食物：苹果红
constexpr Color ALERT {228, 92, 78, 255};     // 死亡提示：同苹果红
constexpr Color INK_DIM {134, 146, 126, 255}; // 次要文字

constexpr int COLS = 32;
constexpr int ROWS = 24;
constexpr int CELL = 32;

struct Cell {
    int x = 0;
    int y = 0;
    bool operator==(const Cell& other) const { return x == other.x && y == other.y; }
};

enum Direction { Right, Left, Up, Down };
constexpr Cell DELTA[] = {{1, 0}, {-1, 0}, {0, -1}, {0, 1}};
constexpr Direction OPPOSITE[] = {Left, Right, Down, Up};

struct Game {
    std::deque<Cell> body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};
    std::deque<Direction> pending;
    Direction heading = Right;
    Cell food{20, 12};
    bool dead = false;
    std::mt19937 rng{std::random_device{}()};
};

bool occupies(const Game& game, Cell cell) {
    for (const Cell& part : game.body) {
        if (part == cell) return true;
    }
    return false;
}

// 食物必须落在空格上。盘面还很大，失败重试的期望次数接近 1；
// 等蛇快占满全场才值得换成「收集空格再抽样」。
void spawn_food(Game& game) {
    std::uniform_int_distribution<int> col(0, COLS - 1);
    std::uniform_int_distribution<int> row(0, ROWS - 1);
    do {
        game.food = Cell{col(game.rng), row(game.rng)};
    } while (occupies(game, game.food));
}

void press(Game& game, Direction dir) {
    Direction last = game.pending.empty() ? game.heading : game.pending.back();
    if (dir == last || dir == OPPOSITE[last]) return;
    if (game.pending.size() >= 3) return;
    game.pending.push_back(dir);
}

void step(Game& game) {
    if (game.dead) return;
    if (!game.pending.empty()) {
        game.heading = game.pending.front();
        game.pending.pop_front();
    }
    Cell head{game.body.front().x + DELTA[game.heading].x,
              game.body.front().y + DELTA[game.heading].y};
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS || occupies(game, head)) {
        game.dead = true;
        return;
    }
    game.body.push_front(head);
    if (head == game.food) {
        spawn_food(game);      // 吃到：尾不出队，蛇长了一节
    } else {
        game.body.pop_back();  // 没吃到：头进尾出
    }
}

int main() {
    InitWindow(COLS * CELL, ROWS * CELL, "snake 05 - food");
    SetTargetFPS(60);

    Game game;
    const float stepTime = 0.12f;
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        if (IsKeyPressed(KEY_RIGHT)) press(game, Right);
        if (IsKeyPressed(KEY_LEFT)) press(game, Left);
        if (IsKeyPressed(KEY_UP)) press(game, Up);
        if (IsKeyPressed(KEY_DOWN)) press(game, Down);
        if (game.dead && IsKeyPressed(KEY_R)) {
            game = Game{};  // 凑合的重开还在，第六章收编
        }

        float dt = GetFrameTime();
        acc += dt;
        while (!game.dead && acc >= stepTime) {
            step(game);
            acc -= stepTime;
        }

        BeginDrawing();
        ClearBackground(NIGHT);
        for (int c = 1; c < COLS; ++c) DrawLine(c * CELL, 0, c * CELL, ROWS * CELL, GRID);
        for (int r = 1; r < ROWS; ++r) DrawLine(0, r * CELL, COLS * CELL, r * CELL, GRID);
        for (const Cell& part : game.body) {
            DrawRectangle(part.x * CELL, part.y * CELL, CELL, CELL, SNAKE);
        }
        DrawCircle(game.body.front().x * CELL + CELL / 2 + DELTA[game.heading].x * 8,
                   game.body.front().y * CELL + CELL / 2 + DELTA[game.heading].y * 8, 4.5f, EYE);
        DrawCircle(game.food.x * CELL + CELL / 2, game.food.y * CELL + CELL / 2, CELL * 0.38f, APPLE);
        if (game.dead) {
            DrawText("DEAD - press R to restart", 24, 24, 20, ALERT);
        }
        DrawText(TextFormat("body %d", (int)game.body.size()), 24, 56, 16, INK_DIM);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
