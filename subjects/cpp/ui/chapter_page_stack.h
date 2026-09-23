#pragma once

#include <gtkmm.h>

#include <set>
#include <string>

using namespace std;

// 分类内的章节页面栈：独占 Gtk::Stack 的子页占位、替换、切换与常驻页保留。
// 不认识具体页面模块，也不装配标签按钮——章节之间的横向切换由顶栏的章节
// 切换器承担，进入分类默认落在生成的索引页（见 ADR 0021）。
class ChapterPageStack final {
public:
    enum class Persistence {
        // 切换分类时随分类一起从 Stack 移除。
        Transient,
        // 常驻 Stack（手册页：ArticleView 生命周期由页面对象独占）。
        Persistent,
    };

    explicit ChapterPageStack(Gtk::Stack& stack);

    ChapterPageStack(const ChapterPageStack&) = delete;
    ChapterPageStack& operator=(const ChapterPageStack&) = delete;

    // 移除当前分类的全部 Transient 页面；Persistent 页面保留。
    void reset();

    // 登记页面控件；同键已存在则替换。
    void set_page(
        const string& key,
        Gtk::Widget& widget,
        const string& title,
        Persistence persistence = Persistence::Transient);
    // 仅当该键尚无页面时放一个空占位，等激活时再换成真实控件。
    void set_placeholder(const string& key, const string& title);
    bool has_page(const string& key) const;

    // 切到指定页（该键无页面时不动）。
    void show(const string& key);

    const string& current_key() const { return m_current_key; }

private:
    Gtk::Stack& m_stack;
    set<string> m_page_keys;
    set<string> m_persistent_keys;
    string m_current_key;
};
