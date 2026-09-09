#include "handbook_page.h"

#include <iostream>
#include <algorithm>
#include <stdexcept>
#include <utility>

using namespace std;

HandbookPage::HandbookPage(
    string category_name,
    const vector<string>& documents,
    const ContentLoader& content_loader,
    Gtk::Window&)
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

    string combined_markdown;
    size_t heading_count = 0;
    for (const auto& document : documents) {
        const string raw = content_loader.load_document(document);
        if (raw.empty()) {
            cerr << "Failed to load handbook document: " << document << endl;
            continue;
        }
        try {
            const auto model = parse_document_blocks(raw);
            const size_t headings = count_if(
                model.blocks.begin(), model.blocks.end(), [](const DocBlock& block) {
                    return block.kind == DocBlockKind::Heading;
                });
            if (headings != 0) {
                m_heading_by_document[document] = heading_count;
            }
            heading_count += headings;
        } catch (const exception& error) {
            cerr << "Failed to parse handbook document " << document
             << ": " << error.what() << endl;
            continue;
        }

        if (!combined_markdown.empty()) {
            combined_markdown += "\n\n---\n\n";
        }
        combined_markdown += raw;
    }

    if (combined_markdown.empty()) {
        cerr << "Handbook for " << m_category_name
             << " has no renderable content" << endl;
        return;
    }

    page->append(*frame);

    try {
        const auto slash = documents.front().find_last_of('/');
        const string resource_base = slash == string::npos
            ? "/app/"
            : "/app/" + documents.front().substr(0, slash + 1);
        m_document_view = make_unique<DocumentView>(resource_base);
        frame->set_child(m_document_view->widget());
        m_document_view->set_markdown(combined_markdown);
    } catch (const exception& error) {
        cerr << "Failed to render GTK handbook for " << m_category_name << ": "
             << error.what() << endl;
    }
}

HandbookPage::~HandbookPage() = default;

Gtk::Widget& HandbookPage::widget() const {
    return *m_page;
}

void HandbookPage::scroll_to_document(const string& document_path) {
    const auto heading = m_heading_by_document.find(document_path);
    if (heading != m_heading_by_document.end() && m_document_view) {
        m_document_view->scroll_to_heading(heading->second);
    }
}
