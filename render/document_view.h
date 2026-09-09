#pragma once

#include "content/doc_model.h"

#include <gtkmm.h>

#include <cstddef>
#include <functional>
#include <map>
#include <string>
#include <vector>

using namespace std;

// ADR 0024 的共享文档控件渲染器。它只消费结构化 DocModel，既不生成 HTML，
// 也不依赖平台 WebView；调用者可把同一控件嵌入手册、学习工作台或对话框。
class DocumentView final {
public:
    struct HeadingAction {
        string label;
        function<void()> activate;
    };
    using SectionExtension = function<Gtk::Widget*()>;

    explicit DocumentView(string resource_base = "");

    Gtk::Widget& widget() const;
    void set_document(const DocModel& document);
    void set_markdown(const string& markdown);
    void set_heading_actions(map<string, vector<HeadingAction>> actions);
    // 在匹配标题所属小节的末尾插入原生学习控件。这样正文仍按 Markdown
    // 叙述，而预测/验证紧跟它要验证的判断，不需要在文档中写专用标记。
    void set_section_extensions(map<string, vector<SectionExtension>> extensions);

    size_t heading_count() const;
    void scroll_to_heading(size_t index);

private:
    Gtk::Widget* render_block(const DocBlock& block, unsigned list_depth = 0);
    Gtk::Widget* render_children(
        const vector<DocBlock>& blocks, unsigned list_depth = 0);
    string render_inlines(const vector<DocInline>& inlines) const;
    string render_inline(const DocInline& item, bool danger = false) const;
    void append_block(const DocBlock& block, Gtk::Box& target, unsigned list_depth);

    string m_resource_base;
    Gtk::ScrolledWindow* m_scrolled = nullptr;
    Gtk::Box* m_content = nullptr;
    vector<Gtk::Widget*> m_headings;
    map<string, vector<HeadingAction>> m_heading_actions;
    map<string, vector<SectionExtension>> m_section_extensions;
};
