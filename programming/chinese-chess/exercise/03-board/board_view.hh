#pragma once

#include <gtkmm.h>

// 这一章只放矢量棋盘，不放棋子，也不接收点击。
class BoardView : public Gtk::DrawingArea {
public:
    BoardView();

private:
    void draw(const Cairo::RefPtr<Cairo::Context>& context, int width, int height);
};
