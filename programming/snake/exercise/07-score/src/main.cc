// 第七章：把「玩得怎样」正式化——计分，以及一份留得住的最高分。
// 计分挂在「吃到」这个事件上；最高分在死亡那一步判定并写入文件。
// 最高分写在进程工作目录，是教学从简：工作目录随启动方式漂移、可能没有写权限、
// 多用户互相覆盖。真实程序应写用户数据目录（每用户一份、卸载不丢）。

#include "raylib.h"

#include <cstdio>
#include <deque>
#include <random>

// 「夜园」主题：全套课程共用的深色配色。每章是独立程序，各自带一份用到的颜色。
constexpr Color NIGHT {22, 27, 21, 255};      // 底色：近黑的绿
constexpr Color GRID {36, 44, 36, 255};       // 网格线：比底色略亮的绿
constexpr Color SNAKE {118, 200, 96, 255};    // 蛇园的草绿
constexpr Color EYE {18, 24, 18, 255};        // 眼睛：近黑
constexpr Color APPLE {228, 92, 78, 255};     // 食物：苹果红
constexpr Color INK {214, 224, 198, 255};     // 主要文字

constexpr int COLS = 32;
constexpr int ROWS = 24;
constexpr int CELL = 32;
constexpr const char* HIGHSCORE_FILE = "snake-highscore.txt";

struct Cell {
    int x = 0;
    int y = 0;
    bool operator==(const Cell& other) const { return x == other.x && y == other.y; }
};

enum Direction { Right, Left, Up, Down };
constexpr Cell DELTA[] = {{1, 0}, {-1, 0}, {0, -1}, {0, 1}};
constexpr Direction OPPOSITE[] = {Left, Right, Down, Up};

enum class Phase { Ready, Playing, Paused, Over };

struct Game {
    std::deque<Cell> body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};
    std::deque<Direction> pending;
    Direction heading = Right;
    Cell food{20, 12};
    int score = 0;
    int best = 0;
    Phase phase = Phase::Ready;
    std::mt19937 rng{std::random_device{}()};
};

bool occupies(const Game& game, Cell cell) {
    for (const Cell& part : game.body) {
        if (part == cell) return true;
    }
    return false;
}

void spawn_food(Game& game) {
    std::uniform_int_distribution<int> col(0, COLS - 1);
    std::uniform_int_distribution<int> row(0, ROWS - 1);
    do {
        game.food = Cell{col(game.rng), row(game.rng)};
    } while (occupies(game, game.food));
}

void reset(Game& game) {
    game.body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};
    game.pending.clear();
    game.heading = Right;
    game.score = 0;
    game.phase = Phase::Playing;
    spawn_food(game);
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

void save_best(int best) {
    // SaveFileText 要非 const 的 char*，TextFormat 给的是 const——写进自己的缓冲再交。
    char text[16];
    snprintf(text, sizeof text, "%d", best);
    SaveFileText(HIGHSCORE_FILE, text);
}

void press(Game& game, Direction dir) {
    Direction last = game.pending.empty() ? game.heading : game.pending.back();
    if (dir == last || dir == OPPOSITE[last]) return;
    if (game.pending.size() >= 3) return;
    game.pending.push_back(dir);
}

void step(Game& game) {
    if (!game.pending.empty()) {
        game.heading = game.pending.front();
        game.pending.pop_front();
    }
    Cell head{game.body.front().x + DELTA[game.heading].x,
              game.body.front().y + DELTA[game.heading].y};
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS || occupies(game, head)) {
        game.phase = Phase::Over;
        if (game.score > game.best) {
            game.best = game.score;
            save_best(game.best);
        }
        return;
    }
    game.body.push_front(head);
    if (head == game.food) {
        game.score += 10;
        spawn_food(game);
    } else {
        game.body.pop_back();
    }
}

int main() {
    const int width = COLS * CELL;
    const int height = ROWS * CELL;
    InitWindow(width, height, "snake 07 - score");
    SetTargetFPS(60);

    Game game;
    game.best = load_best();
    const float stepTime = 0.18f;
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        if (game.phase == Phase::Ready || game.phase == Phase::Over) {
            if (IsKeyPressed(KEY_ENTER) || IsKeyPressed(KEY_SPACE)) reset(game);
        } else if (game.phase == Phase::Playing) {
            if (IsKeyPressed(KEY_P)) {
                game.phase = Phase::Paused;
            } else {
                if (IsKeyPressed(KEY_RIGHT) || IsKeyPressed(KEY_D)) press(game, Right);
                if (IsKeyPressed(KEY_LEFT) || IsKeyPressed(KEY_A)) press(game, Left);
                if (IsKeyPressed(KEY_UP) || IsKeyPressed(KEY_W)) press(game, Up);
                if (IsKeyPressed(KEY_DOWN) || IsKeyPressed(KEY_S)) press(game, Down);
            }
        } else if (game.phase == Phase::Paused) {
            if (IsKeyPressed(KEY_P)) game.phase = Phase::Playing;
        }

        float dt = GetFrameTime();
        if (game.phase == Phase::Playing) {
            acc += dt;
            while (acc >= stepTime) {
                step(game);
                acc -= stepTime;
            }
        } else {
            acc = 0.0f;
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
        DrawCircle(game.food.x * CELL + CELL / 2, game.food.y * CELL + CELL / 2, CELL * 0.38f, APPLE);
        DrawText(TextFormat("score %d    best %d", game.score, game.best), 24, 24, 18, INK);

        const char* hint = nullptr;
        if (game.phase == Phase::Ready) hint = "snake 07 - press ENTER to start";
        if (game.phase == Phase::Paused) hint = "PAUSED - press P to resume";
        if (game.phase == Phase::Over) hint = "GAME OVER - press ENTER to restart";
        if (hint) {
            DrawRectangle(0, height / 2 - 44, width, 88, Fade(NIGHT, 0.8f));
            DrawText(hint, 24, height / 2 - 12, 24, INK);
        }
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
