#pragma once

// 把魔方状态、求解计划、回放和涂色输入接在一起。
// 规则在 cube.cc，求解在 solver.cc，画面在 view.cc；这里只决定"什么时候该做哪一件"。

#include "cube.hh"
#include "solver.hh"
#include "view.hh"

#include <gtkmm.h>

#include <array>
#include <chrono>
#include <optional>
#include <random>
#include <vector>

// 界面文件里的控件。Session 不创建控件，只按名字接上它们。
struct Widgets {
    Gtk::Label* status = nullptr;
    Gtk::Label* note = nullptr;
    Gtk::Label* moves = nullptr;
    std::vector<Gtk::Label*> stage;     // 每个阶段一个标签；计划有几个阶段就用前几个
    Gtk::Button* scramble = nullptr;
    Gtk::Button* reset = nullptr;
    Gtk::Button* solve = nullptr;
    Gtk::Button* prev = nullptr;
    Gtk::Button* play = nullptr;
    Gtk::Button* next = nullptr;
    Gtk::Button* check = nullptr;
    Gtk::Button* clear = nullptr;
    Gtk::Scale* speed = nullptr;
    Gtk::ToggleButton* edit = nullptr;
    Gtk::Revealer* palette = nullptr;
    std::array<Gtk::ToggleButton*, 6> paint{};
};

class Session {
public:
    Session();
    view::CubeView& cube_view() { return cube_view_; }
    view::NetView& net_view() { return net_view_; }
    void bind(const Widgets& widgets);

private:
    // 计划里的一步：转哪一下，属于第几阶段、第几段。
    struct Step {
        cube::Move move;
        int stage;
        int segment;
    };
    struct Animation {
        cube::Move move;
        bool forward;
        double t;
    };

    void scramble();
    void reset();
    void solve();
    bool prepare();
    void adopt(cube::Plan plan, const std::string& headline);
    void step_forward();
    void step_back();
    void toggle_play();
    void set_editing(bool on);
    void paint_slot(int slot);
    void check();

    void start(cube::Move move, bool forward);
    bool tick();
    void finish_animation();
    void forget_plan();
    void refresh();
    void say(const std::string& text, bool error = false);
    std::string moves_markup() const;
    view::Marks current_marks() const;
    double seconds_for(cube::Move move) const;

    view::CubeView cube_view_;
    view::NetView net_view_;
    Widgets w_;

    std::mt19937 rng_{std::random_device{}()};
    cube::Stickers state_ = cube::solved();
    std::optional<cube::Plan> plan_;
    std::vector<Step> steps_;
    std::vector<int> stage_begin_;       // 每个阶段的第一步在 steps_ 里的下标
    std::vector<int> stage_end_;
    int done_ = 0;                       // 已经做完的步数

    std::optional<Animation> animation_;
    bool playing_ = false;
    bool editing_ = false;
    int brush_ = -1;
    sigc::connection timer_;
    bool turned_ = false;
    std::chrono::steady_clock::time_point last_tick_;
};
