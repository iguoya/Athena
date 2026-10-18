#include "session.hh"

#include <algorithm>
#include <stdexcept>

void Session::bind(const Widgets& widgets) {
    w_ = widgets;
    for (int i = 0; i < 9; ++i) {
        const cube::Move move = cube::basic_moves()[i];
        w_.turn[i]->signal_clicked().connect([this, move] { enqueue({move}); });
    }
    w_.run->signal_clicked().connect(sigc::mem_fun(*this, &Session::run_entry));
    w_.entry->signal_activate().connect(sigc::mem_fun(*this, &Session::run_entry));
    w_.undo->signal_clicked().connect(sigc::mem_fun(*this, &Session::undo));
    w_.reset->signal_clicked().connect(sigc::mem_fun(*this, &Session::reset));
    w_.scramble->signal_clicked().connect(sigc::mem_fun(*this, &Session::scramble));
    say("点一个转法，或者在输入框里写一串记号，比如 R U R' U'。");
    refresh();
}

// ---- 动作：都只是往队列里放转法 ----

void Session::enqueue(const cube::Alg& alg) {
    for (const cube::Move& move : alg) {
        queue_.push_back(move);
    }
    if (!animation_) {
        start_next();
    }
}

void Session::run_entry() {
    try {
        const cube::Alg alg = cube::parse(w_.entry->get_text().raw());
        w_.entry->set_text("");
        enqueue(alg);
    } catch (const std::invalid_argument& error) {
        say(error.what(), true);
    }
}

void Session::undo() {
    if (animation_ || history_.empty()) {
        return;
    }
    // 撤销就是把最后一步反着转一次，并且把它从历史里拿掉。
    const cube::Move last = history_.back();
    history_.pop_back();
    animation_ = Animation{cube::inverse(last), false, 0.0};
    if (!timer_.connected()) {
        last_tick_ = std::chrono::steady_clock::now();
        timer_ = Glib::signal_timeout().connect(sigc::mem_fun(*this, &Session::tick), 16);
    }
    refresh();
}

void Session::reset() {
    queue_.clear();
    animation_.reset();
    timer_.disconnect();
    history_.clear();
    state_ = cube::solved();
    say("已复原。");
    refresh();
}

void Session::scramble() {
    enqueue(cube::random_alg(rng_, 20));
    say("正在打乱：随机转 20 步。");
}

// ---- 动画 ----

double Session::seconds_for(cube::Move move) const {
    const double speed = w_.speed->get_value();
    return (move.turns == 2 ? 0.8 : 0.55) / std::max(0.2, speed);
}

void Session::start_next() {
    if (queue_.empty()) {
        return;
    }
    animation_ = Animation{queue_.front(), true, 0.0};
    queue_.pop_front();
    if (!timer_.connected()) {
        last_tick_ = std::chrono::steady_clock::now();
        timer_ = Glib::signal_timeout().connect(sigc::mem_fun(*this, &Session::tick), 16);
    }
    refresh();
}

bool Session::tick() {
    if (!animation_) {
        return false;
    }
    const auto now = std::chrono::steady_clock::now();
    const double dt = std::chrono::duration<double>(now - last_tick_).count();
    last_tick_ = now;
    animation_->t += dt / seconds_for(animation_->move);
    if (animation_->t >= 1.0) {
        finish();
        return animation_.has_value();
    }
    // 先慢后快再慢，比匀速看着自然。动画只是画面上的过渡，状态要等转完才换。
    const double t = animation_->t;
    cube_view_.show_turning(state_, animation_->move, t * t * (3 - 2 * t));
    return true;
}

void Session::finish() {
    const Animation done = *animation_;
    animation_.reset();
    state_ = cube::perform(state_, done.move);
    if (done.record) {
        history_.push_back(done.move);
    }
    if (!queue_.empty()) {
        start_next();
        return;
    }
    refresh();
}

// ---- 刷新界面 ----

void Session::say(const std::string& text, bool error) {
    w_.status->set_text(text);
    if (error) {
        w_.status->add_css_class("error");
    } else {
        w_.status->remove_css_class("error");
    }
}

// 圈出这一步转的那一层：8 张贴纸，面上的 4 张加四周侧面的 4 张。
view::Marks Session::layer_marks(cube::Move move) const {
    view::Marks marks{};
    const cube::Vec axis = cube::face_normal(move.face);
    for (int i = 0; i < cube::kStickers; ++i) {
        const cube::Vec p = cube::slot(i).pos;
        marks[i] = p.x * axis.x + p.y * axis.y + p.z * axis.z == 1;
    }
    return marks;
}

void Session::refresh() {
    view::Marks marks{};
    if (animation_) {
        marks = layer_marks(animation_->move);
    } else {
        cube_view_.show(state_, marks);
    }
    net_view_.show(state_, marks);
    w_.undo->set_sensitive(!animation_ && !history_.empty());
    w_.history->set_text(history_.empty() ? "还没有转过。" : "已转：" + cube::to_string(history_));
    if (!animation_ && !queue_.empty()) {
        return;
    }
    if (!animation_ && cube::is_solved(state_) && !history_.empty()) {
        say("回到了复原状态。");
    }
}
