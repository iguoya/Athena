#pragma once

#include "registry/chapter_catalog.h"

#include <gtkmm.h>

#include <functional>
#include <map>
#include <set>
#include <string>
#include <vector>

using namespace std;

// 分类内的章节标签条与页面栈：独占标签按钮装配、编组、页面占位与切换。
// MainWindow 只声明「有哪些标签、激活时做什么」，不再直接摆 GTK 控件或
// 记账 Stack 子页。标签条不认识具体页面模块，激活行为通过回调回传。
class ChapterNavStrip final {
public:
    struct TabSpec {
        // 稳定页面键；show() 与 has_page() 按它定位，可留空表示标签不绑页面。
        string key;
        string label;
        string tooltip;
        IconSpec icon;
    };

    enum class Persistence {
        // 切换分类时随标签一起从 Stack 移除。
        Transient,
        // 常驻 Stack（手册页：ArticleView 生命周期由页面对象独占）。
        Persistent,
    };

    ChapterNavStrip(Gtk::FlowBox& tab_box, Gtk::Stack& stack);

    ChapterNavStrip(const ChapterNavStrip&) = delete;
    ChapterNavStrip& operator=(const ChapterNavStrip&) = delete;

    // 移除当前分类的全部标签按钮与 Transient 页面；Persistent 页面保留。
    void reset();

    // 追加一个标签。用户点击或 show() 命中时触发 on_activate。
    void add_tab(const TabSpec& spec, function<void()> on_activate);

    // 登记页面控件；同键已存在则替换（保持可见状态由 reveal 决定）。
    void set_page(
        const string& key,
        Gtk::Widget& widget,
        const string& title,
        Persistence persistence = Persistence::Transient);
    // 仅当该键尚无页面时放一个空占位，等激活时再换成真实控件。
    void set_placeholder(const string& key, const string& title);
    bool has_page(const string& key) const;

    // 切到指定页并高亮其标签（不重复触发 on_activate）。
    void show(const string& key);
    // 只切 Stack 可见页，不动标签状态；供 on_activate 内部收尾调用。
    void reveal(const string& key);
    // 激活第一个标签，触发其 on_activate。
    void activate_first();

    const string& current_key() const { return m_current_key; }

private:
    Gtk::FlowBox& m_tab_box;
    Gtk::Stack& m_stack;
    vector<Gtk::ToggleButton*> m_tabs;
    std::map<string, Gtk::ToggleButton*> m_button_by_key;
    set<string> m_page_keys;
    set<string> m_persistent_keys;
    string m_current_key;
    bool m_suppress_activate = false;
};
