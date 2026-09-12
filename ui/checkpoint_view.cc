#include "checkpoint_view.h"

#include "services/ai_service.h"

#include <stdexcept>
#include <utility>

using namespace std;

CheckpointView::CheckpointView(
    const Checkpoint& checkpoint,
    function<bool(const string&, int)> on_mastery_changed,
    function<void(const string&)> on_verify_requested)
    : m_checkpoint(checkpoint),
      m_on_mastery_changed(std::move(on_mastery_changed)),
      m_on_verify_requested(std::move(on_verify_requested)),
      m_builder(Gtk::Builder::create_from_resource("/app/checkpoint.ui")) {
    m_root = m_builder->get_widget<Gtk::Widget>("checkpoint");
    m_progress = m_builder->get_widget<Gtk::Label>("checkpoint_progress");
    m_intro = m_builder->get_widget<Gtk::Label>("checkpoint_intro");
    m_stem = m_builder->get_widget<Gtk::Label>("checkpoint_stem");
    m_difficulty = m_builder->get_widget<Gtk::Label>("checkpoint_difficulty");
    m_goal = m_builder->get_widget<Gtk::Label>("checkpoint_goal");
    m_choice_host = m_builder->get_widget<Gtk::Box>("checkpoint_choice_host");
    m_feedback = m_builder->get_widget<Gtk::Box>("checkpoint_feedback");
    m_verdict = m_builder->get_widget<Gtk::Label>("checkpoint_verdict");
    m_explain = m_builder->get_widget<Gtk::Label>("checkpoint_explain");
    m_submit = m_builder->get_widget<Gtk::Button>("checkpoint_submit");
    m_next = m_builder->get_widget<Gtk::Button>("checkpoint_next");
    m_verify = m_builder->get_widget<Gtk::Button>("checkpoint_verify");
    m_restart = m_builder->get_widget<Gtk::Button>("checkpoint_restart");
    m_score = m_builder->get_widget<Gtk::Label>("checkpoint_score");
    if (!m_root || !m_progress || !m_intro || !m_stem || !m_difficulty
        || !m_goal || !m_choice_host
        || !m_feedback || !m_verdict || !m_explain || !m_submit || !m_next
        || !m_verify || !m_restart || !m_score) {
        throw runtime_error("Failed to load checkpoint Blueprint");
    }
    if (checkpoint.questions.empty()) {
        throw invalid_argument("checkpoint needs at least one question");
    }

    m_intro->set_text(checkpoint.intro);
    m_intro->set_visible(!checkpoint.intro.empty());
    m_submit->signal_clicked().connect([this] { submit(); });
    m_next->signal_clicked().connect([this] { advance(); });
    m_restart->signal_clicked().connect([this] { restart(); });
    m_verify->signal_clicked().connect([this] {
        if (m_on_verify_requested
            && !m_checkpoint.experiment_function_id.empty()) {
            m_on_verify_requested(m_checkpoint.experiment_function_id);
        }
    });
    show_question();
}

Gtk::Widget& CheckpointView::widget() const {
    return *m_root;
}

void CheckpointView::show_question() {
    const auto& question = m_checkpoint.questions[m_index];
    m_progress->set_text(
        "第 " + to_string(m_index + 1) + " / "
        + to_string(m_checkpoint.questions.size()) + " 题");
    m_stem->set_text(question.stem);

    // 难度与掌握必要性分别编码：难度用色阶，掌握目标用另一套徽章配色，
    // 两个维度不共用一套视觉编码（AGENTS.md）。
    const int level = question.difficulty < 1 ? 1
                    : question.difficulty > 5 ? 5
                                              : question.difficulty;
    m_difficulty->set_text("难度 " + to_string(level) + " / 5");
    for (int i = 1; i <= 5; ++i) {
        m_difficulty->remove_css_class("difficulty-level-" + to_string(i));
    }
    m_difficulty->add_css_class("difficulty-level-" + to_string(level));

    struct GoalStyle {
        const char* text;
        const char* css;
        const char* tip;
    };
    const GoalStyle goal_style =
        question.goal == QuestionGoal::Master
            ? GoalStyle{"需要精通", "mastery-goal-master",
                        "需要精通：判断要稳，能说清规则边界"}
        : question.goal == QuestionGoal::Familiar
            ? GoalStyle{"一般了解", "mastery-goal-familiar",
                        "一般了解：知道有这回事，需要时能查"}
            : GoalStyle{"必须掌握", "mastery-goal-required",
                        "必须掌握：能正确使用，并说明为什么这样选"};
    m_goal->set_text(goal_style.text);
    for (const char* css : {"mastery-goal-master", "mastery-goal-required",
                            "mastery-goal-familiar"}) {
        m_goal->remove_css_class(css);
    }
    m_goal->add_css_class(goal_style.css);
    m_goal->set_tooltip_text(goal_style.tip);

    while (auto* child = m_choice_host->get_first_child()) {
        m_choice_host->remove(*child);
    }
    m_choice_buttons.clear();
    m_selected_choice.reset();
    for (size_t index = 0; index < question.choices.size(); ++index) {
        auto* choice =
            Gtk::make_managed<Gtk::ToggleButton>(question.choices[index]);
        choice->set_halign(Gtk::Align::START);
        choice->add_css_class("learning-unit-choice");
        choice->signal_clicked().connect(
            [this, index] { select_choice(index); });
        m_choice_host->append(*choice);
        m_choice_buttons.push_back(choice);
    }

    m_feedback->set_visible(false);
    m_submit->set_visible(true);
    m_submit->set_sensitive(false);
    m_next->set_visible(false);
    m_verify->set_visible(false);
}

void CheckpointView::select_choice(size_t index) {
    // 判分后不再允许改选：这一题已经计入成绩，改答案只会让分数失去意义。
    if (m_feedback->get_visible()) {
        for (size_t i = 0; i < m_choice_buttons.size(); ++i) {
            m_choice_buttons[i]->set_active(
                m_selected_choice && *m_selected_choice == i);
        }
        return;
    }
    m_selected_choice = index;
    for (size_t i = 0; i < m_choice_buttons.size(); ++i) {
        m_choice_buttons[i]->set_active(i == index);
    }
    m_submit->set_sensitive(true);
}

void CheckpointView::submit() {
    if (!m_selected_choice) {
        return;
    }
    const auto& question = m_checkpoint.questions[m_index];
    const bool right = *m_selected_choice == question.correct_choice;
    if (right) {
        ++m_correct;
    }

    // 标出正确答案；答错时同时标出选错的那一项。只说"不对"而不指出哪个才对，
    // 读者还得回头自己找，考核的反馈价值就打了折。
    if (question.correct_choice < m_choice_buttons.size()) {
        m_choice_buttons[question.correct_choice]->add_css_class(
            "choice-correct");
    }
    if (!right && *m_selected_choice < m_choice_buttons.size()) {
        m_choice_buttons[*m_selected_choice]->add_css_class("choice-wrong");
    }

    m_verdict->set_text(right ? "答对了" : "不对");
    m_verdict->remove_css_class("correct");
    m_verdict->remove_css_class("incorrect");
    m_verdict->add_css_class(right ? "correct" : "incorrect");
    m_explain->set_text(question.explain);
    m_feedback->set_visible(true);
    m_submit->set_visible(false);
    // 判断只是预期，真实输出才是证据——每题判分后都给一次去验证的机会。
    m_verify->set_visible(
        !m_checkpoint.experiment_function_id.empty() && m_on_verify_requested);

    if (m_index + 1 < m_checkpoint.questions.size()) {
        m_next->set_visible(true);
    } else {
        finish();
    }
}

void CheckpointView::advance() {
    if (m_index + 1 >= m_checkpoint.questions.size()) {
        return;
    }
    ++m_index;
    show_question();
}

void CheckpointView::finish() {
    const int total = static_cast<int>(m_checkpoint.questions.size());
    const int mastery = mastery_from_quiz_score(m_correct, total);
    bool saved = false;
    if (m_on_mastery_changed) {
        saved = m_on_mastery_changed(m_checkpoint.knowledge_id, mastery);
    }
    m_score->set_text(
        "本次成绩：" + to_string(m_correct) + " / " + to_string(total)
        + "，评定为 " + to_string(mastery) + " 星。"
        + (saved ? "已记入学习进度。" : "暂时无法记入学习进度。"));
    m_score->remove_css_class("correct");
    if (mastery >= 5) {
        m_score->add_css_class("correct");
    }
    m_score->set_visible(true);
    m_restart->set_visible(true);
    m_progress->set_text("已完成");
}

void CheckpointView::restart() {
    m_index = 0;
    m_correct = 0;
    m_score->set_visible(false);
    m_restart->set_visible(false);
    show_question();
}
