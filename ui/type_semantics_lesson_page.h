#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "render/document_view.h"
#include "ui/experiment_dock.h"

#include <gtkmm.h>

#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

using namespace std;

class LearningUnitView;

// ADR 0026 的第一条原生学习场景。它不读取或解析 Markdown；参考资料跳转与
// 专注实验入口都由 MainWindow 注入，因而页面不反向依赖窗口实现。
//
// 「类型推导」标签是完整学习块的样板：概念对比（.blp）→ 运行时对象图
// （Cairo 自绘）→ 预测单元 → 专注实验入口 → 换条件的迁移预测。对象图这类
// 需要绘制的内容按 AGENTS.md「GTK 与 Blueprint 规则」第 3 条留在代码里。
//
// 第一个标签是例外：按 ADR 0028，大纲那一层就是章节的 overview_document，
// 页面直接用 DocumentView 渲染那一份 Markdown，不另写一份控件树副本。
class TypeSemanticsLessonPage final {
public:
    TypeSemanticsLessonPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        const ContentLoader& content_loader,
        const map<string, int>& mastery_by_id,
        function<void(const ExperimentSelection&, bool)> on_experiment_requested,
        function<void()> on_reference_requested);

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
    // 把 overview_document 渲染进「大纲」标签。文档缺失时留空并记日志，
    // 不影响其余学习标签可用。
    void render_overview(
        const Glib::RefPtr<Gtk::Builder>& builder,
        const ContentLoader& content_loader);
    void apply_tab_labels(const map<string, int>& mastery_by_id);
    Gtk::Widget* build_tab_label(
        const SectionTab& section, const map<string, int>& mastery_by_id) const;

    LearningUnitView& add_learning_unit(
        Gtk::Box& host, LearningUnit data, const string& verify_subchapter);

    // 「让变化说明规则」的可控逐步演示（type_deduction 教案第 4 节分镜）。
    // 步骤 0–6：创建 original / 初始化 copy / 绑定 alias / 绑定 view /
    // copy=7 / alias=99 / view=20 的边界。默认静止，读者操作后才推进。
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
    vector<SectionTab> m_section_tabs;
    unique_ptr<DocumentView> m_overview_view;

    static constexpr int kDeductionAnimSteps = 6;
    Gtk::DrawingArea* m_deduction_graph = nullptr;
    Gtk::Label* m_anim_status = nullptr;
    Gtk::Label* m_anim_note = nullptr;
    Gtk::Button* m_anim_playpause = nullptr;
    int m_anim_step = 0;
    bool m_anim_playing = false;
    sigc::connection m_anim_timer;
};
