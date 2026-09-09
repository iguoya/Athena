#pragma once

#include "registry/chapter_catalog.h"

#include <gtkmm.h>

#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace std;

// 单个 ADR 0025 学习单元的 GTK 外壳。它只持有本次阅读的预测状态；不把
// 一次点击误写成长期掌握度，验证动作仍交给现有专注实验页面。
class LearningUnitView final {
public:
    LearningUnitView(
        const LearningUnit& unit,
        function<void(const string&)> on_verify_requested);

    Gtk::Widget& widget() const;

private:
    void select_choice(size_t index);
    void reveal_feedback();

    const LearningUnit& m_unit;
    function<void(const string&)> m_on_verify_requested;
    Glib::RefPtr<Gtk::Builder> m_builder;
    Gtk::Widget* m_root = nullptr;
    Gtk::Button* m_check_button = nullptr;
    Gtk::Box* m_feedback_box = nullptr;
    vector<Gtk::ToggleButton*> m_choice_buttons;
    optional<size_t> m_selected_choice;
};
