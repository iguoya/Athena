// 第三章：让「蛇」存在——固定长度，能转向，撞墙会死。
// 蛇身是一条队列（头进尾出，整体前移），按键排进另一条队列（每步只消费一个）。
// 这一章没有食物：蛇不会变长，也就不会咬到自己——「自吃」是下一章才诞生的死法。
// 死了按 R 重开，先用一行裸 if 凑合；等散装判断收拾不动了，第五章再收编它。
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
constexpr Direction OPPOSITE[] = {Left, Right, Down, Up};

struct Game {
    std::deque<Cell> body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};  // 头在 front
    std::deque<Direction> pending;
    Direction heading = Right;
    bool dead = false;
};

// 按键不直接改方向，只排队。反向的输入丢掉：固定长度的蛇一步掉头，
// 头会撞进自己的第二节——这个 bug 不需要变长就存在。
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
        if (IsKeyPressed(KEY_RIGHT)) press(game, Right);
        if (IsKeyPressed(KEY_LEFT)) press(game, Left);
        if (IsKeyPressed(KEY_UP)) press(game, Up);
        if (IsKeyPressed(KEY_DOWN)) press(game, Down);
        if (game.dead && IsKeyPressed(KEY_R)) {
            game = Game{};  // 凑合的重开：整只换新。第五章用状态机正式收编它。
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
