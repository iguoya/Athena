#include "handbook_page.h"

#include "render/markdown_renderer.h"
#include "ui/markdown_fallback.h"

#include <iostream>
#include <stdexcept>
#include <utility>

using namespace std;

HandbookPage::HandbookPage(
    string category_name,
    const vector<string>& documents,
    const ContentLoader& content_loader,
    Gtk::Window& parent)
    : m_category_name(std::move(category_name)) {
    if (documents.empty()) {
        auto placeholder = Gtk::make_managed<Gtk::Label>(
            "本分类的手册还没有收录文档。");
        placeholder->set_halign(Gtk::Align::CENTER);
        placeholder->set_valign(Gtk::Align::CENTER);
        placeholder->add_css_class("dim-label");
        m_page = placeholder;
        return;
    }

    auto page = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL);
    page->set_hexpand(true);
    page->set_vexpand(true);
    page->set_margin_top(16);
    page->set_margin_start(20);
    page->set_margin_end(20);
    page->set_margin_bottom(20);
    page->add_css_class("article-page");
    m_page = page;

    auto frame = Gtk::make_managed<Gtk::Frame>();
    frame->set_hexpand(true);
    frame->set_vexpand(true);
    frame->add_css_class("article-surface");

    auto host = Gtk::make_managed<Gtk::DrawingArea>();
    host->set_hexpand(true);
    host->set_vexpand(true);
    frame->set_child(*host);

    string combined_markdown;
    size_t heading_count = 0;
    for (const auto& document : documents) {
        const string markdown = content_loader.load_document(document);
        if (markdown.empty()) {
            cerr << "Failed to load handbook document: " << document << endl;
            continue;
        }
        vector<MarkdownHeading> headings;
        try {
            headings = parse_markdown_headings(markdown);
        } catch (const exception& error) {
            cerr << "Failed to parse handbook document " << document
                 << ": " << error.what() << endl;
            continue;
        }
        if (!headings.empty()) {
            m_anchor_by_document[document] =
                "athena-heading-" + to_string(heading_count);
        }
        heading_count += headings.size();

        if (!combined_markdown.empty()) {
            combined_markdown += "\n\n---\n\n";
        }
        combined_markdown += markdown;
    }

    if (combined_markdown.empty()) {
        cerr << "Handbook for " << m_category_name
             << " has no renderable content" << endl;
        return;
    }

    m_article_view = create_platform_article_view(*host, parent);
    if (!m_article_view) {
        // Linux 等平台还没有 WebView 后端：退回纯文本显示 Markdown 原文，
        // 不留一片空白（见 docs/ARCHITECTURE.md 路线图第 9 条）。
        page->append(*make_markdown_fallback_view(combined_markdown));
        return;
    }
    page->append(*frame);

    try {
        const auto headings = parse_markdown_headings(combined_markdown);
        const string stylesheet =
            content_loader.load_resource("/app/article.css");
        if (stylesheet.empty()) {
            throw runtime_error("Article stylesheet is unavailable");
        }
        m_article_view->load_html(
            render_markdown_html(combined_markdown, stylesheet, headings),
            content_loader.document_base_directory(documents.front()));
    } catch (const exception& error) {
        cerr << "Failed to render handbook for " << m_category_name << ": "
             << error.what() << endl;
    }
}

HandbookPage::~HandbookPage() = default;

Gtk::Widget& HandbookPage::widget() const {
    return *m_page;
}

void HandbookPage::scroll_to_document(const string& document_path) {
    const auto anchor = m_anchor_by_document.find(document_path);
    if (anchor != m_anchor_by_document.end() && m_article_view) {
        m_article_view->scroll_to_anchor(anchor->second);
    }
}
