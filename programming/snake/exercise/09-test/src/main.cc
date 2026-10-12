// 第九章：给搬出来的规则配上测试。
// logic.hh 不 include 任何 raylib 类型——改规则从此不必开着窗口玩一遍才知道对错。
// main 从「整个游戏」瘦成三件事：收输入、管状态机、画出来。
// 文件 IO 和 phase 留在 main：它们是「这一局怎么呈现」的事，不是蛇的规则。
// 这一章只做搬运，不改行为。画面仍是跳格的，也是无声的——那是后面章的事。
// 本章的程序与第八章逐行相同——差别全在 tests/：不开窗口就能断言规则。

#include "../logic.hh"

#include "raylib.h"

#include <cstdio>
#include <deque>

constexpr int CELL = 20;
constexpr const char* HIGHSCORE_FILE = "snake-highscore.txt";

enum class Phase { Ready, Playing, Paused, Over };

int load_best() {
    if (!FileExists(HIGHSCORE_FILE)) return 0;
    // LoadFileText 返回的是堆内存，用完要还给 UnloadFileText；读失败时返回空指针。
    char* text = LoadFileText(HIGHSCORE_FILE);
    if (text == nullptr) return 0;
    int best = atoi(text);
    UnloadFileText(text);
    return best;
}

int main() {
    const int width = snake::COLS * CELL;
    const int height = snake::ROWS * CELL;
    InitWindow(width, height, "snake 09 - tests");
    SetTargetFPS(60);

    snake::Game game;
    int best = load_best();
    Phase phase = Phase::Ready;
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        if (phase == Phase::Ready || phase == Phase::Over) {
            if (IsKeyPressed(KEY_ENTER) || IsKeyPressed(KEY_SPACE)) {
                snake::reset(game);
                phase = Phase::Playing;
            }
        } else if (phase == Phase::Playing) {
            if (IsKeyPressed(KEY_P)) {
                phase = Phase::Paused;
            } else {
                if (IsKeyPressed(KEY_RIGHT)) snake::press(game, snake::Dir::Right);
                if (IsKeyPressed(KEY_LEFT)) snake::press(game, snake::Dir::Left);
                if (IsKeyPressed(KEY_UP)) snake::press(game, snake::Dir::Up);
                if (IsKeyPressed(KEY_DOWN)) snake::press(game, snake::Dir::Down);
            }
        } else if (phase == Phase::Paused) {
            if (IsKeyPressed(KEY_P)) phase = Phase::Playing;
        }

        float dt = GetFrameTime();
        if (phase == Phase::Playing) {
            acc += dt;
            while (acc >= game.stepTime) {
                snake::step(game);
                acc -= game.stepTime;
                if (game.dead) {
                    phase = Phase::Over;
                    if (game.score > best) {
                        best = game.score;
                        char text[16];
                        snprintf(text, sizeof text, "%d", best);
                        SaveFileText(HIGHSCORE_FILE, text);
                    }
                }
            }
        } else {
            acc = 0.0f;
        }

        BeginDrawing();
        ClearBackground(RAYWHITE);
        for (const snake::Cell& part : game.body) {
            DrawRectangle(part.x * CELL, part.y * CELL, CELL, CELL, GREEN);
        }
        {
            const snake::Cell& head = game.body.front();
            snake::Cell dir = snake::DELTA[snake::dir_index(game.heading)];
            DrawCircle((head.x + 0.5f) * CELL + dir.x * 5, (head.y + 0.5f) * CELL + dir.y * 5, 3.0f, DARKGREEN);
        }
        DrawRectangle(game.food.x * CELL, game.food.y * CELL, CELL, CELL, MAROON);
        DrawText(TextFormat("score %d    best %d", game.score, best), 24, 24, 16, DARKGREEN);

        const char* hint = nullptr;
        if (phase == Phase::Ready) hint = "snake 09 - press ENTER to start";
        if (phase == Phase::Paused) hint = "PAUSED - press P to resume";
        if (phase == Phase::Over) hint = "GAME OVER - press ENTER to restart";
        if (hint) {
            DrawRectangle(0, 200, width, 80, Fade(RAYWHITE, 0.85f));
            DrawText(hint, 24, 232, 24, MAROON);
        }
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
