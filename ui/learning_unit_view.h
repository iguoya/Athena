#pragma once

#include <gtkmm.h>

#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace std;

// 一条嵌在某节讲解之后的微型学习循环（ADR 0025）。原生学习页在代码里直接
// 构造它——ADR 0034 删掉 Markdown 手册后，学习单元不再由配置按标题定位。
// 它只保存要显示的内容与稳定实验 ID；选择状态属于 UI，不写回数据库。
struct LearningUnit {
    string id;
    string heading;
    string claim;
    string question;
    vector<string> choices;
    size_t correct_choice = 0;
    string feedback;
    string follow_up;
    string experiment_function_id;
};

// 单个 ADR 0025 学习单元的 GTK 外壳。它只持有本次阅读的预测状态；不把
// 一次点击误写成长期掌握度，验证动作仍交给现有专注实验页面。
//
// 要把结果计入熟练度的是一节末尾的随堂考核（ui/checkpoint_view.h）：那里是
// 多题小测，按正确率换算后落库。两者分工不同，别把写库挪到这里来。
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
