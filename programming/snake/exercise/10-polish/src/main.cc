// 完成版：给规则配上一双好看的手。
// 相对第九章的三件事：
//   1. 插值渲染——逻辑 5~16 Hz，画面 60 fps，蛇身在两步之间滑动而不是跳格；
//   2. 声音——数字音频的最小模型：声音就是一列采样值，运行时合成，不需要音频文件；
//   3. 规则自己也在演化——logic.hh 长出「吃到加速」，测试跟着长出一条断言。
// 画面还换上全套课程共用的「夜园」深色主题：双色格棋盘、渐变的蛇身、呼吸的苹果——
// 这些都只在呈现层，logic.hh 与测试对此一无所知。
// 输入也长了一源：USB 手柄（XInput）——D-pad/左摇杆转向、A 开始/重开、Start 暂停；
// 仍只是输入映射，汇进同一条 press 队列，规则层不知道玩家用的是键盘还是手柄。
// 界面文字仍是英文，理由同第一章。

#include "../logic.hh"

#include "raylib.h"

#if defined(_WIN32)
// GLFW 的 gamepad 接口只认「有映射的 XInput 手柄」；直插的 HID 手柄（DirectInput 类）
// XInput 不认，raylib 便看不见它。Windows 自带的老游戏杆接口（winmm）认这类手柄，
// 这里轮询它做兜底。其它平台 GLFW 走 evdev / IOHID，这类手柄原生可见，无需兜底。
// 下面一组 NO* 宏把 winuser/winmm 里与 raylib 同名的 API（CloseWindow、DrawText、
// PlaySound 等）挡在声明之外——本程序用不到它们，留着只会撞名。
#define NOMINMAX
#define NOGDI
#define NOUSER
#define NOSOUND
#define NOMMIDS
#define MMNOSOUND
#define NOMCX
#include <windows.h>
#include <mmsystem.h>
#endif

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <deque>

constexpr int CELL = 32;
constexpr const char* HIGHSCORE_FILE = "snake-highscore.txt";

// 「夜园」主题色板：全套课程共用的一副深色配色，本章把它铺满。
constexpr Color NIGHT {22, 27, 21, 255};        // 底色：近黑的绿
constexpr Color LAWN_A {31, 39, 30, 255};       // 棋盘浅格
constexpr Color LAWN_B {26, 33, 25, 255};       // 棋盘深格
constexpr Color SNAKE_HEAD {158, 224, 118, 255}; // 蛇头：亮草绿
constexpr Color SNAKE_TAIL {64, 124, 60, 255};  // 蛇尾：暗绿
constexpr Color FADED {104, 112, 100, 255};     // 死后整条褪成的灰绿
constexpr Color EYE {18, 24, 18, 255};          // 眼睛：近黑
constexpr Color APPLE {228, 92, 78, 255};       // 苹果红
constexpr Color APPLE_SHINE {255, 190, 172, 255}; // 苹果高光
constexpr Color CARD {38, 47, 37, 252};         // 提示卡片：比底色亮一档
constexpr Color INK {214, 224, 198, 255};       // 主要文字
constexpr Color INK_DIM {134, 146, 126, 255};   // 次要文字
constexpr Color AMBER {234, 188, 92, 255};      // 最高分：琥珀金

// 颜色也要插值：蛇身的渐变就是从头色到尾色的 t。
Color blend(Color a, Color b, float t) {
    auto mix = [t](unsigned char x, unsigned char y) {
        return static_cast<unsigned char>(x + (y - x) * t);
    };
    return Color{mix(a.r, b.r), mix(a.g, b.g), mix(a.b, b.b), mix(a.a, b.a)};
}

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
    snake::reset(game);  // 开机先摆出初始局面：Ready 相的画面要画蛇与食物，而 Game 默认构造是空局面
    int best = load_best();
    Phase phase = Phase::Ready;

    std::deque<snake::Cell> previous;  // 上一步的蛇身，插值的起点
    float acc = 0.0f;

    // 手柄（若插着）与键盘汇入同一条 press 队列——输入源不同，规则不变。
    // 左摇杆是持续量不是按键：只在「指向哪边发生变化」的沿上入队一次，
    // 否则按住不放会每帧灌缓冲，把玩家提前排好的转向顶掉。死区滤掉静置噪声。
    int stickDir = -1;  // 上一帧摇杆方向：0 右 1 左 2 上 3 下，-1 死区
    auto stick_poll = [&]() {
        if (!IsGamepadAvailable(0)) return;
        const float ax = GetGamepadAxisMovement(0, GAMEPAD_AXIS_LEFT_X);
        const float ay = GetGamepadAxisMovement(0, GAMEPAD_AXIS_LEFT_Y);
        int dir = -1;
        if (fabsf(ax) > 0.35f || fabsf(ay) > 0.35f)
            dir = fabsf(ax) > fabsf(ay) ? (ax > 0 ? 0 : 1) : (ay > 0 ? 3 : 2);
        if (dir != stickDir) {
            stickDir = dir;
            if (dir == 0) snake::press(game, snake::Dir::Right);
            else if (dir == 1) snake::press(game, snake::Dir::Left);
            else if (dir == 2) snake::press(game, snake::Dir::Up);
            else if (dir == 3) snake::press(game, snake::Dir::Down);
        }
    };

#if defined(_WIN32)
    // winmm 兜底手柄：开机选一个有响应的游戏杆 id（不做热插拔——XInput 路径仍支持；
    // HID 手柄请插好再启动）。POV 十字与轴合成同一个方向变化沿；键位约定：
    // 1 号键=开始/重开，2 号键=暂停/继续（转向全靠 POV 与轴，各手柄 POV 最可靠）。
    UINT padId = 0;
    bool padFound = false;
    int padDir = -1;
    UINT padButtons = 0;
    JOYINFOEX ji{};
    ji.dwSize = sizeof(ji);
    ji.dwFlags = JOY_RETURNALL | JOY_RETURNPOV;
    for (UINT id = 0; id < joyGetNumDevs(); ++id) {
        if (joyGetPosEx(id, &ji) == JOYERR_NOERROR) { padId = id; padFound = true; break; }
    }
#else
    const bool padStart = false;
    const bool padPause = false;
    const int padDirHit = -1;
#endif

    while (!WindowShouldClose()) {
#if defined(_WIN32)
        bool padStart = false;
        bool padPause = false;
        int padDirHit = -1;
        if (padFound && joyGetPosEx(padId, &ji) == JOYERR_NOERROR) {
            int dir = -1;
            if (ji.dwPOV != JOY_POVCENTERED) {
                const int deg = static_cast<int>(ji.dwPOV / 100);  // 0 上 / 90 右 / 180 下 / 270 左
                dir = (deg < 45 || deg > 315) ? 2 : (deg < 135 ? 0 : (deg < 225 ? 3 : 1));
            } else {
                const float ax = (ji.dwXpos - 32768.0f) / 32768.0f;
                const float ay = (ji.dwYpos - 32768.0f) / 32768.0f;
                if (fabsf(ax) > 0.35f || fabsf(ay) > 0.35f)
                    dir = fabsf(ax) > fabsf(ay) ? (ax > 0 ? 0 : 1) : (ay > 0 ? 3 : 2);
            }
            if (dir != padDir) { padDir = dir; padDirHit = dir; }
            const UINT hit = ji.dwButtons & ~padButtons;  // 本帧新按下的位
            padButtons = ji.dwButtons;
            padStart = (hit & JOY_BUTTON1) != 0;
            padPause = (hit & JOY_BUTTON2) != 0;
        }
#endif
        if (phase == Phase::Ready || phase == Phase::Over) {
            if (IsKeyPressed(KEY_ENTER) || IsKeyPressed(KEY_SPACE)
                || IsGamepadButtonPressed(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
                || padStart) {
                snake::reset(game);
                previous = game.body;
                phase = Phase::Playing;
            }
        } else if (phase == Phase::Playing) {
            if (IsKeyPressed(KEY_P) || IsGamepadButtonPressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT) || padPause) {
                phase = Phase::Paused;
            } else {
                if (IsKeyPressed(KEY_D) || IsKeyPressed(KEY_RIGHT)
                    || IsGamepadButtonPressed(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT)) snake::press(game, snake::Dir::Right);
                if (IsKeyPressed(KEY_A) || IsKeyPressed(KEY_LEFT)
                    || IsGamepadButtonPressed(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT)) snake::press(game, snake::Dir::Left);
                if (IsKeyPressed(KEY_W) || IsKeyPressed(KEY_UP)
                    || IsGamepadButtonPressed(0, GAMEPAD_BUTTON_LEFT_FACE_UP)) snake::press(game, snake::Dir::Up);
                if (IsKeyPressed(KEY_S) || IsKeyPressed(KEY_DOWN)
                    || IsGamepadButtonPressed(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN)) snake::press(game, snake::Dir::Down);
                stick_poll();
                if (padDirHit >= 0) {
                    const snake::Dir PAD_DIR[4] = {snake::Dir::Right, snake::Dir::Left, snake::Dir::Up, snake::Dir::Down};
                    snake::press(game, PAD_DIR[padDirHit]);
                }
            }
        } else if (phase == Phase::Paused) {
            if (IsKeyPressed(KEY_P) || IsGamepadButtonPressed(0, GAMEPAD_BUTTON_MIDDLE_RIGHT) || padPause) phase = Phase::Playing;
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
        ClearBackground(NIGHT);
        // 棋盘铺成双色格的园圃：纯装饰，逻辑世界里仍然只有格子。
        DrawRectangle(0, 0, width, height, LAWN_B);
        for (int row = 0; row < snake::ROWS; ++row) {
            for (int col = row % 2; col < snake::COLS; col += 2) {
                DrawRectangle(col * CELL, row * CELL, CELL, CELL, LAWN_A);
            }
        }
        // 蛇身：每一节的颜色从头色滑向尾色；死了就整条褪成灰。
        // 每节向四周多画一像素，插值滑动时相邻两节正好搭住，链身看起来是连续的。
        const int length = static_cast<int>(game.body.size());
        int index = 0;
        for (const snake::Cell& part : game.body) {
            const snake::Cell& from = index < (int)previous.size() ? previous[index] : part;
            float x = lerp((float)from.x, (float)part.x, t) * CELL;
            float y = lerp((float)from.y, (float)part.y, t) * CELL;
            float shade = length > 1 ? (float)index / (length - 1) : 0.0f;
            Color skin = game.dead ? FADED : blend(SNAKE_HEAD, SNAKE_TAIL, shade);
            DrawRectangleRounded(Rectangle{x - 1, y - 1, CELL + 2, CELL + 2}, 0.3f, 6, skin);
            index += 1;
        }
        {
            const snake::Cell& head = game.body.front();
            snake::Cell dir = snake::DELTA[snake::dir_index(game.heading)];
            float cx = (head.x + 0.5f) * CELL;
            float cy = (head.y + 0.5f) * CELL;
            // 两只眼：沿前进方向偏一点，再沿垂直方向分开两侧。
            float fx = dir.x * 6.5f;
            float fy = dir.y * 6.5f;
            float px = -dir.y * 7.0f;
            float py = dir.x * 7.0f;
            DrawCircleV(Vector2{cx + fx + px, cy + fy + py}, 3.4f, EYE);
            DrawCircleV(Vector2{cx + fx - px, cy + fy - py}, 3.4f, EYE);
        }
        {
            // 苹果轻轻呼吸：半径随时间摆动 ±8%；死后画面定格，呼吸停止。
            float pulse = game.dead ? 1.0f : 1.0f + 0.08f * std::sin((float)GetTime() * 4.0f);
            float radius = CELL * 0.40f * pulse;
            Vector2 center{(game.food.x + 0.5f) * CELL, (game.food.y + 0.5f) * CELL};
            DrawCircleV(center, radius, APPLE);
            DrawCircleV(Vector2{center.x - radius * 0.35f, center.y - radius * 0.35f}, radius * 0.22f, APPLE_SHINE);
        }
        // HUD：一条半透明的夜色横条，得分在左，最高分在右。
        DrawRectangleRounded(Rectangle{16, 14, width - 32, 44}, 0.5f, 8, Fade(NIGHT, 0.72f));
        DrawText(TextFormat("SCORE %d", game.score), 36, 26, 20, INK);
        DrawText(TextFormat("STEP %.0f ms", game.stepTime * 1000), 220, 28, 16, INK_DIM);
        DrawText(TextFormat("BEST %d", best), width - 140, 26, 20, AMBER);

        const char* title = nullptr;
        const char* sub = nullptr;
        if (phase == Phase::Ready) { title = "READY"; sub = "ENTER / A - start"; }
        if (phase == Phase::Paused) { title = "PAUSED"; sub = "P / Start - resume"; }
        if (phase == Phase::Over) { title = "GAME OVER"; sub = "ENTER / A - restart"; }
        if (title) {
            // 提示卡：全屏压暗，中央一张圆角卡片承载标题与按键提示。
            DrawRectangle(0, 0, width, height, Fade(NIGHT, 0.55f));
            const float cardWidth = 560;
            const float cardHeight = 128;
            float x0 = (width - cardWidth) / 2;
            float y0 = (height - cardHeight) / 2;
            DrawRectangleRounded(Rectangle{x0, y0, cardWidth, cardHeight}, 0.16f, 10, CARD);
            DrawText(title, (int)(x0 + (cardWidth - MeasureText(title, 34)) / 2), (int)y0 + 28, 34, INK);
            DrawText(sub, (int)(x0 + (cardWidth - MeasureText(sub, 18)) / 2), (int)y0 + 78, 18, INK_DIM);
        }
        EndDrawing();
    }

    UnloadSound(eat);
    UnloadSound(crash);
    CloseAudioDevice();
    CloseWindow();
    return 0;
}
