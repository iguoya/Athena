// 第三章：让「蛇」存在——三节身体，能转向，撞墙会死。
// 蛇身是一条队列：头进尾出，整体前移。方向在这一章是直接改写的：
// IsKeyPressed 检测到就写 heading，没有缓冲。
// 〔已知 bug，有意留在这里〕快速按两下键（比如「上、左」），两帧内方向连改两次，
// 蛇会在一步之内掉头，头叠进自己的身体——画面上蛇身折叠。它不是崩溃，
// 但它是错的。第四章的输入缓冲就是为这个 bug 发明的。
// 界面文字用英文，理由同第一章。

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

struct Game {
    std::deque<Cell> body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};  // 头在 front
    Direction heading = Right;
    bool dead = false;
};

void step(Game& game) {
    if (game.dead) return;
    Cell head{game.body.front().x + DELTA[game.heading].x,
              game.body.front().y + DELTA[game.heading].y};
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS) {
        game.dead = true;  // 撞死那一步头不入队，蛇停在原地，画面才对得上死因
        return;
    }
    game.body.push_front(head);
    game.body.pop_back();  // 头进尾出：队列的进出就是蛇的移动
}

int main() {
    InitWindow(COLS * CELL, ROWS * CELL, "snake 03 - body");
    SetTargetFPS(60);

    Game game;
    const float stepTime = 0.12f;
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        // 方向直接改写。试试在两帧之内按「上、左」：蛇会当场折叠——这就是第四章要修的 bug。
        if (IsKeyPressed(KEY_RIGHT)) game.heading = Right;
        if (IsKeyPressed(KEY_LEFT)) game.heading = Left;
        if (IsKeyPressed(KEY_UP)) game.heading = Up;
        if (IsKeyPressed(KEY_DOWN)) game.heading = Down;
        if (game.dead && IsKeyPressed(KEY_R)) {
            game = Game{};  // 凑合的重开：整只换新。第六章用状态机正式收编它。
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
