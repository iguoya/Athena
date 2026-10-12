#include "board_view.hh"

#include "../../assets/xiangqi_art.hh"

// 只登记绘制。点击从第 5 章才接。
BoardView::BoardView() {
    set_overflow(Gtk::Overflow::HIDDEN);
    set_draw_func(sigc::mem_fun(*this, &BoardView::draw));
    set_size_request(520, 580);
}

// GTK 要重画时调用。先裁到自己的区域，再按当前像素算交叉点。这一章不画子。
void BoardView::draw(const Cairo::RefPtr<Cairo::Context>& context, int width, int height) {
    context->rectangle(0, 0, width, height);
    context->clip();
    const xiangqi_art::Layout layout = xiangqi_art::layout_for(width, height);
    xiangqi_art::paint_board(*this, context, layout);
}
