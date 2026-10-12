// 第四章：修一个第三章留下的 bug——快速按两下键，蛇在一步之内掉头，身体折叠。
// 修法不是「加判断」，是多加一条队列：按键不直接改方向，排进 pending；
// 逻辑每步只消费一个；反向的输入在压队时丢弃。
// 缓冲容量三格：太深则早先按下的方向很久才生效，手感发飘。
// 撞墙判定沿用第三章。重开的凑合也还在，第六章收编。

#include "raylib.h"

#include <deque>

// 「夜园」主题：全套课程共用的深色配色。每章是独立程序，各自带一份用到的颜色。
constexpr Color NIGHT {22, 27, 21, 255};      // 底色：近黑的绿
constexpr Color GRID {36, 44, 36, 255};       // 网格线：比底色略亮的绿
constexpr Color SNAKE {118, 200, 96, 255};    // 蛇园的草绿
constexpr Color EYE {18, 24, 18, 255};        // 眼睛：近黑
constexpr Color ALERT {228, 92, 78, 255};     // 死亡提示：苹果红
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
    std::deque<Cell> body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};  // 头在 front
    std::deque<Direction> pending;  // 输入缓冲：bug 的修在这里
    Direction heading = Right;
    bool dead = false;
};

// 反向的输入在压队时丢弃——蛇不能在自己的头里穿过自己。
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
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS) {
        game.dead = true;
        return;
    }
    game.body.push_front(head);
    game.body.pop_back();
}

int main() {
    InitWindow(COLS * CELL, ROWS * CELL, "snake 04 - input buffer");
    SetTargetFPS(60);

    Game game;
    const float stepTime = 0.18f;
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        if (IsKeyPressed(KEY_RIGHT) || IsKeyPressed(KEY_D)) press(game, Right);
        if (IsKeyPressed(KEY_LEFT) || IsKeyPressed(KEY_A)) press(game, Left);
        if (IsKeyPressed(KEY_UP) || IsKeyPressed(KEY_W)) press(game, Up);
        if (IsKeyPressed(KEY_DOWN) || IsKeyPressed(KEY_S)) press(game, Down);
        if (game.dead && IsKeyPressed(KEY_R)) {
            game = Game{};
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
        if (game.dead) {
            DrawText("DEAD - press R to restart", 24, 24, 20, ALERT);
        }
        DrawText(TextFormat("body %d", (int)game.body.size()), 24, 56, 16, INK_DIM);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
