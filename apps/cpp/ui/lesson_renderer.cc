#include "ui/lesson_renderer.h"

#include "ui/lesson_blocks.h"

#include <utility>

using namespace std;

namespace {

lesson::CalloutKind callout_kind(const string& name) {
    if (name == "why") {
        return lesson::CalloutKind::Why;
    }
    if (name == "key") {
        return lesson::CalloutKind::Key;
    }
    if (name == "trap") {
        return lesson::CalloutKind::Trap;
    }
    if (name == "use") {
        return lesson::CalloutKind::Use;
    }
    return lesson::CalloutKind::Note;
}

}  // namespace

LessonRenderer::LessonRenderer(FigureFactory figures)
    : m_figures(std::move(figures)) {}

void LessonRenderer::render(Gtk::Box& host, const LessonDoc& doc) const {
    render_blocks(host, doc.blocks);
}

void LessonRenderer::render_blocks(
    Gtk::Box& host, const vector<LessonBlock>& blocks) const {
    for (const LessonBlock& block : blocks) {
        render_block(host, block);
    }
}

void LessonRenderer::render_block(Gtk::Box& host, const LessonBlock& block) const {
    if (block.type == "lead") {
        auto& label = lesson::prose(host, block.text);
        label.add_css_class("native-lesson-lead");
        return;
    }
    if (block.type == "prose") {
        lesson::prose(host, block.text);
        return;
    }
    if (block.type == "bullets") {
        lesson::bullets(host, block.items);
        return;
    }
    if (block.type == "code") {
        lesson::code(host, block.text, block.caption);
        return;
    }
    if (block.type == "steps") {
        lesson::steps(host, block.items);
        return;
    }
    if (block.type == "table") {
        lesson::table(host, block.head, block.rows, block.note);
        return;
    }
    if (block.type == "section") {
        // 档位决定这一节是摊开还是收起：核心必须懂，进阶遇到坑再回来，
        // 选读用到再说。空 tier 等同核心。
        const char* badge = nullptr;
        if (block.tier == "deeper") {
            badge = "进阶";
        } else if (block.tier == "optional") {
            badge = "选读";
        }
        Gtk::Box& body = badge == nullptr
            ? lesson::section(host, block.title)
            : lesson::folded_section(host, badge, block.title);
        render_blocks(body, block.blocks);
        return;
    }
    if (block.type == "callout") {
        Gtk::Box& body = lesson::callout(host, callout_kind(block.kind), block.title);
        render_blocks(body, block.blocks);
        return;
    }
    if (block.type == "quiz" || block.type == "predict") {
        // predict 是「先猜再验」：不算检验，只为让预期显形，猜错无所谓。
        lesson::quiz(
            host, block.text, block.items, block.answer, block.note,
            block.type == "quiz");
        return;
    }
    if (block.type == "figure") {
        Gtk::Widget* widget = m_figures ? m_figures(block.id) : nullptr;
        if (widget != nullptr) {
            host.append(*widget);
        }
        if (!block.caption.empty()) {
            auto& caption = lesson::prose(host, block.caption);
            caption.add_css_class("lesson-figure-caption");
        }
        return;
    }
    // 走到这里说明生成器放过了一个渲染器不认识的块类型，两边不同步了。
    // 显式说出来，不要静默跳过——那会让一段内容凭空消失而没人发现。
    lesson::prose(host, "（未知内容块类型：" + block.type + "）");
}
