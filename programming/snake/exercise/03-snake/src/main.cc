// 第三章：一条蛇是两条队列，随机是一门学问。
// 蛇身是 deque（头进尾出，吃食物时尾不出）；按键是另一条队列（每步只消费一个）。
// 两条队列把贪吃蛇最经典的两个 bug 挡在门外：一帧内掉头自杀、一帧内两键只认后一个。
// 撞墙或咬到自己就停；按 R 重开。状态机的整理留到第四章。

#include "raylib.h"

#include <deque>
#include <random>

constexpr int COLS = 32;
constexpr int ROWS = 24;
constexpr int CELL = 20;

struct Cell {
    int x = 0;
    int y = 0;
    bool operator==(const Cell& other) const { return x == other.x && y == other.y; }
};

enum Direction { Right, Left, Up, Down };
constexpr Cell DELTA[] = {{1, 0}, {-1, 0}, {0, -1}, {0, 1}};
constexpr Direction OPPOSITE[] = {Left, Right, Down, Up};

struct Game {
    std::deque<Cell> body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};  // 头在 front
    std::deque<Direction> pending;   // 输入缓冲
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

// 食物必须落在空格上。盘面还很大，失败重试即可；等蛇快占满全场才值得换算法。
void spawn_food(Game& game) {
    std::uniform_int_distribution<int> col(0, COLS - 1);
    std::uniform_int_distribution<int> row(0, ROWS - 1);
    do {
        game.food = Cell{col(game.rng), row(game.rng)};
    } while (occupies(game, game.food));
}

void reset(Game& game) {
    game.body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};
    game.pending.clear();
    game.heading = Right;
    game.dead = false;
    spawn_food(game);
}

// 按键不直接改方向，只排队。反向的输入丢掉——蛇不能在自己的头里穿过自己。
void press(Game& game, Direction dir) {
    Direction last = game.pending.empty() ? game.heading : game.pending.back();
    if (dir == last || dir == OPPOSITE[last]) return;
    if (game.pending.size() >= 3) return;  // 缓冲太深会让手感发飘
    game.pending.push_back(dir);
}

// 逻辑前进一步。只在节拍到点时被调用，与帧率无关。
void step(Game& game) {
    if (game.dead) return;
    if (!game.pending.empty()) {
        game.heading = game.pending.front();
        game.pending.pop_front();
    }
    Cell head{game.body.front().x + DELTA[game.heading].x,
              game.body.front().y + DELTA[game.heading].y};
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS || occupies(game, head)) {
        game.dead = true;  // 注意：撞死时头不入队，蛇停在原地，画面才对得上死因
        return;
    }
    game.body.push_front(head);
    if (head == game.food) {
        spawn_food(game);      // 吃到食物：尾不出队，蛇自然长了一节
    } else {
        game.body.pop_back();  // 没吃到：头进尾出，等于整体前移一格
    }
}

int main() {
    InitWindow(COLS * CELL, ROWS * CELL, "snake 03 - body and input");
    SetTargetFPS(60);

    Game game;
    const float stepTime = 0.12f;
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        if (IsKeyPressed(KEY_RIGHT)) press(game, Right);
        if (IsKeyPressed(KEY_LEFT)) press(game, Left);
        if (IsKeyPressed(KEY_UP)) press(game, Up);
        if (IsKeyPressed(KEY_DOWN)) press(game, Down);
        if (game.dead && IsKeyPressed(KEY_R)) reset(game);

        float dt = GetFrameTime();
        acc += dt;
        while (!game.dead && acc >= stepTime) {
            step(game);
            acc -= stepTime;
        }

        BeginDrawing();
        ClearBackground(RAYWHITE);
        for (const Cell& part : game.body) {
            DrawRectangle(part.x * CELL, part.y * CELL, CELL, CELL, GREEN);
        }
        // 眼睛画在头上，方向才看得出来
        DrawCircle(game.body.front().x * CELL + CELL / 2 + DELTA[game.heading].x * 5,
                   game.body.front().y * CELL + CELL / 2 + DELTA[game.heading].y * 5, 3.0f, DARKGREEN);
        DrawRectangle(game.food.x * CELL, game.food.y * CELL, CELL, CELL, MAROON);

        if (game.dead) {
            DrawText("DEAD - press R to restart", 24, 24, 20, MAROON);
        }
        DrawText(TextFormat("body %d", (int)game.body.size()), 24, 48, 16, GRAY);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
