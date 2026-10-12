// 第五章：把散落的 if 收进一台状态机。
// 前两章的「死了按 R 整只换新」是一行凑合；开始画面一来、暂停一来，
// 散装判断就开始互相纠缠——凑合不动了，才是收编的时机。
// 四相：Ready / Playing / Paused / Over。输入按相分发，逻辑只在 Playing 里走。
// 这一章没有分数：分数是第六章的事。

#include "raylib.h"

#include <deque>
#include <random>

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

enum class Phase { Ready, Playing, Paused, Over };

struct Game {
    std::deque<Cell> body = {Cell{5, 12}, Cell{4, 12}, Cell{3, 12}};
    std::deque<Direction> pending;
    Direction heading = Right;
    Cell food{20, 12};
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
    game.phase = Phase::Playing;
    spawn_food(game);
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
        game.phase = Phase::Over;  // 上一章的 dead 布尔，升格成了状态机的一个相
        return;
    }
    game.body.push_front(head);
    if (head == game.food) {
        spawn_food(game);
    } else {
        game.body.pop_back();
    }
}

int main() {
    InitWindow(COLS * CELL, ROWS * CELL, "snake 05 - state machine");
    SetTargetFPS(60);

    Game game;
    const float stepTime = 0.12f;
    float acc = 0.0f;

    while (!WindowShouldClose()) {
        // 输入按相分发：同一颗键在不同相里含义不同，这正是状态机的价值。
        if (game.phase == Phase::Ready || game.phase == Phase::Over) {
            if (IsKeyPressed(KEY_ENTER) || IsKeyPressed(KEY_SPACE)) reset(game);
        } else if (game.phase == Phase::Playing) {
            if (IsKeyPressed(KEY_P)) {
                game.phase = Phase::Paused;
            } else {
                if (IsKeyPressed(KEY_RIGHT)) press(game, Right);
                if (IsKeyPressed(KEY_LEFT)) press(game, Left);
                if (IsKeyPressed(KEY_UP)) press(game, Up);
                if (IsKeyPressed(KEY_DOWN)) press(game, Down);
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
            acc = 0.0f;  // 暂停期间流逝的不是游戏时间，回来不补
        }

        BeginDrawing();
        ClearBackground(RAYWHITE);
        for (const Cell& part : game.body) {
            DrawRectangle(part.x * CELL, part.y * CELL, CELL, CELL, GREEN);
        }
        DrawCircle(game.body.front().x * CELL + CELL / 2 + DELTA[game.heading].x * 5,
                   game.body.front().y * CELL + CELL / 2 + DELTA[game.heading].y * 5, 3.0f, DARKGREEN);
        DrawRectangle(game.food.x * CELL, game.food.y * CELL, CELL, CELL, MAROON);

        const char* hint = nullptr;
        if (game.phase == Phase::Ready) hint = "snake 05 - press ENTER to start";
        if (game.phase == Phase::Paused) hint = "PAUSED - press P to resume";
        if (game.phase == Phase::Over) hint = "GAME OVER - press ENTER to restart";
        if (hint) {
            DrawRectangle(0, 200, COLS * CELL, 80, Fade(RAYWHITE, 0.85f));
            DrawText(hint, 24, 232, 24, MAROON);
        }
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
