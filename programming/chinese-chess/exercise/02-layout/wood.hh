#pragma once

#include <gtkmm.h>

// 这一章的棋盘还只是一块木色。两个窗口都用这一份，颜色和线从下一章才开始。
class Wood : public Gtk::DrawingArea {
public:
    Wood() {
        set_overflow(Gtk::Overflow::HIDDEN);
        set_draw_func([this](const Cairo::RefPtr<Cairo::Context>& context, int, int) {
            // 只涂自己的分配区域。不限制的话，底色会画到侧栏上面。
            context->rectangle(0, 0, get_width(), get_height());
            context->clip();
            context->set_source_rgb(0.93, 0.78, 0.55);
            context->rectangle(0, 0, get_width(), get_height());
            context->fill();
        });
        set_hexpand(true);
        set_vexpand(true);
        set_size_request(520, 580);
    }
};
