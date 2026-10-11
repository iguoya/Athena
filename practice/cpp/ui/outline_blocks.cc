#include "outline_blocks.h"

#include <stdexcept>

using namespace std;

namespace outline {
namespace {

Glib::RefPtr<Gtk::Builder> load() {
    return Gtk::Builder::create_from_resource("/app/outline.ui");
}

template <typename T>
T& take(const Glib::RefPtr<Gtk::Builder>& builder, const char* id) {
    auto* widget = builder->get_widget<T>(id);
    if (!widget) {
        throw runtime_error(string("outline block not found: ") + id);
    }
    return *widget;
}

struct GoalStyle {
    const char* css;
    const char* level;
};

GoalStyle goal_style(MasteryGoal goal) {
    switch (goal) {
    case MasteryGoal::Master:
        return {"mastery-goal-master", "需要精通"};
    case MasteryGoal::Required:
        return {"mastery-goal-required", "必须掌握"};
    case MasteryGoal::Familiar:
        return {"mastery-goal-familiar", "一般了解"};
    case MasteryGoal::Unrated:
        break;
    }
    return {"mastery-goal-familiar", "尚未评定"};
}

} // namespace

Sections build(
    Gtk::Box& host, const string& lead, const SectionTitles& titles) {
    const auto builder = load();
    auto& root = take<Gtk::Box>(builder, "outline_root");
    take<Gtk::Label>(builder, "outline_lead").set_text(lead);

    const pair<const char*, const string*> headings[] = {
        {"outline_origin", &titles.origin},
        {"outline_model", &titles.model},
        {"outline_scope", &titles.scope},
        {"outline_tradeoff", &titles.tradeoff},
        {"outline_landing", &titles.landing},
    };
    for (const auto& [id, title] : headings) {
        take<Gtk::Frame>(builder, id).set_label(*title);
    }

    Sections sections;
    sections.origin = &take<Gtk::Box>(builder, "outline_origin_body");
    sections.model = &take<Gtk::Box>(builder, "outline_model_body");
    sections.scope = &take<Gtk::Box>(builder, "outline_scope_body");
    sections.tradeoff = &take<Gtk::Box>(builder, "outline_tradeoff_body");
    sections.landing = &take<Gtk::Box>(builder, "outline_landing_body");
    host.append(root);
    return sections;
}

void grade_groups(
    Gtk::Box& host, const ChapterMeta& chapter, const vector<GradeNote>& notes) {
    for (const auto& note : notes) {
        // 成员从配置里筛，不手抄：改了 athena.json 的评级，这里立刻跟着变。
        string members;
        for (const auto& subchapter : chapter.subchapters) {
            if (subchapter.mastery_goal != note.goal) {
                continue;
            }
            if (!members.empty()) {
                members += "、";
            }
            members += subchapter.title;
        }
        if (members.empty()) {
            // 本章没有这一档就不摆空架子。
            continue;
        }

        const auto builder = load();
        auto& root = take<Gtk::Box>(builder, "outline_grade_group");
        auto& badge = take<Gtk::Label>(builder, "outline_grade_badge");
        auto& level = take<Gtk::Label>(builder, "outline_grade_level");
        auto& member_label = take<Gtk::Label>(builder, "outline_grade_members");
        auto& note_label = take<Gtk::Label>(builder, "outline_grade_note");

        const auto style = goal_style(note.goal);
        badge.set_text(note.label.empty() ? style.level : note.label);
        badge.add_css_class(style.css);
        level.set_text(style.level);
        member_label.set_text(members);
        note_label.set_text(note.note);
        note_label.set_visible(!note.note.empty());
        host.append(root);
    }
}

} // namespace outline
