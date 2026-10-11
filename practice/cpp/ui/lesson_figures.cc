#include "ui/lesson_figures.h"

#include "render/lesson_figure.h"

#include <functional>
#include <map>

using namespace std;

namespace {

using Painter = function<void(const Cairo::RefPtr<Cairo::Context>&, int, int)>;

// id → 绘制函数与设计高度。高度按各自图的设计稿给，纯静态图用
// DrawingArea + set_draw_func 即可（ADR 0035：需要对照切换或逐步推进时
// 才写 snapshot_vfunc）。
struct FigureSpec {
    Painter paint;
    int height;
};

const map<string, FigureSpec>& registry() {
    static const map<string, FigureSpec> table{
        {"shallow_copy_aliasing",
         {lesson_figure::shallow_copy_aliasing, 300}},
    };
    return table;
}

}  // namespace

Gtk::Widget* make_lesson_figure(const string& id) {
    const auto found = registry().find(id);
    if (found == registry().end()) {
        return nullptr;
    }
    auto* area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_height(found->second.height);
    area->set_hexpand(true);
    area->set_draw_func(
        [paint = found->second.paint](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            paint(cr, width, height);
        });
    return area;
}
