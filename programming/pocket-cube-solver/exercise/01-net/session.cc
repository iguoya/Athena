#include "session.hh"

#include <string>

Session::Session() {
    net_view_.signal_picked().connect(sigc::mem_fun(*this, &Session::pick));
}

void Session::bind(Gtk::Label* info, Gtk::Button* show_sample, Gtk::Button* show_solved) {
    info_ = info;
    show_sample->signal_clicked().connect([this] { show(cube::sample()); });
    show_solved->signal_clicked().connect([this] { show(cube::solved()); });
    show(state_);
}

void Session::show(const cube::Stickers& state) {
    state_ = state;
    net_view_.show(state_, {});
    info_->set_text("点展开图上的任意一格，看它属于哪个角块。");
}

// 点中一格：找出它所在的角块，把这个角块的三张贴纸圈起来，并列出每张贴纸在哪个面、什么颜色。
void Session::pick(int slot) {
    const int corner = cube::corner_of(slot);
    view::Marks marks{};
    std::string text = std::string("角块 ") + cube::corner_name(corner) + "：";
    for (int s : cube::corner_slots()[corner]) {
        marks[s] = true;
        text += std::string("\n  ") + cube::face_name(s / 4) + "上的 " + cube::color_name(state_[s]) + "色";
    }
    net_view_.show(state_, marks);
    info_->set_text(text);
}
