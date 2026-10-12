// 第三章：让「蛇」存在——三节身体，能转向，撞墙会死。
// 蛇身是一条队列：头进尾出，整体前移。方向在这一章是直接改写的：
// IsKeyPressed 检测到就写 heading，没有缓冲。
// 〔已知 bug，有意留在这里〕快速按两下键（比如「上、左」），两帧内方向连改两次，
// 蛇会在一步之内掉头，头叠进自己的身体——画面上蛇身折叠。它不是崩溃，
// 但它是错的。第四章的输入缓冲就是为这个 bug 发明的。
// 界面文字用英文，理由同第一章。

#include "raylib.h"

#include <deque>

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
        ClearBackground(RAYWHITE);
        for (const Cell& part : game.body) {
            DrawRectangle(part.x * CELL, part.y * CELL, CELL, CELL, GREEN);
        }
        DrawCircle(game.body.front().x * CELL + CELL / 2 + DELTA[game.heading].x * 5,
                   game.body.front().y * CELL + CELL / 2 + DELTA[game.heading].y * 5, 3.0f, DARKGREEN);
        if (game.dead) {
            DrawText("DEAD - press R to restart", 24, 24, 20, MAROON);
        }
        DrawText(TextFormat("body %d", (int)game.body.size()), 24, 48, 16, GRAY);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
