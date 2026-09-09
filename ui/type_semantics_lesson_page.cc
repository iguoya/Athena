#include "type_semantics_lesson_page.h"

#include "ui/learning_unit_view.h"

#include <stdexcept>
#include <utility>
#include <vector>

using namespace std;

namespace {

const SubChapter& topic_by_name(
    const ChapterMeta& chapter, const string& subchapter_name) {
    for (const auto& subchapter : chapter.subchapters) {
        if (subchapter.name == subchapter_name) {
            return subchapter;
        }
    }
    throw runtime_error(
        "TypeSemantics lesson requires topic " + subchapter_name);
}

} // namespace

TypeSemanticsLessonPage::TypeSemanticsLessonPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    function<void(const ExperimentSelection&, bool)> on_experiment_requested,
    function<void()> on_reference_requested)
    : m_chapter(chapter),
      m_on_experiment_requested(std::move(on_experiment_requested)) {
    auto* unit_host =
        builder->get_widget<Gtk::Box>("type_semantics_learning_unit_host");
    auto* run_button =
        builder->get_widget<Gtk::Button>("type_semantics_run_button");
    auto* reference_button = builder->get_widget<Gtk::Button>(
        "type_semantics_reference_button");
    if (!unit_host || !run_button || !reference_button) {
        throw runtime_error("Failed to load TypeSemantics lesson Blueprint");
    }

    const auto& topic = topic_by_name(m_chapter, "initialization");
    m_learning_unit_data = LearningUnit{
        .id = "narrowing_boundary",
        .heading = "",
        .claim = "花括号初始化会把可能丢失信息的窄化转换拦在编译期。",
        .question = "double source = 3.75; int value{source}; 这行代码会怎样？",
        .choices = {
            "通过编译，并把 3.75 截断为 3",
            "编译失败，因为列表初始化拒绝窄化",
        },
        .correct_choice = 1,
        .feedback = "小数部分可能丢失，因此列表初始化在编译期拒绝它。圆括号初始化才允许调用者明确接受截断。",
        .follow_up = "实验里再观察 int value(source) 为什么能运行，却需要由调用者承担截断。",
        .experiment_function_id = topic.function_id,
    };
    m_learning_unit = make_unique<LearningUnitView>(
        m_learning_unit_data,
        [this](const string&) { open_experiment("initialization"); });
    unit_host->append(m_learning_unit->widget());

    run_button->signal_clicked().connect(
        [this]() { open_experiment("initialization"); });
    reference_button->signal_clicked().connect(std::move(on_reference_requested));

    const vector<pair<const char*, const char*>> experiment_buttons = {
        {"type_semantics_auto_button", "auto_deduction"},
        {"type_semantics_decltype_button", "decltype_deduction"},
        {"type_semantics_value_category_button", "value_category"},
        {"type_semantics_cast_button", "cast"},
        {"type_semantics_enum_button", "enum_class"},
    };
    for (const auto& [widget_id, topic_name] : experiment_buttons) {
        auto* button = builder->get_widget<Gtk::Button>(widget_id);
        if (!button) {
            throw runtime_error(
                string("Missing TypeSemantics lesson button: ") + widget_id);
        }
        button->signal_clicked().connect(
            [this, topic_name]() { open_experiment(topic_name); });
    }
}

void TypeSemanticsLessonPage::open_experiment(const string& subchapter_name) {
    const auto& topic = topic_by_name(m_chapter, subchapter_name);
    if (m_on_experiment_requested) {
        m_on_experiment_requested(
            {.function_id = topic.function_id,
             .title = topic.title,
             .description = topic.description,
             .source_path = topic.source,
             .member_name = topic.name},
            false);
    }
}
