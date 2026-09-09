#pragma once

#include "content/content_loader.h"
#include "render/document_view.h"

#include <gtkmm.h>

#include <map>
#include <memory>
#include <string>
#include <vector>

using namespace std;

// 一部分类手册的完整页面。它独占 GTK 文档控件和文档锚点；MainWindow
// 只负责把 widget 放进 Stack 并请求文档跳转。
class HandbookPage final {
public:
    HandbookPage(
        string category_name,
        const vector<string>& documents,
        const ContentLoader& content_loader,
        Gtk::Window& parent);
    ~HandbookPage();

    HandbookPage(const HandbookPage&) = delete;
    HandbookPage& operator=(const HandbookPage&) = delete;

    Gtk::Widget& widget() const;
    void scroll_to_document(const string& document_path);

private:
    string m_category_name;
    Gtk::Widget* m_page = nullptr;
    map<string, size_t> m_heading_by_document;
    unique_ptr<DocumentView> m_document_view;
};
