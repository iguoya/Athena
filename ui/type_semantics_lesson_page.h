#pragma once

#include "registry/chapter_catalog.h"
#include "ui/experiment_dock.h"

#include <gtkmm.h>

#include <functional>
#include <memory>

using namespace std;

class LearningUnitView;

// ADR 0026 的第一条原生学习场景。它不读取或解析 Markdown；参考资料跳转与
// 专注实验入口都由 MainWindow 注入，因而页面不反向依赖窗口实现。
class TypeSemanticsLessonPage final {
public:
    TypeSemanticsLessonPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        function<void(const ExperimentSelection&, bool)> on_experiment_requested,
        function<void()> on_reference_requested);

private:
    void open_experiment(const string& subchapter_name);

    const ChapterMeta& m_chapter;
    function<void(const ExperimentSelection&, bool)> m_on_experiment_requested;
    LearningUnit m_learning_unit_data;
    unique_ptr<LearningUnitView> m_learning_unit;
};
