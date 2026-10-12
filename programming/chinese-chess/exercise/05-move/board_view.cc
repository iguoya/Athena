#include "board_view.hh"

#include "../../assets/xiangqi_art.hh"

#include <cmath>

namespace {

// 规则用的 Side、Kind 和矢量图用的不是同一个枚举。这里只做对照，避免 position.cc 包含绘图头。
xiangqi_art::Side art_side(Side side) {
    return side == Side::Red ? xiangqi_art::Side::Red : xiangqi_art::Side::Black;
}

xiangqi_art::Kind art_kind(Kind kind) {
    switch (kind) {
    case Kind::General:
        return xiangqi_art::Kind::General;
    case Kind::Advisor:
        return xiangqi_art::Kind::Advisor;
    case Kind::Elephant:
        return xiangqi_art::Kind::Elephant;
    case Kind::Horse:
        return xiangqi_art::Kind::Horse;
    case Kind::Rook:
        return xiangqi_art::Kind::Rook;
    case Kind::Cannon:
        return xiangqi_art::Kind::Cannon;
    case Kind::Pawn:
        return xiangqi_art::Kind::Pawn;
    }
    return xiangqi_art::Kind::Pawn;
}

}  // namespace

BoardView::BoardView() {
    set_overflow(Gtk::Overflow::HIDDEN);
    set_draw_func(sigc::mem_fun(*this, &BoardView::draw));
    set_size_request(520, 580);
    auto click = Gtk::GestureClick::create();
    click->signal_released().connect(sigc::mem_fun(*this, &BoardView::on_click));
    add_controller(click);
}

// Session 算完局面和提示后交给这里。本类不保存规则，只记住要画的东西并要求重画。
void BoardView::show_position(const Position& position, std::optional<Cell> selected,
                              const std::vector<Cell>& hints, std::optional<Cell> last_from,
                              std::optional<Cell> last_to) {
    position_ = &position;
    selected_ = selected;
    hints_ = hints;
    last_from_ = last_from;
    last_to_ = last_to;
    queue_draw();
}

// 只把像素收成交叉点。离交叉点太远当作没点到。能不能走由 Session 问 Position。
void BoardView::on_click(int, double x, double y) {
    const xiangqi_art::Layout layout = xiangqi_art::layout_for(get_width(), get_height());
    if (layout.cell <= 0) {
        return;
    }
    const int file = static_cast<int>(std::lround((x - layout.origin_x) / layout.cell));
    const int rank = static_cast<int>(std::lround((y - layout.origin_y) / layout.cell));
    if (file < 0 || file > 8 || rank < 0 || rank > 9) {
        return;
    }
    const double px = layout.origin_x + file * layout.cell;
    const double py = layout.origin_y + rank * layout.cell;
    if (std::hypot(x - px, y - py) > layout.cell * 0.45) {
        return;
    }
    picked_.emit(file, rank);
}

// 棋子来自 Position。圆点和圈是 Session 给的提示、上一步和选中，不是在这里现算的。
void BoardView::draw(const Cairo::RefPtr<Cairo::Context>& context, int width, int height) {
    context->rectangle(0, 0, width, height);
    context->clip();
    const xiangqi_art::Layout layout = xiangqi_art::layout_for(width, height);
    xiangqi_art::paint_board(*this, context, layout);
    if (position_ == nullptr) {
        return;
    }

    const double cell = layout.cell;
    auto spot = [&](Cell where) {
        return std::pair{layout.origin_x + where.x * cell, layout.origin_y + where.y * cell};
    };

    for (int rank = 0; rank < 10; ++rank) {
        for (int file = 0; file < 9; ++file) {
            const auto piece = position_->at(Cell{file, rank});
            if (!piece) {
                continue;
            }
            const auto [px, py] = spot(Cell{file, rank});
            xiangqi_art::paint_piece(context, layout, art_side(piece->side), art_kind(piece->kind), px, py);
        }
    }

    for (const Cell hint : hints_) {
        const auto [px, py] = spot(hint);
        const bool capture = position_->at(hint).has_value();
        context->set_source_rgba(0.72, 0.16, 0.1, capture ? 0.95 : 0.8);
        context->arc(px, py, capture ? cell * 0.48 : cell * 0.09, 0, 6.28318530718);
        if (capture) {
            context->set_line_width(std::max(1.5, cell * 0.045));
            context->stroke();
        } else {
            context->fill();
        }
    }

    auto ring = [&](Cell where, double red, double green, double blue) {
        const auto [px, py] = spot(where);
        context->set_source_rgb(red, green, blue);
        context->set_line_width(std::max(1.5, cell * 0.05));
        context->arc(px, py, cell * 0.5, 0, 6.28318530718);
        context->stroke();
    };
    if (last_from_) {
        ring(*last_from_, 0.72, 0.5, 0.12);
    }
    if (last_to_) {
        ring(*last_to_, 0.72, 0.5, 0.12);
    }
    if (selected_) {
        ring(*selected_, 0.93, 0.72, 0.12);
    }
}
