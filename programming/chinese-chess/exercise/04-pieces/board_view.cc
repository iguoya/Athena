#include "board_view.hh"

#include "../../assets/xiangqi_art.hh"

BoardView::BoardView() {
    set_overflow(Gtk::Overflow::HIDDEN);
    set_draw_func(sigc::mem_fun(*this, &BoardView::draw));
    set_size_request(520, 580);
}

// 先画棋盘，再按开局坐标摆子。坐标写在这里，还没有 Position，点了也不会走。
void BoardView::draw(const Cairo::RefPtr<Cairo::Context>& context, int width, int height) {
    context->rectangle(0, 0, width, height);
    context->clip();
    const xiangqi_art::Layout layout = xiangqi_art::layout_for(width, height);
    xiangqi_art::paint_board(*this, context, layout);

    using xiangqi_art::Kind;
    using xiangqi_art::Side;
    const Kind black_back[] = {Kind::Rook, Kind::Horse,     Kind::Elephant, Kind::Advisor, Kind::General,
                               Kind::Advisor, Kind::Elephant, Kind::Horse,  Kind::Rook};
    const Kind red_back[] = {Kind::Rook, Kind::Horse,     Kind::Elephant, Kind::Advisor, Kind::General,
                             Kind::Advisor, Kind::Elephant, Kind::Horse,  Kind::Rook};
    auto paint = [&](int file, int rank, Side side, Kind kind) {
        xiangqi_art::paint_piece(context, layout, side, kind, layout.origin_x + file * layout.cell,
                                 layout.origin_y + rank * layout.cell);
    };
    for (int file = 0; file < 9; ++file) {
        paint(file, 0, Side::Black, black_back[file]);
        paint(file, 9, Side::Red, red_back[file]);
        if (file % 2 == 0) {
            paint(file, 3, Side::Black, Kind::Pawn);
            paint(file, 6, Side::Red, Kind::Pawn);
        }
    }
    paint(1, 2, Side::Black, Kind::Cannon);
    paint(7, 2, Side::Black, Kind::Cannon);
    paint(1, 7, Side::Red, Kind::Cannon);
    paint(7, 7, Side::Red, Kind::Cannon);
}
