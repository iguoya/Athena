#pragma once

// 这一章的会话：一个转动队列。按钮、输入框、打乱都往队列里放转法，
// 队列里的转法一个一个放成动画，放完一个才把状态真正换掉。

#include "cube.hh"
#include "view.hh"

#include <gtkmm.h>

#include <array>
#include <chrono>
#include <deque>
#include <random>
#include <vector>

struct Widgets {
    Gtk::Label* status = nullptr;
    Gtk::Label* history = nullptr;
    Gtk::Entry* entry = nullptr;
    Gtk::Button* run = nullptr;
    Gtk::Button* undo = nullptr;
    Gtk::Button* reset = nullptr;
    Gtk::Button* scramble = nullptr;
    Gtk::Scale* speed = nullptr;
    std::array<Gtk::Button*, 9> turn{};  // 顺序同 cube::basic_moves()：U U2 U' R R2 R' F F2 F'
};

class Session {
public:
    view::CubeView& cube_view() { return cube_view_; }
    view::NetView& net_view() { return net_view_; }
    void bind(const Widgets& widgets);

private:
    struct Animation {
        cube::Move move;
        bool record;   // 撤销时的反向动画不记进历史
        double t;
    };

    void enqueue(const cube::Alg& alg);
    void run_entry();
    void undo();
    void reset();
    void scramble();
    void start_next();
    bool tick();
    void finish();
    void refresh();
    void say(const std::string& text, bool error = false);
    view::Marks layer_marks(cube::Move move) const;
    double seconds_for(cube::Move move) const;

    view::CubeView cube_view_;
    view::NetView net_view_;
    Widgets w_;

    std::mt19937 rng_{std::random_device{}()};
    cube::Stickers state_ = cube::solved();
    cube::Alg history_;                 // 已经转过的步
    std::deque<cube::Move> queue_;      // 等着转的步
    std::optional<Animation> animation_;
    sigc::connection timer_;
    std::chrono::steady_clock::time_point last_tick_;
};
