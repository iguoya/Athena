// 完成版：给规则配上一双好看的手。
// 相对第九章的三件事：
//   1. 插值渲染——逻辑 5~16 Hz，画面 60 fps，蛇身在两步之间滑动而不是跳格；
//   2. 声音——数字音频的最小模型：声音就是一列采样值，运行时合成，不需要音频文件；
//   3. 规则自己也在演化——logic.hh 长出「吃到加速」，测试跟着长出一条断言。
// 界面文字仍是英文，理由同第一章。

#include "../logic.hh"

#include "raylib.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <deque>

constexpr int CELL = 20;
constexpr const char* HIGHSCORE_FILE = "snake-highscore.txt";

enum class Phase { Ready, Playing, Paused, Over };

float lerp(float a, float b, float t) { return a + (b - a) * t; }

// 声音就是一列采样值：频率决定音高，指数衰减决定「叮」的短促感。
// 合成完立刻交给 raylib 拷贝成 Sound，原来的内存随即释放。
Sound make_beep(float freq, float seconds) {
    const int sampleRate = 22050;
    int count = static_cast<int>(sampleRate * seconds);
    short* samples = static_cast<short*>(malloc(sizeof(short) * count));
    for (int i = 0; i < count; ++i) {
        float t = static_cast<float>(i) / sampleRate;
        float decay = std::exp(-t * 18.0f);
        samples[i] = static_cast<short>(32767.0f * 0.4f * decay * std::sin(2.0f * PI * freq * t));
    }
    Wave wave{};
    wave.frameCount = count;
    wave.sampleRate = sampleRate;
    wave.sampleSize = 16;
    wave.channels = 1;
    wave.data = samples;
    Sound sound = LoadSoundFromWave(wave);
    UnloadWave(wave);
    return sound;
}

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
    InitWindow(width, height, "snake 10 - polish");
    SetTargetFPS(60);
    InitAudioDevice();
    Sound eat = make_beep(660.0f, 0.12f);
    Sound crash = make_beep(110.0f, 0.3f);

    snake::Game game;
    int best = load_best();
    Phase phase = Phase::Ready;

    std::deque<snake::Cell> previous;  // 上一步的蛇身，插值的起点
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        if (phase == Phase::Ready || phase == Phase::Over) {
            if (IsKeyPressed(KEY_ENTER) || IsKeyPressed(KEY_SPACE)) {
                snake::reset(game);
                previous = game.body;
                phase = Phase::Playing;
            }
        } else if (phase == Phase::Playing) {
            if (IsKeyPressed(KEY_P)) {
                phase = Phase::Paused;
            } else {
                if (IsKeyPressed(KEY_D) || IsKeyPressed(KEY_RIGHT)) snake::press(game, snake::Dir::Right);
                if (IsKeyPressed(KEY_A) || IsKeyPressed(KEY_LEFT)) snake::press(game, snake::Dir::Left);
                if (IsKeyPressed(KEY_W) || IsKeyPressed(KEY_UP)) snake::press(game, snake::Dir::Up);
                if (IsKeyPressed(KEY_S) || IsKeyPressed(KEY_DOWN)) snake::press(game, snake::Dir::Down);
            }
        } else if (phase == Phase::Paused) {
            if (IsKeyPressed(KEY_P)) phase = Phase::Playing;
        }

        float dt = GetFrameTime();
        if (phase == Phase::Playing) {
            acc += dt;
            while (acc >= game.stepTime) {
                previous = game.body;
                snake::step(game);
                acc -= game.stepTime;
                // 音效是 step 的观察输出，必须在这一步之内判断：放到循环外，两步之间
                // 的每个渲染帧都会看到「蛇比 previous 长」，一口食物会连响好几次。
                if (game.body.size() > previous.size()) PlaySound(eat);  // 长了一节，就是吃到了
                if (game.dead) {
                    PlaySound(crash);
                    phase = Phase::Over;
                    if (game.score > best) {
                        best = game.score;
                        char text[16];
                        snprintf(text, sizeof text, "%d", best);
                        SaveFileText(HIGHSCORE_FILE, text);
                    }
                    break;  // 死了就不再补步，撞墙声也只响这一次
                }
            }
        } else {
            acc = 0.0f;
            previous = game.body;
        }

        // 插值比例：攒到下一次步进走了几分之几。渲染帧远快于逻辑步，这一格就是平滑的来源。
        float t = phase == Phase::Playing ? acc / game.stepTime : 1.0f;

        BeginDrawing();
        ClearBackground(RAYWHITE);
        int index = 0;
        for (const snake::Cell& part : game.body) {
            const snake::Cell& from = index < (int)previous.size() ? previous[index] : part;
            float x = lerp((float)from.x, (float)part.x, t) * CELL;
            float y = lerp((float)from.y, (float)part.y, t) * CELL;
            DrawRectangleRounded(Rectangle{x, y, CELL, CELL}, 0.5f, 8, GREEN);
            index += 1;
        }
        {
            const snake::Cell& head = game.body.front();
            snake::Cell dir = snake::DELTA[snake::dir_index(game.heading)];
            float cx = (head.x + 0.5f) * CELL;
            float cy = (head.y + 0.5f) * CELL;
            // 两只眼：沿前进方向偏一点，再沿垂直方向分开两侧。
            float fx = dir.x * 4.0f;
            float fy = dir.y * 4.0f;
            float px = -dir.y * 4.5f;
            float py = dir.x * 4.5f;
            DrawCircleV(Vector2{cx + fx + px, cy + fy + py}, 2.2f, DARKGREEN);
            DrawCircleV(Vector2{cx + fx - px, cy + fy - py}, 2.2f, DARKGREEN);
        }
        DrawRectangle(game.food.x * CELL, game.food.y * CELL, CELL, CELL, MAROON);
        DrawText(TextFormat("score %d    best %d    step %.0f ms", game.score, best, game.stepTime * 1000), 24, 24, 16, DARKGREEN);

        const char* hint = nullptr;
        if (phase == Phase::Ready) hint = "snake 10 - press ENTER to start";
        if (phase == Phase::Paused) hint = "PAUSED - press P to resume";
        if (phase == Phase::Over) hint = "GAME OVER - press ENTER to restart";
        if (hint) {
            DrawRectangle(0, 200, width, 80, Fade(RAYWHITE, 0.85f));
            DrawText(hint, 24, 232, 24, MAROON);
        }
        EndDrawing();
    }

    UnloadSound(eat);
    UnloadSound(crash);
    CloseAudioDevice();
    CloseWindow();
    return 0;
}
