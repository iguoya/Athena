#include "type_semantics_lesson_page.h"

#include "ui/learning_unit_view.h"

#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <string>
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

string repeat_star(int count) {
    string stars;
    for (int index = 0; index < count; ++index) {
        stars += "★";
    }
    return stars;
}

// 平均熟练度落在哪一档：完全没碰过、学习中、已全部掌握。三档语义与
// 知识图谱节点一致，直接复用它的配色。
const char* mastery_tier(double average_mastery) {
    if (average_mastery <= 0.0) {
        return "mastery-none";
    }
    if (average_mastery >= 5.0) {
        return "mastery-all";
    }
    return "mastery-some";
}

} // namespace

TypeSemanticsLessonPage::TypeSemanticsLessonPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const map<string, int>& mastery_by_id,
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
    m_section_notebook = builder->get_widget<Gtk::Notebook>(
        "type_semantics_section_notebook");
    if (!unit_host || !run_button || !reference_button || !m_section_notebook) {
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

    // 标签顺序必须与 type_semantics_lesson.blp 中 Notebook 页顺序一致。
    // 一个标签是一个学习小节，可能覆盖不止一个知识点。
    m_section_tabs = {
        {"初始化", {"initialization"}},
        {"类型推导", {"auto_deduction", "decltype_deduction"}},
        {"值类别", {"value_category"}},
        {"类型转换", {"cast"}},
        {"enum class", {"enum_class"}},
    };
    apply_tab_labels(mastery_by_id);
}

void TypeSemanticsLessonPage::refresh_progress(
    const map<string, int>& mastery_by_id) {
    apply_tab_labels(mastery_by_id);
}

void TypeSemanticsLessonPage::apply_tab_labels(
    const map<string, int>& mastery_by_id) {
    if (m_section_notebook == nullptr) {
        return;
    }
    const int page_count = m_section_notebook->get_n_pages();
    if (page_count != static_cast<int>(m_section_tabs.size())) {
        cerr << "TypeSemantics lesson: Notebook has " << page_count
             << " pages but " << m_section_tabs.size()
             << " section descriptors; tab styling skipped" << endl;
        return;
    }
    for (int index = 0; index < page_count; ++index) {
        auto* page = m_section_notebook->get_nth_page(index);
        if (page == nullptr) {
            continue;
        }
        m_section_notebook->set_tab_label(
            *page,
            *build_tab_label(
                m_section_tabs[static_cast<size_t>(index)], mastery_by_id));
    }
}

Gtk::Widget* TypeSemanticsLessonPage::build_tab_label(
    const SectionTab& section, const map<string, int>& mastery_by_id) const {
    int importance = 0;
    double mastery_sum = 0.0;
    int mastery_count = 0;
    for (const auto& subchapter_name : section.subchapter_names) {
        const auto& subchapter = topic_by_name(m_chapter, subchapter_name);
        importance = max(importance, subchapter.importance);
        const auto found = mastery_by_id.find(subchapter.function_id);
        mastery_sum += found == mastery_by_id.end() ? 0.0 : found->second;
        ++mastery_count;
    }
    const double average_mastery =
        mastery_count == 0 ? 0.0 : mastery_sum / mastery_count;

    auto* row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
    row->add_css_class("lesson-tab");

    auto* title = Gtk::make_managed<Gtk::Label>(section.title);
    title->add_css_class("lesson-tab-title");
    row->append(*title);

    if (importance > 0) {
        auto* stars = Gtk::make_managed<Gtk::Label>(repeat_star(importance));
        stars->add_css_class("lesson-tab-stars");
        stars->add_css_class("importance-level-" + to_string(importance));
        stars->set_tooltip_text("知识点重要度 " + to_string(importance) + " / 5");
        row->append(*stars);
    }

    auto* dot = Gtk::make_managed<Gtk::Label>("●");
    dot->add_css_class("lesson-tab-dot");
    dot->add_css_class(mastery_tier(average_mastery));
    dot->set_tooltip_text(
        average_mastery <= 0.0
            ? string("尚未开始")
            : "平均熟练度 " + to_string(static_cast<int>(average_mastery + 0.5))
                  + " / 5");
    row->append(*dot);

    return row;
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
