#include "ui/lesson_page.h"

#include "ui/lesson_blocks.h"

#include <stdexcept>
#include <utility>

using namespace std;

namespace {

template <typename T>
T& take(const Glib::RefPtr<Gtk::Builder>& builder, const char* id) {
    auto* widget = builder->get_widget<T>(id);
    if (!widget) {
        throw runtime_error(string("lesson page template is missing: ") + id);
    }
    return *widget;
}

}  // namespace

LessonPage::LessonPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    LessonRenderer::FigureFactory figures,
    ExperimentRequested on_experiment_requested)
    : m_chapter(chapter),
      m_renderer(std::move(figures)),
      m_on_experiment_requested(std::move(on_experiment_requested)) {
    m_root = &take<Gtk::Box>(builder, "lesson_page");
    m_notebook = &take<Gtk::Notebook>(builder, "lesson_page_notebook");
    take<Gtk::Label>(builder, "lesson_page_title").set_text(chapter.title);
    auto& subtitle = take<Gtk::Label>(builder, "lesson_page_subtitle");
    subtitle.set_text(chapter.description);
    subtitle.set_visible(!chapter.description.empty());

    LessonChapter content;
    try {
        content = load_lesson_chapter(chapter.category + "." + chapter.name);
    } catch (const exception& error) {
        // 课文读不出来时把原因摆在页面上。静默留一个空页面，作者会以为
        // 是自己内容写少了，而不是文件没打进 GResource。
        Gtk::Box& body = *Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 10);
        body.set_margin(20);
        lesson::prose(body, string("读不出这一章的课文：") + error.what());
        m_notebook->append_page(body, "内容缺失");
        return;
    }

    build_tab(content.outline, "教学大纲");
    for (const LessonDoc& doc : content.topics) {
        build_tab(doc, doc.title);
    }
}

void LessonPage::build_tab(const LessonDoc& doc, const string& tab_title) {
    const auto builder = Gtk::Builder::create_from_resource("/app/chapters/lesson.ui");
    auto& page = take<Gtk::ScrolledWindow>(builder, "lesson_topic_page");
    auto& body = take<Gtk::Box>(builder, "lesson_topic_body");

    if (!doc.subtitle.empty()) {
        auto& lead = lesson::prose(body, doc.subtitle);
        lead.add_css_class("native-lesson-lead");
    }
    m_renderer.render(body, doc);

    // 知识点页尾部挂一个进实验台的入口：讲解与实验是同一个知识点的两面
    // （ADR 0028），读完就该能直接动手。大纲页没有对应知识点，不挂。
    const SubChapter* topic = nullptr;
    for (const SubChapter& candidate : m_chapter.subchapters) {
        if (candidate.function_id == doc.topic) {
            topic = &candidate;
            break;
        }
    }
    if (topic != nullptr && m_on_experiment_requested) {
        auto& button = *Gtk::make_managed<Gtk::Button>("▶ 到实验台动手");
        button.set_halign(Gtk::Align::START);
        button.add_css_class("btn-sm");
        button.add_css_class("btn-primary");
        const ExperimentSelection selection{
            .function_id = topic->function_id,
            .title = topic->title,
            .description = topic->description,
            .source_path = topic->source,
            .member_name = topic->name,
            .labs = topic->labs,
        };
        button.signal_clicked().connect(
            [this, selection] { m_on_experiment_requested(selection, false); });
        body.append(button);
    }

    m_notebook->append_page(page, tab_title);
}
