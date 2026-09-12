#pragma once

#include "registry/chapter_catalog.h"
#include "ui/experiment_dock.h"
#include "ui/learning_unit_view.h"

#include <gtkmm.h>

#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

using namespace std;

class LearningUnitView;

// ADR 0026 的第一条原生学习场景。它不读取或解析 Markdown；专注实验入口
// 由 MainWindow 注入，因而页面不反向依赖窗口实现。
//
// 「类型推导」标签是完整学习块的样板：概念对比（.blp）→ 运行时对象图
// （Cairo 自绘）→ 预测单元 → 专注实验入口 → 换条件的迁移预测。对象图这类
// 需要绘制的内容按 AGENTS.md「GTK 与 Blueprint 规则」第 3 条留在代码里。
//
// 第一个标签是章节教学大纲（ADR 0028 第一层），用 GTK 控件手写；其余标签是
// 这一页自己的教学过程（第二层）。两者不能互相替换。
class TypeSemanticsLessonPage final {
public:
    TypeSemanticsLessonPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        const map<string, int>& mastery_by_id,
        function<void(const ExperimentSelection&, bool)> on_experiment_requested);

    ~TypeSemanticsLessonPage();

    // AI 自测写入新的熟练度后由 MainWindow 调用，重新给每个学习小节的
    // 标签上色，不重建整页。
    void refresh_progress(const map<string, int>& mastery_by_id);

private:
    // 一个学习小节标签覆盖的知识点。标签是概念分段，可能合并多条成员函数
    // （如“类型推导”同时讲 auto 与 decltype）。
    struct SectionTab {
        string title;
        vector<string> subchapter_names;
    };

    void open_experiment(const string& subchapter_name);
    void apply_tab_labels(const map<string, int>& mastery_by_id);
    Gtk::Widget* build_tab_label(
        const SectionTab& section, const map<string, int>& mastery_by_id) const;

    LearningUnitView& add_learning_unit(
        Gtk::Box& host, LearningUnit data, const string& verify_subchapter);

    // 「让变化说明规则」的可控逐步演示（type_deduction 教案第 4 节分镜）。
    // 步骤 0–6：创建 original / 初始化 copy / 绑定 alias / 绑定 view /
    // copy=7 / alias=99 / view=20 的边界。默认静止，读者操作后才推进。
    // 大纲页的知识点路线图：节点按 requires 的拓扑层排布，连线是先修关系，
    // 配色是掌握目标，底部细条是当前熟练度。全部来自运行时数据，所以只能
    // Cairo 自绘——.blp 表达不了「层数与连线由数据决定」的结构。
    struct RoadmapNode {
        string name;      // subchapter name
        string title;
        MasteryGoal goal = MasteryGoal::Unrated;
        int mastery = 0;  // 0-5
        double x = 0.0;
        double y = 0.0;
        double width = 0.0;
        double height = 0.0;
    };

    void rebuild_roadmap(const map<string, int>& mastery_by_id);

    // 值类别分类器：三类由「有身份 × 可移动」两问决定，点表达式看它落在哪一格。
    // 概念节需要的是辨析，所以做成可切换的对照，而不是一张静态表格（ADR 0033）。
    enum class ValueCategory { None, LValue, XValue, PRValue };
    void select_value_expression(ValueCategory category, const string& expression);
    void draw_value_matrix(
        const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) const;
    void draw_roadmap(
        const Cairo::RefPtr<Cairo::Context>& cr, int width, int height);
    void on_roadmap_pressed(double x, double y);

    void draw_deduction_graph(
        const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) const;
    void set_anim_step(int step);
    void set_anim_playing(bool playing);
    bool on_anim_tick();

    const ChapterMeta& m_chapter;
    function<void(const ExperimentSelection&, bool)> m_on_experiment_requested;

    // 每个学习单元的数据必须比它的 View 活得久（View 持有 const 引用）。
    vector<unique_ptr<LearningUnit>> m_unit_data;
    vector<unique_ptr<LearningUnitView>> m_unit_views;

    Gtk::Notebook* m_section_notebook = nullptr;
    Gtk::DrawingArea* m_roadmap = nullptr;
    Gtk::DrawingArea* m_value_matrix = nullptr;
    Gtk::Label* m_value_result_title = nullptr;
    Gtk::Label* m_value_result_detail = nullptr;
    ValueCategory m_value_selection = ValueCategory::None;
    vector<RoadmapNode> m_roadmap_nodes;
    // 先修边，存的是 m_roadmap_nodes 的下标：from 是先修，to 依赖它。
    vector<pair<size_t, size_t>> m_roadmap_edges;
    vector<SectionTab> m_section_tabs;

    static constexpr int kDeductionAnimSteps = 6;
    Gtk::DrawingArea* m_deduction_graph = nullptr;
    Gtk::Label* m_anim_status = nullptr;
    Gtk::Label* m_anim_note = nullptr;
    Gtk::Button* m_anim_playpause = nullptr;
    int m_anim_step = 0;
    bool m_anim_playing = false;
    sigc::connection m_anim_timer;
};
