#include "learning_unit_view.h"

#include <stdexcept>
#include <utility>

using namespace std;

LearningUnitView::LearningUnitView(
    const LearningUnit& unit,
    function<void(const string&)> on_verify_requested)
    : m_unit(unit),
      m_on_verify_requested(std::move(on_verify_requested)),
      m_builder(Gtk::Builder::create_from_resource("/app/learning_unit.ui")) {
    m_root = m_builder->get_widget<Gtk::Widget>("learning_unit");
    auto* claim = m_builder->get_widget<Gtk::Label>("learning_unit_claim");
    auto* question =
        m_builder->get_widget<Gtk::Label>("learning_unit_question");
    auto* choices = m_builder->get_widget<Gtk::Box>("learning_unit_choices");
    m_check_button =
        m_builder->get_widget<Gtk::Button>("learning_unit_check_button");
    m_feedback_box =
        m_builder->get_widget<Gtk::Box>("learning_unit_feedback_box");
    auto* feedback =
        m_builder->get_widget<Gtk::Label>("learning_unit_feedback");
    auto* follow_up =
        m_builder->get_widget<Gtk::Label>("learning_unit_follow_up");
    auto* verify =
        m_builder->get_widget<Gtk::Button>("learning_unit_verify_button");
    if (!m_root || !claim || !question || !choices || !m_check_button
        || !m_feedback_box || !feedback || !follow_up || !verify) {
        throw runtime_error("Failed to load learning unit Blueprint");
    }

    claim->set_text("判断：" + unit.claim);
    question->set_text("先预测：" + unit.question);
    feedback->set_text(unit.feedback);
    follow_up->set_text("迁移：" + unit.follow_up);
    for (size_t index = 0; index < unit.choices.size(); ++index) {
        auto choice = Gtk::make_managed<Gtk::ToggleButton>(unit.choices[index]);
        choice->set_halign(Gtk::Align::START);
        choice->set_hexpand(false);
        choice->add_css_class("learning-unit-choice");
        choice->signal_clicked().connect(
            [this, index]() { select_choice(index); });
        choices->append(*choice);
        m_choice_buttons.push_back(choice);
    }
    m_check_button->signal_clicked().connect(
        [this]() { reveal_feedback(); });
    verify->signal_clicked().connect([this]() {
        if (m_on_verify_requested) {
            m_on_verify_requested(m_unit.experiment_function_id);
        }
    });
}

Gtk::Widget& LearningUnitView::widget() const {
    return *m_root;
}

void LearningUnitView::select_choice(size_t index) {
    m_selected_choice = index;
    for (size_t current = 0; current < m_choice_buttons.size(); ++current) {
        m_choice_buttons[current]->set_active(current == index);
    }
    m_check_button->set_sensitive(true);
}

void LearningUnitView::reveal_feedback() {
    if (!m_selected_choice) {
        return;
    }
    const bool correct = *m_selected_choice == m_unit.correct_choice;
    auto* feedback =
        m_builder->get_widget<Gtk::Label>("learning_unit_feedback");
    if (feedback) {
        feedback->set_text(
            string(correct ? "✓ 判断正确。" : "✗ 这次预测不符合规则。")
            + " " + m_unit.feedback);
    }
    m_feedback_box->set_visible(true);
    m_check_button->set_sensitive(false);
}
