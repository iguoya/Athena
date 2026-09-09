#pragma once

#include "registry/chapter_catalog.h"
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
class TypeSemanticsLessonPage final {
public:
    TypeSemanticsLessonPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        const map<string, int>& mastery_by_id,
        function<void(const ExperimentSelection&, bool)> on_experiment_requested,
        function<void()> on_reference_requested);

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

    const ChapterMeta& m_chapter;
    function<void(const ExperimentSelection&, bool)> m_on_experiment_requested;
    LearningUnit m_learning_unit_data;
    unique_ptr<LearningUnitView> m_learning_unit;
    Gtk::Notebook* m_section_notebook = nullptr;
    vector<SectionTab> m_section_tabs;
};
