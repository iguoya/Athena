#pragma once

#include "registry/chapter_catalog.h"
#include "services/case_workspace.h"

#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <atomic>
#include <memory>
#include <string>

using namespace std;

// 动手实验工作台（ADR 0053）：展开骨架的工作副本、保存学员的修改、
// 调本机编译器跑一遍、把编译诊断和输出原样摆出来。
//
// 控件从 Builder 按名字取（window.blp 里的 case_*）。这里不学
// ExperimentDock 把十来个控件指针摊在构造参数上——那套灵活性是为了
// 同一份逻辑接不同 Blueprint，而动手实验只有一处。
class CaseDock final {
public:
    CaseDock(
        const Glib::RefPtr<Gtk::Builder>& builder,
        CaseWorkspace workspace,
        shared_ptr<atomic_bool> ui_alive);
    ~CaseDock();

    CaseDock(const CaseDock&) = delete;
    CaseDock& operator=(const CaseDock&) = delete;

    // 装载一个案例。案例读不出来时把原因写进输出区，不抛给调用方。
    void show(const LabSpec& lab);

    // 当前装着的案例 id，没有则为空串。
    const string& current_case() const { return m_case_id; }

private:
    struct SharedState;

    void run();
    void confirm_reset();
    void reset();
    void save_current_edit();
    void set_running(bool running);
    void set_source_text(const string& text);
    string source_text() const;

    CaseWorkspace m_workspace;
    shared_ptr<atomic_bool> m_ui_alive;
    shared_ptr<SharedState> m_state;

    GtkSourceView* m_source_view = nullptr;
    Gtk::TextView* m_output_view = nullptr;
    Gtk::Label* m_prompt_label = nullptr;
    Gtk::Label* m_goal_label = nullptr;
    Gtk::Label* m_hint_label = nullptr;
    Gtk::Label* m_file_label = nullptr;
    Gtk::Label* m_status_label = nullptr;
    Gtk::Button* m_run_button = nullptr;
    Gtk::Button* m_reset_button = nullptr;
    Gtk::Spinner* m_spinner = nullptr;

    string m_case_id;
    // 当前编辑的文件名。一个案例通常只有 main.cpp；多文件时先认第一个，
    // 等真有多文件案例再加文件切换。
    string m_file_name;
};
