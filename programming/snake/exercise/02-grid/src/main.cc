// 第二章：把世界变成格子，把时间变成节拍。
// 网格坐标（Cell）是逻辑世界，像素只是它每帧的投影；
// 逻辑按固定节拍走（5 Hz），渲染每一帧都跑（60 fps）——两者从这一章起正式分家。

#include "raylib.h"

// 「夜园」主题：全套课程共用的深色配色。每章是独立程序，各自带一份用到的颜色。
constexpr Color NIGHT {22, 27, 21, 255};      // 底色：近黑的绿
constexpr Color GRID {36, 44, 36, 255};       // 网格线：比底色略亮的绿
constexpr Color SNAKE {118, 200, 96, 255};    // 蛇园的草绿
constexpr Color INK {214, 224, 198, 255};     // 主要文字
constexpr Color INK_DIM {134, 146, 126, 255}; // 次要文字

constexpr int COLS = 32;
constexpr int ROWS = 24;
constexpr int CELL = 32;  // 32 x 24 格，每格 32 像素，正好 1024 x 768

struct Cell {
    int x = 0;
    int y = 0;
};

int main() {
    InitWindow(COLS * CELL, ROWS * CELL, "snake 02 - grid and tick");
    SetTargetFPS(60);

    Cell pos{0, 12};           // 逻辑位置，只在步进时变化
    const float stepTime = 0.2f;  // 每 0.2 秒走一格
    float acc = 0.0f;             // 累加器：攒够一个节拍，就走一步

    while (!WindowShouldClose()) {
        float dt = GetFrameTime();
        acc += dt;
        // 用 while 而不是 if：卡顿攒下两三个节拍时一次补齐，
        // 逻辑世界才不会因为渲染变慢而变慢。这是所有实时程序的时间模型。
        while (acc >= stepTime) {
            pos.x = (pos.x + 1) % COLS;
            acc -= stepTime;
        }

        BeginDrawing();
        ClearBackground(NIGHT);

        // 网格线只是画给人看的；逻辑世界里没有线，只有格子。
        for (int c = 1; c < COLS; ++c) {
            DrawLine(c * CELL, 0, c * CELL, ROWS * CELL, GRID);
        }
        for (int r = 1; r < ROWS; ++r) {
            DrawLine(0, r * CELL, COLS * CELL, r * CELL, GRID);
        }

        DrawRectangle(pos.x * CELL, pos.y * CELL, CELL, CELL, SNAKE);
        DrawText("logic ticks at 5 Hz, drawing runs at 60 fps", 24, 24, 18, INK);
        DrawText(TextFormat("cell (%d, %d)", pos.x, pos.y), 24, 52, 16, INK_DIM);

        EndDrawing();
    }

    CloseWindow();
    return 0;
}
