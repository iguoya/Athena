#pragma once

#include "content/lesson_doc.h"
#include "registry/chapter_catalog.h"
#include "ui/experiment_dock.h"
#include "ui/lesson_renderer.h"

#include <gtkmm.h>

#include <functional>
#include <string>

using namespace std;

// 数据驱动的章节学习页（ADR 0055）。
//
// 它对所有走数据的章节通用：课文从 GResource 按章节 ID 读，页面结构由
// lesson_page.blp 给，内容由 LessonRenderer 渲染。**新增一章不该碰这个类**
// ——需要碰，说明该加的是块类型或 figure，不是页面分支。
class LessonPage final {
public:
    using ExperimentRequested =
        function<void(const ExperimentSelection&, bool run_immediately)>;

    LessonPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        LessonRenderer::FigureFactory figures,
        ExperimentRequested on_experiment_requested);

    // 页面根控件，交给 MainWindow 挂进标签栈。
    Gtk::Widget& root() const { return *m_root; }

private:
    void build_tab(const LessonDoc& doc, const string& tab_title);

    const ChapterMeta& m_chapter;
    LessonRenderer m_renderer;
    ExperimentRequested m_on_experiment_requested;
    Gtk::Box* m_root = nullptr;
    Gtk::Notebook* m_notebook = nullptr;
};
