#include "render/cairo_text.h"

#include <pangomm/layout.h>

void draw_cairo_text(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const string& text,
    double x,
    double y,
    double size,
    const ChartColor& color,
    bool bold,
    double align) {
    auto layout = Pango::Layout::create(cr);
    Pango::FontDescription font;
    font.set_family("sans-serif");
    font.set_absolute_size(size * Pango::SCALE);
    font.set_weight(bold ? Pango::Weight::BOLD : Pango::Weight::NORMAL);
    layout->set_font_description(font);
    layout->set_text(text);
    int text_width = 0;
    int text_height = 0;
    layout->get_pixel_size(text_width, text_height);
    cr->set_source_rgb(color.r, color.g, color.b);
    cr->move_to(x - text_width * align, y - text_height / 2.0);
    layout->show_in_cairo_context(cr);
}
