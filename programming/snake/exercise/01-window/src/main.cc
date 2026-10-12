// 第一章：先开出一扇窗，把「每一帧都在重画」看见。
// raylib 是 immediate mode：没有控件、没有回调，只有一个每帧从头画一遍的循环。
// 界面文字用英文——raylib 默认字体只带 ASCII，中文化要 LoadFontEx 加载 TTF，
// 那是「资源管线」的事，不在这个入门章里。

#include "raylib.h"

int main() {
    const int screenWidth = 640;
    const int screenHeight = 480;
    InitWindow(screenWidth, screenHeight, "snake 01 - window");
    SetTargetFPS(60);

    // 帧计数与累计时间只用来证明循环在跑：画面上会动的东西，全是它们的函数。
    int frames = 0;
    double elapsed = 0.0;

    while (!WindowShouldClose()) {
        // dt 是上一帧花掉的秒数。现在还用不上它，但每帧都问一次，
        // 是这个循环的固定动作——从下一章起它就是逻辑的时间基准。
        float dt = GetFrameTime();
        elapsed += dt;
        frames += 1;

        BeginDrawing();
        ClearBackground(RAYWHITE);

        DrawText("snake 01: the loop is running", 24, 24, 20, DARKGREEN);
        DrawText(TextFormat("frame %d   elapsed %.2f s   dt %.4f s", frames, elapsed, dt), 24, 56, 16, GRAY);

        // 方块的 x 由累计时间决定。每帧重画同一个函数，位置自然随时间走——
        // 在 immediate mode 里「动画」就是这件事，没有补间、没有失效区域、没有别的机制。
        int x = static_cast<int>(elapsed * 120.0) % (screenWidth - 80);
        DrawRectangle(x, 200, 80, 40, GREEN);

        DrawFPS(24, screenHeight - 32);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
