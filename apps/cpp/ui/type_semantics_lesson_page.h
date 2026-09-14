#pragma once

#include "registry/chapter_catalog.h"
#include "ui/experiment_dock.h"
#include "render/roadmap_view.h"
#include "ui/checkpoint_view.h"
#include "ui/learning_unit_view.h"

#include <gtkmm.h>

#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

using namespace std;

class CheckpointView;
class LearningUnitView;

// ADR 0026 的第一条原生学习场景。它不读取或解析 Markdown；专注实验入口
// 由 MainWindow 注入，因而页面不反向依赖窗口实现。
//
// 「类型推导」标签是完整学习块的样板：概念对比（.blp）→ 运行时对象图
// （Cairo 自绘）→ 预测单元 → 专注实验入口 → 换条件的迁移预测。对象图这类
// 需要绘制的内容按 AGENTS.md「GTK 与 Blueprint 规则」第 3 条留在代码里。
//
// 第一个标签是章节教学大纲（ADR 0028 第一层），用 GTK 控件手写；其余标签是
// 这一页自己的教学过程（第二层）。两者不能互相替换。ADR 0039 撤销了原先排在
// 最前面的「本章导览」——它那四块内容大纲都有，并存只会漂移。
class TypeSemanticsLessonPage final {
public:
    TypeSemanticsLessonPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        const map<string, int>& mastery_by_id,
        function<void(const ExperimentSelection&, bool)> on_experiment_requested,
        // 随堂考核答完后回写评定结果（完整函数 ID、0-5 星、答对数、总题数），
        // 返回是否落库成功。页面不持有 LearningStore：写库属于持久化层，
        // 这里只交出结果。
        CheckpointView::OnScored on_mastery_recorded);

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
    // 页头随当前标签更新：小节名、它要解决什么（取自 athena.json 的
    // description），以及实验台按钮此刻指向哪个知识点。都不写死成某一节。
    void apply_section_header(int page_index);
    void apply_tab_labels(const map<string, int>& mastery_by_id);
    Gtk::Widget* build_tab_label(
        const SectionTab& section, const map<string, int>& mastery_by_id) const;

    LearningUnitView& add_learning_unit(
        Gtk::Box& host, LearningUnit data, const string& verify_subchapter);

    // 在某节末尾挂一组随堂考核。data.knowledge_id 用短名（成员函数名），
    // 这里展开成完整函数 ID 再落库。
    CheckpointView& add_checkpoint(Gtk::Box& host, Checkpoint data);
    void build_checkpoints(const Glib::RefPtr<Gtk::Builder>& builder);

    // 「让变化说明规则」的可控逐步演示（type_deduction 教案第 4 节分镜）。
    // 步骤 0–6：创建 original / 初始化 copy / 绑定 alias / 绑定 view /
    // copy=7 / alias=99 / view=20 的边界。默认静止，读者操作后才推进。
    // 大纲页的知识点路线图：节点按 requires 的拓扑层排布，连线是先修关系，
    // 配色是掌握目标，底部细条是当前熟练度。全部来自运行时数据，所以只能
    // Cairo 自绘——.blp 表达不了「层数与连线由数据决定」的结构。

    // 值类别分类器：三类由「有身份 × 可移动」两问决定，点表达式看它落在哪一格。
    // 概念节需要的是辨析，所以做成可切换的对照，而不是一张静态表格（ADR 0033）。
    enum class ValueCategory { None, LValue, XValue, PRValue };
    void select_value_expression(ValueCategory category, const string& expression);
    void draw_value_matrix(
        const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) const;

    // decltype 活对照：同一批声明，五个表达式各问一次 auto 与 decltype。
    // 两列结果完全由「名字看声明、表达式看值类别」两条规则算出来，所以按
    // ADR 0033 做成可切换的活对照，而不是一张会和规则说明各说各话的静态表。
    void select_decltype_expression(size_t index);

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
    // 大纲页的知识点路线图：配色表达难度，节点文字给掌握目标，底部细条是
    // 熟练度（ADR 0039 合并导览后只剩这一张）。
    unique_ptr<RoadmapView> m_outline_roadmap;
    vector<unique_ptr<Checkpoint>> m_checkpoint_data;
    vector<unique_ptr<CheckpointView>> m_checkpoint_views;
    CheckpointView::OnScored m_on_mastery_recorded;

    Gtk::Notebook* m_section_notebook = nullptr;
    Gtk::Label* m_page_title = nullptr;
    Gtk::Label* m_page_subtitle = nullptr;
    Gtk::Button* m_open_dock_button = nullptr;
    // 实验台按钮当前指向的知识点。导览与教学大纲没有自己的实验，退回本章
    // 第一个知识点，并由 tooltip 说明打开的是哪一个。
    string m_dock_topic;
    Gtk::DrawingArea* m_value_matrix = nullptr;
    Gtk::Label* m_value_result_title = nullptr;
    Gtk::Label* m_value_result_detail = nullptr;
    ValueCategory m_value_selection = ValueCategory::None;
    Gtk::Label* m_decltype_auto_result = nullptr;
    Gtk::Label* m_decltype_result = nullptr;
    Gtk::Label* m_decltype_result_title = nullptr;
    Gtk::Label* m_decltype_result_detail = nullptr;
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
