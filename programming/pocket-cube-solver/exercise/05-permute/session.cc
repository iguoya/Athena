#include "session.hh"

#include <algorithm>

namespace {

const char* kStageMarks[3] = {"①", "②", "③"};

}  // namespace

void Session::bind(const Widgets& widgets) {
    w_ = widgets;
    w_.scramble->signal_clicked().connect(sigc::mem_fun(*this, &Session::scramble));
    w_.reset->signal_clicked().connect(sigc::mem_fun(*this, &Session::reset));
    w_.solve->signal_clicked().connect(sigc::mem_fun(*this, &Session::solve));
    w_.prev->signal_clicked().connect(sigc::mem_fun(*this, &Session::step_back));
    w_.next->signal_clicked().connect(sigc::mem_fun(*this, &Session::step_forward));
    w_.play->signal_clicked().connect(sigc::mem_fun(*this, &Session::toggle_play));
    scramble();
}

// ---- 动作 ----

void Session::scramble() {
    forget_plan();
    state_ = cube::perform(cube::solved(), cube::random_alg(rng_, 25));
    say("已随机打乱。点「求解」，看它怎样一步步来。");
    refresh();
}

void Session::reset() {
    forget_plan();
    state_ = cube::solved();
    say("已复原。");
    refresh();
}

// 求解之前的共同准备。这一章的魔方永远是摆正的（打乱只用 U、R、F，DBL 不会动），
// 不需要检查输入、也不需要摆正；下一章才会有任意输入。
bool Session::prepare() {
    if (animation_) {
        return false;
    }
    forget_plan();
    return true;
}

// 把一份计划摊成一步一步的列表，回放时按它走。
void Session::adopt(cube::Plan plan, const std::string& headline) {
    plan_ = std::move(plan);
    int index = 0;
    const int stage_count = static_cast<int>(plan_->stages.size());
    stage_begin_.assign(stage_count, 0);
    stage_end_.assign(stage_count, 0);
    for (int s = 0; s < stage_count; ++s) {
        stage_begin_[s] = index;
        const auto& segments = plan_->stages[s].segments;
        for (int g = 0; g < static_cast<int>(segments.size()); ++g) {
            for (const cube::Move& m : segments[g].moves) {
                steps_.push_back({m, s, g});
                ++index;
            }
        }
        stage_end_[s] = index;
    }
    say(headline);
    refresh();
}

void Session::solve() {
    if (!prepare()) {
        return;
    }
    cube::Plan plan = cube::solve(state_);
    const int steps = plan.length();
    adopt(std::move(plan), "共 " + std::to_string(steps) + " 步，分三个阶段。");
}

void Session::step_forward() {
    if (animation_ || done_ >= static_cast<int>(steps_.size())) {
        return;
    }
    start(steps_[done_].move, true);
}

void Session::step_back() {
    if (animation_ || done_ == 0) {
        return;
    }
    start(cube::inverse(steps_[done_ - 1].move), false);
}

void Session::toggle_play() {
    if (playing_) {
        playing_ = false;  // 当前这一步放完再停
        refresh();
        return;
    }
    if (steps_.empty()) {
        return;
    }
    if (done_ >= static_cast<int>(steps_.size())) {
        // 放完之后再点播放：回到起点重放。
        for (int i = done_ - 1; i >= 0; --i) {
            state_ = cube::perform(state_, cube::inverse(steps_[i].move));
        }
        done_ = 0;
    }
    playing_ = true;
    if (!animation_) {
        start(steps_[done_].move, true);
    }
    refresh();
}

// ---- 动画 ----

double Session::seconds_for(cube::Move move) const {
    const double speed = w_.speed ? w_.speed->get_value() : 1.0;
    return (move.turns == 2 ? 0.8 : 0.55) / std::max(0.2, speed);
}

void Session::start(cube::Move move, bool forward) {
    animation_ = Animation{move, forward, 0.0};
    if (!timer_.connected()) {
        last_tick_ = std::chrono::steady_clock::now();
        timer_ = Glib::signal_timeout().connect(sigc::mem_fun(*this, &Session::tick), 16);
    }
    cube_view_.show_turning(state_, move, 0.0);
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
        finish_animation();
        return animation_.has_value();
    }
    // 先慢后快再慢，比匀速看着自然。
    const double t = animation_->t;
    cube_view_.show_turning(state_, animation_->move, t * t * (3 - 2 * t));
    return true;
}

void Session::finish_animation() {
    const Animation done = *animation_;
    animation_.reset();
    state_ = cube::perform(state_, done.move);
    done_ += done.forward ? 1 : -1;
    if (playing_ && done_ < static_cast<int>(steps_.size()) && done.forward) {
        refresh();
        start(steps_[done_].move, true);
        return;
    }
    playing_ = false;
    refresh();
}

void Session::forget_plan() {
    plan_.reset();
    steps_.clear();
    done_ = 0;
    animation_.reset();
    playing_ = false;
    timer_.disconnect();
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

view::Marks Session::current_marks() const {
    view::Marks marks{};
    if (!plan_ || steps_.empty()) {
        return marks;
    }
    const Step& step = steps_[std::min<int>(done_, steps_.size() - 1)];
    for (int pos : plan_->stages[step.stage].segments[step.segment].focus) {
        for (int slot : cube::corner_slots(pos)) {
            marks[slot] = true;
        }
    }
    return marks;
}

std::string Session::moves_markup() const {
    std::string out;
    int g = 0;
    for (std::size_t s = 0; s < plan_->stages.size(); ++s) {
        const cube::Stage& stage = plan_->stages[s];
        out += std::string("<b>") + kStageMarks[s] + " " + Glib::Markup::escape_text(stage.title) + "</b>\n";
        if (stage.segments.empty()) {
            out += "<span foreground=\"#8a8f98\">这一步不用做</span>\n";
            continue;
        }
        for (std::size_t i = 0; i < stage.segments.size(); ++i) {
            if (i > 0) {
                out += "  ·  ";
            }
            for (const cube::Move& m : stage.segments[i].moves) {
                const std::string text = Glib::Markup::escape_text(cube::to_string(m));
                if (g == done_) {
                    out += "<span background=\"#f6d365\" foreground=\"#222222\"><b> " + text + " </b></span> ";
                } else if (g < done_) {
                    out += "<span foreground=\"#8a8f98\">" + text + "</span> ";
                } else {
                    out += text + " ";
                }
                ++g;
            }
        }
        out += "\n";
    }
    return out;
}

void Session::refresh() {
    const view::Marks marks = current_marks();
    if (!animation_) {
        cube_view_.show(state_, marks);
    }
    net_view_.show(state_, marks);

    const bool have_plan = plan_.has_value();
    const int total = static_cast<int>(steps_.size());
    w_.prev->set_sensitive(have_plan && !animation_ && done_ > 0);
    w_.next->set_sensitive(have_plan && !animation_ && done_ < total);
    w_.play->set_sensitive(have_plan && (playing_ || total > 0));
    w_.play->set_label(playing_ ? "暂停" : "播放");
    w_.solve->set_sensitive(!animation_);

    for (std::size_t s = 0; s < w_.stage.size(); ++s) {
        Gtk::Label* label = w_.stage[s];
        label->remove_css_class("done");
        label->remove_css_class("current");
        std::string text = std::string(kStageMarks[s]) + " ";
        if (have_plan && s >= plan_->stages.size()) {
            label->set_visible(false);  // 这个计划没有这么多阶段
            continue;
        }
        label->set_visible(true);
        if (!have_plan) {
            text += s == 0 ? "做第一层" : (s == 1 ? "翻顶面" : "摆顶层");
        } else {
            const cube::Stage& stage = plan_->stages[s];
            const int steps = stage_end_[s] - stage_begin_[s];
            text += stage.title + " · " + std::to_string(steps) + " 步";
            if (done_ >= stage_end_[s] && (steps > 0 || done_ >= stage_begin_[s])) {
                label->add_css_class("done");
            } else if (done_ >= stage_begin_[s] && done_ < stage_end_[s]) {
                label->add_css_class("current");
            }
        }
        label->set_text(text);
    }

    if (!have_plan) {
        w_.moves->set_text("");
        w_.note->set_text("");
        return;
    }
    w_.moves->set_markup(moves_markup());
    if (total == 0) {
        w_.note->set_text("已经是复原状态，不需要任何转动。");
    } else if (done_ >= total) {
        w_.note->set_text("完成：魔方已经复原。");
    } else {
        const Step& step = steps_[done_];
        const cube::Segment& seg = plan_->stages[step.stage].segments[step.segment];
        w_.note->set_text(std::string(kStageMarks[step.stage]) + " " + seg.title + " —— " + seg.note +
                          "（第 " + std::to_string(done_ + 1) + "/" + std::to_string(total) + " 步）");
    }
}
