#pragma once

#include <gtkmm.h>

// 矢量棋子画在交叉点上，这一章还不能走。
class BoardView : public Gtk::DrawingArea {
public:
    BoardView();

private:
    void draw(const Cairo::RefPtr<Cairo::Context>& context, int width, int height);
};
