#include "workbench_page.h"

#include "render/markdown_renderer.h"
#include "ui/icon_utils.h"

#include <iostream>
#include <utility>
#include <vector>

using namespace std;

WorkbenchPage::WorkbenchPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    Gtk::Window& parent,
    function<void(const ExperimentSelection&, bool)> on_experiment_requested)
    : m_chapter(chapter),
      m_content_loader(content_loader),
      m_on_experiment_requested(std::move(on_experiment_requested)) {
    auto* title_label =
        builder->get_widget<Gtk::Label>("workbench_chapter_title_label");
    auto* description_label = builder->get_widget<Gtk::Label>(
        "workbench_chapter_description_label");
    auto* icon = builder->get_widget<Gtk::Image>("workbench_chapter_icon");
    auto* article_host =
        builder->get_widget<Gtk::DrawingArea>("workbench_article_host");

    if (title_label) {
        title_label->set_text(chapter.title);
    }
    if (description_label) {
        description_label->set_text(chapter.description);
    }
    if (icon) {
        configure_icon_image(*icon, chapter.icon, 34);
    }
    if (article_host) {
        m_article_view = create_platform_article_view(*article_host, parent);
    }

    for (const auto& subchapter : chapter.subchapters) {
        m_topic_by_function_id[subchapter.function_id] = &subchapter;
    }
    load_article();
}

WorkbenchPage::~WorkbenchPage() = default;

void WorkbenchPage::load_article() {
    const string& document = m_chapter.overview_document;
    if (document.empty()) {
        cerr << "Workbench chapter " << m_chapter.name
             << " has no overview_document" << endl;
        return;
    }

    const string raw = m_content_loader.load_document(document);
    if (raw.empty()) {
        cerr << "Failed to load workbench document: " << document << endl;
        return;
    }
    const auto slash = document.find_last_of('/');
    const string document_dir =
        slash == string::npos ? string() : document.substr(0, slash + 1);
    const string markdown = inline_markdown_images(
        raw, [&](const string& relative) {
            return m_content_loader.load_document(document_dir + relative);
        });

    vector<MarkdownHeading> headings;
    try {
        headings = parse_markdown_headings(markdown);
    } catch (const exception& error) {
        cerr << "Failed to parse workbench document " << document << ": "
             << error.what() << endl;
        return;
    }

    if (!m_article_view) {
        return;
    }

    vector<HeadingExperimentLink> experiment_links;
    for (const auto& subchapter : m_chapter.subchapters) {
        if (subchapter.teaches && subchapter.teaches->document == document) {
            experiment_links.push_back(
                {.heading = subchapter.teaches->heading,
                 .knowledge_id = subchapter.function_id,
                 .label = subchapter.title});
        }
    }

    m_article_view->set_link_handler(
        [this](const string& knowledge_id) {
            select_by_knowledge_id(knowledge_id);
        });

    try {
        const string stylesheet =
            m_content_loader.load_resource("/app/article.css");
        if (stylesheet.empty()) {
            throw runtime_error("Article stylesheet is unavailable");
        }
        m_article_view->load_html(
            render_markdown_html(markdown, stylesheet, headings, experiment_links),
            m_content_loader.document_base_directory(document));
    } catch (const exception& error) {
        cerr << "Failed to render workbench document " << document << ": "
             << error.what() << endl;
    }
}

void WorkbenchPage::select_by_knowledge_id(const string& knowledge_id) {
    const auto found = m_topic_by_function_id.find(knowledge_id);
    if (found == m_topic_by_function_id.end()) {
        cerr << "Workbench: no subchapter for knowledge id '" << knowledge_id
             << "'" << endl;
        return;
    }

    const SubChapter& subchapter = *found->second;
    if (m_on_experiment_requested) {
        m_on_experiment_requested(
            {.function_id = subchapter.function_id,
             .title = subchapter.title,
             .description = subchapter.description,
             .source_path = subchapter.source,
             .member_name = subchapter.name},
            false);
    }
}
