#pragma once

#include <gtkmm.h>

#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace std;

// 一道题要考到什么程度。和知识点级的 MasteryGoal 同一套语义，但落在单题上：
// 同一个知识点里，有的判断必须精通，有的知道有这回事即可。
enum class QuestionGoal { Master, Required, Familiar };

// 随堂考核的一道题。stem 是题干，choices 至少两项，correct_choice 是正确项
// 下标，explain 在判分后展示——它要讲清"为什么"，不是重复一遍答案。
//
// difficulty 1-5，goal 是掌握必要性：两个维度分开标，因为它们不同向——
// 难的不一定要精通（decltype 的取类型规则），简单的也可能必须掌握
// （enum class 的隐式转换边界）。
struct CheckpointQuestion {
    string stem;
    vector<string> choices;
    size_t correct_choice = 0;
    string explain;
    int difficulty = 0;
    QuestionGoal goal = QuestionGoal::Required;
};

// 一节末尾的随堂考核。knowledge_id 是完整函数 ID，考核成绩按它落库；
// experiment_function_id 非空时给出"运行实验验证"入口，让判断能被真实
// 输出检验，而不是停在选项上。
struct Checkpoint {
    string knowledge_id;
    string intro;
    string experiment_function_id;
    vector<CheckpointQuestion> questions;
};

// 随堂考核控件。与 LearningUnitView 的分工：那个是讲解中的单题预测，只影响
// 本次阅读；这个是多题小测，答完按正确率换算 0-5 星并通过回调落库。一次
// 点击不该变成长期掌握度，多题才作数。
class CheckpointView final {
public:
    // on_mastery_changed 在答完全部题目后调用一次，参数是换算出的 0-5 星，
    // 返回是否成功持久化（写库失败时界面要如实说明，不能假装存上了）。
    // on_verify_requested 打开对应的专注实验。两个回调都可以为空。
    CheckpointView(
        const Checkpoint& checkpoint,
        function<bool(const string&, int)> on_mastery_changed,
        function<void(const string&)> on_verify_requested);

    Gtk::Widget& widget() const;

private:
    void show_question();
    void select_choice(size_t index);
    void submit();
    void advance();
    void restart();
    void finish();

    const Checkpoint& m_checkpoint;
    function<bool(const string&, int)> m_on_mastery_changed;
    function<void(const string&)> m_on_verify_requested;

    Glib::RefPtr<Gtk::Builder> m_builder;
    Gtk::Widget* m_root = nullptr;
    Gtk::Label* m_progress = nullptr;
    Gtk::Label* m_intro = nullptr;
    Gtk::Label* m_stem = nullptr;
    Gtk::Label* m_difficulty = nullptr;
    Gtk::Label* m_goal = nullptr;
    Gtk::Box* m_choice_host = nullptr;
    Gtk::Box* m_feedback = nullptr;
    Gtk::Label* m_verdict = nullptr;
    Gtk::Label* m_explain = nullptr;
    Gtk::Button* m_submit = nullptr;
    Gtk::Button* m_next = nullptr;
    Gtk::Button* m_verify = nullptr;
    Gtk::Button* m_restart = nullptr;
    Gtk::Label* m_score = nullptr;

    vector<Gtk::ToggleButton*> m_choice_buttons;
    optional<size_t> m_selected_choice;
    size_t m_index = 0;
    int m_correct = 0;
};
