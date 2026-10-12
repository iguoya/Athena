#pragma once

// 棋盘和棋子是矢量图，按窗口当前的像素尺寸栅格化，拉大时重画，不把小图放大。
// 图的许可与出处见同目录 ATTRIBUTION.txt。
// 棋盘图的格子是 100 用户单位，左上第一个交叉点在 (51.383, 51)。
// 点击和坐标都用换算后的这个格子，才能和画面上的交叉点重合。
// 图里没有楚河汉界、外侧坐标和炮兵位的折角，这三样仍由这里补上。

#include <gtkmm.h>

#include <librsvg/rsvg.h>

#include <algorithm>
#include <cmath>
#include <string>

namespace xiangqi_art {

enum class Side { Red, Black };

enum class Kind { General, Advisor, Elephant, Horse, Rook, Cannon, Pawn };

struct Layout {
    double board_x = 0;
    double board_y = 0;
    double board_w = 0;
    double board_h = 0;
    double cell = 0;
    double origin_x = 0;
    double origin_y = 0;
};

inline constexpr double k_board_w = 902.383;
inline constexpr double k_board_h = 1002.0;
inline constexpr double k_grid_x = 51.383;
inline constexpr double k_grid_y = 51.0;
inline constexpr double k_svg_cell = 100.0;

// 把棋盘图放进控件的像素：格子多大、左上角交叉点在哪。绘制和以后的点击都用这一份。
inline Layout layout_for(int width, int height) {
    const double label = 26;
    const double pad = 8;
    const double avail_w = std::max(1.0, width - 2 * pad);
    const double avail_h = std::max(1.0, height - 2 * (pad + label));
    const double aspect = k_board_w / k_board_h;
    double board_w = avail_w;
    double board_h = board_w / aspect;
    if (board_h > avail_h) {
        board_h = avail_h;
        board_w = board_h * aspect;
    }
    const double board_x = (width - board_w) / 2.0;
    const double board_y = label + (height - 2 * label - board_h) / 2.0;
    const double scale = board_w / k_board_w;
    return {board_x, board_y, board_w, board_h, k_svg_cell * scale,
            board_x + k_grid_x * scale, board_y + k_grid_y * scale};
}

namespace {

struct Library {
    bool ready = false;
    RsvgHandle* board = nullptr;
    RsvgHandle* pieces[2][7] = {};
    cairo_surface_t* board_image = nullptr;
    int board_w = 0;
    int board_h = 0;
    cairo_surface_t* piece_image[2][7] = {};
    int piece_px = 0;
};

inline const char* piece_file(Side side, Kind kind) {
    static const char* names[2][7] = {
        {"red_king.svg", "red_advisor.svg", "red_bishop.svg", "red_knight.svg", "red_rook.svg",
         "red_cannon.svg", "red_pawn.svg"},
        {"black_king.svg", "black_advisor.svg", "black_bishop.svg", "black_knight.svg", "black_rook.svg",
         "black_cannon.svg", "black_pawn.svg"},
    };
    const int si = side == Side::Red ? 0 : 1;
    const int ki = static_cast<int>(kind);
    return names[si][ki];
}

inline RsvgHandle* load_svg(const std::string& path) {
    GError* error = nullptr;
    RsvgHandle* handle = rsvg_handle_new_from_file(path.c_str(), &error);
    if (handle == nullptr) {
        g_printerr("棋子图打不开 %s：%s\n", path.c_str(), error != nullptr ? error->message : "未知原因");
        g_clear_error(&error);
    }
    return handle;
}

inline Library& library() {
    static Library lib;
    if (lib.ready) {
        return lib;
    }
    lib.board = load_svg(std::string(XQ_ASSETS) + "/board.svg");
    for (const Side side : {Side::Red, Side::Black}) {
        for (int kind = 0; kind < 7; ++kind) {
            const auto piece_kind = static_cast<Kind>(kind);
            const int si = side == Side::Red ? 0 : 1;
            const std::string path =
                std::string(XQ_ASSETS) + "/pieces/" + piece_file(side, piece_kind);
            lib.pieces[si][kind] = load_svg(path);
        }
    }
    lib.ready = true;
    return lib;
}

inline void paint_surface(cairo_t* cr, cairo_surface_t* image, double x, double y, double w, double h) {
    cairo_save(cr);
    cairo_translate(cr, x, y);
    cairo_scale(cr, w / cairo_image_surface_get_width(image), h / cairo_image_surface_get_height(image));
    cairo_set_source_surface(cr, image, 0, 0);
    if (cairo_pattern_t* pattern = cairo_get_source(cr)) {
        cairo_pattern_set_filter(pattern, CAIRO_FILTER_BEST);
    }
    cairo_paint(cr);
    cairo_restore(cr);
}

inline cairo_surface_t* render_document(RsvgHandle* handle, int px, int py) {
    cairo_surface_t* image = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, px, py);
    cairo_t* tmp = cairo_create(image);
    const RsvgRectangle viewport{0, 0, static_cast<double>(px), static_cast<double>(py)};
    GError* error = nullptr;
    if (!rsvg_handle_render_document(handle, tmp, &viewport, &error)) {
        g_printerr("棋子图渲染失败：%s\n", error != nullptr ? error->message : "未知原因");
        g_clear_error(&error);
    }
    cairo_destroy(tmp);
    return image;
}

inline void paint_handle(cairo_t* cr, RsvgHandle* handle, cairo_surface_t*& cache, int& cache_w, int& cache_h,
                         double x, double y, double w, double h) {
    if (handle == nullptr || w < 1 || h < 1) {
        return;
    }
    double device_w = w;
    double device_h = h;
    cairo_user_to_device_distance(cr, &device_w, &device_h);
    const int px = std::max(1, static_cast<int>(std::lround(std::abs(device_w))));
    const int py = std::max(1, static_cast<int>(std::lround(std::abs(device_h))));
    if (cache == nullptr || cache_w != px || cache_h != py) {
        if (cache != nullptr) {
            cairo_surface_destroy(cache);
        }
        cache = render_document(handle, px, py);
        cache_w = px;
        cache_h = py;
    }
    paint_surface(cr, cache, x, y, w, h);
}

inline void draw_centered(Gtk::Widget& widget, const Cairo::RefPtr<Cairo::Context>& context, double cx,
                          double cy, const std::string& text, int size_px) {
    auto layout = widget.create_pango_layout(text);
    Pango::FontDescription font;
    font.set_family("Microsoft YaHei");
    font.set_size(std::max(10, size_px) * PANGO_SCALE);
    layout->set_font_description(font);
    int text_w = 0;
    int text_h = 0;
    layout->get_pixel_size(text_w, text_h);
    context->move_to(cx - text_w / 2.0, cy - text_h / 2.0);
    layout->show_in_cairo_context(context);
}

inline void stroke_corner(const Cairo::RefPtr<Cairo::Context>& context, double px, double py, int sx,
                          int sy, double cell) {
    const double gap = cell * 0.08;
    const double arm = cell * 0.16;
    context->move_to(px + sx * gap, py + sy * (gap + arm));
    context->line_to(px + sx * gap, py + sy * gap);
    context->line_to(px + sx * (gap + arm), py + sy * gap);
}

inline void paint_marks(const Cairo::RefPtr<Cairo::Context>& context, const Layout& layout) {
    const double cell = layout.cell;
    const double x0 = layout.origin_x;
    const double y0 = layout.origin_y;
    context->set_source_rgb(0.1, 0.08, 0.06);
    context->set_line_width(std::max(1.0, cell * 0.02));
    auto star = [&](int file, int rank) {
        const double px = x0 + file * cell;
        const double py = y0 + rank * cell;
        const int unique = (file == 0 || file == 8) ? 1 : 2;
        for (int i = 0; i < unique; ++i) {
            const int sx = (file == 0 || file == 8) ? (file == 0 ? 1 : -1) : (i == 0 ? -1 : 1);
            stroke_corner(context, px, py, sx, -1, cell);
            stroke_corner(context, px, py, sx, 1, cell);
        }
    };
    for (const int file : {1, 7}) {
        star(file, 2);
        star(file, 7);
    }
    for (const int file : {0, 2, 4, 6, 8}) {
        star(file, 3);
        star(file, 6);
    }
    context->stroke();
}

inline void paint_fallback_grid(const Cairo::RefPtr<Cairo::Context>& context, const Layout& layout) {
    const double cell = layout.cell;
    const double x0 = layout.origin_x;
    const double y0 = layout.origin_y;
    context->set_source_rgb(0.15, 0.1, 0.06);
    context->set_line_width(std::max(1.0, cell * 0.03));
    for (int rank = 0; rank < 10; ++rank) {
        context->move_to(x0, y0 + rank * cell);
        context->line_to(x0 + 8 * cell, y0 + rank * cell);
    }
    context->move_to(x0, y0);
    context->line_to(x0, y0 + 9 * cell);
    context->move_to(x0 + 8 * cell, y0);
    context->line_to(x0 + 8 * cell, y0 + 9 * cell);
    for (int file = 1; file <= 7; ++file) {
        context->move_to(x0 + file * cell, y0);
        context->line_to(x0 + file * cell, y0 + 4 * cell);
        context->move_to(x0 + file * cell, y0 + 5 * cell);
        context->line_to(x0 + file * cell, y0 + 9 * cell);
    }
    context->move_to(x0 + 3 * cell, y0);
    context->line_to(x0 + 5 * cell, y0 + 2 * cell);
    context->move_to(x0 + 5 * cell, y0);
    context->line_to(x0 + 3 * cell, y0 + 2 * cell);
    context->move_to(x0 + 3 * cell, y0 + 7 * cell);
    context->line_to(x0 + 5 * cell, y0 + 9 * cell);
    context->move_to(x0 + 5 * cell, y0 + 7 * cell);
    context->line_to(x0 + 3 * cell, y0 + 9 * cell);
    context->stroke();
}

}  // namespace

// 画线、九宫、河界和路名。棋子不在这里。
inline void paint_board(Gtk::Widget& widget, const Cairo::RefPtr<Cairo::Context>& context, const Layout& layout) {
    context->set_source_rgb(0.882, 0.745, 0.525);
    context->paint();

    Library& lib = library();
    if (lib.board != nullptr) {
        paint_handle(context->cobj(), lib.board, lib.board_image, lib.board_w, lib.board_h, layout.board_x,
                     layout.board_y, layout.board_w, layout.board_h);
    } else {
        paint_fallback_grid(context, layout);
    }
    paint_marks(context, layout);

    const double cell = layout.cell;
    context->set_source_rgb(0.28, 0.14, 0.08);
    draw_centered(widget, context, layout.origin_x + 2 * cell, layout.origin_y + 4.5 * cell, "楚 河",
                  static_cast<int>(cell * 0.38));
    draw_centered(widget, context, layout.origin_x + 6 * cell, layout.origin_y + 4.5 * cell, "汉 界",
                  static_cast<int>(cell * 0.38));

    context->set_source_rgb(0.2, 0.1, 0.05);
    static const char* red_files[] = {"九", "八", "七", "六", "五", "四", "三", "二", "一"};
    for (int file = 0; file < 9; ++file) {
        const double x = layout.origin_x + file * cell;
        draw_centered(widget, context, x, layout.board_y - 14, std::to_string(file + 1),
                      static_cast<int>(cell * 0.26));
        draw_centered(widget, context, x, layout.board_y + layout.board_h + 14, red_files[file],
                      static_cast<int>(cell * 0.26));
    }
}

// 把一颗矢量子画在交叉点中心。边长跟着格子走，窗口变大时重新栅格化。
inline void paint_piece(const Cairo::RefPtr<Cairo::Context>& context, const Layout& layout, Side side, Kind kind,
                        double cx, double cy) {
    const double size = layout.cell * 0.92;
    Library& lib = library();
    const int si = side == Side::Red ? 0 : 1;
    const int ki = static_cast<int>(kind);
    RsvgHandle* handle = lib.pieces[si][ki];
    if (handle == nullptr) {
        context->set_source_rgb(0.96, 0.93, 0.86);
        context->arc(cx, cy, size * 0.42, 0, 6.28318530718);
        context->fill();
        return;
    }
    double device = size;
    double unused = 0;
    cairo_user_to_device_distance(context->cobj(), &device, &unused);
    const int px = std::max(1, static_cast<int>(std::lround(std::abs(device))));
    if (lib.piece_px != px) {
        for (auto& row : lib.piece_image) {
            for (cairo_surface_t*& image : row) {
                if (image != nullptr) {
                    cairo_surface_destroy(image);
                    image = nullptr;
                }
            }
        }
        lib.piece_px = px;
    }
    if (lib.piece_image[si][ki] == nullptr) {
        lib.piece_image[si][ki] = render_document(handle, px, px);
    }
    paint_surface(context->cobj(), lib.piece_image[si][ki], cx - size / 2, cy - size / 2, size, size);
}

}  // namespace xiangqi_art
