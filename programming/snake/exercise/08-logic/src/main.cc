// 第八章：把蛇的规则从窗口里搬出来。
// logic.hh 不 include 任何 raylib 类型——改规则从此不必开着窗口玩一遍才知道对错。
// main 从「整个游戏」瘦成三件事：收输入、管状态机、画出来。
// 文件 IO 和 phase 留在 main：它们是「这一局怎么呈现」的事，不是蛇的规则。
// 这一章只做搬运，不改行为。画面仍是跳格的，也是无声的——那是后面章的事。
// 测试是搬出来之后能干的第一件事，下一章单独讲。

#include "../logic.hh"

#include "raylib.h"

#include <cstdio>
#include <deque>

// 「夜园」主题：全套课程共用的深色配色。每章是独立程序，各自带一份用到的颜色。
constexpr Color NIGHT {22, 27, 21, 255};      // 底色：近黑的绿
constexpr Color GRID {36, 44, 36, 255};       // 网格线：比底色略亮的绿
constexpr Color SNAKE {118, 200, 96, 255};    // 蛇园的草绿
constexpr Color EYE {18, 24, 18, 255};        // 眼睛：近黑
constexpr Color APPLE {228, 92, 78, 255};     // 食物：苹果红
constexpr Color INK {214, 224, 198, 255};     // 主要文字

constexpr int CELL = 32;
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
    InitWindow(width, height, "snake 08 - logic out of the window");
    SetTargetFPS(60);

    snake::Game game;
    snake::reset(game);  // 开机先摆出初始局面：Ready 相的画面要画蛇与食物，而 Game 默认构造是空局面
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
        ClearBackground(NIGHT);
        for (int c = 1; c < snake::COLS; ++c) DrawLine(c * CELL, 0, c * CELL, snake::ROWS * CELL, GRID);
        for (int r = 1; r < snake::ROWS; ++r) DrawLine(0, r * CELL, snake::COLS * CELL, r * CELL, GRID);
        for (const snake::Cell& part : game.body) {
            DrawRectangle(part.x * CELL, part.y * CELL, CELL, CELL, SNAKE);
        }
        {
            const snake::Cell& head = game.body.front();
            snake::Cell dir = snake::DELTA[snake::dir_index(game.heading)];
            DrawCircle((head.x + 0.5f) * CELL + dir.x * 8, (head.y + 0.5f) * CELL + dir.y * 8, 4.5f, EYE);
        }
        DrawCircle(game.food.x * CELL + CELL / 2, game.food.y * CELL + CELL / 2, CELL * 0.38f, APPLE);
        DrawText(TextFormat("score %d    best %d", game.score, best), 24, 24, 18, INK);

        const char* hint = nullptr;
        if (phase == Phase::Ready) hint = "snake 08 - press ENTER to start";
        if (phase == Phase::Paused) hint = "PAUSED - press P to resume";
        if (phase == Phase::Over) hint = "GAME OVER - press ENTER to restart";
        if (hint) {
            DrawRectangle(0, height / 2 - 44, width, 88, Fade(NIGHT, 0.8f));
            DrawText(hint, 24, height / 2 - 12, 24, INK);
        }
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
