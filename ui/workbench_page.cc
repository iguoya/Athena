#include "workbench_page.h"

#include "render/markdown_renderer.h"
#include "ui/icon_utils.h"

#include <algorithm>
#include <iostream>
#include <utility>
#include <vector>

using namespace std;

WorkbenchPage::WorkbenchPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    ExperimentRunner& experiment_runner,
    Gtk::Window& parent)
    : m_chapter(chapter), m_content_loader(content_loader) {
    auto* title_label =
        builder->get_widget<Gtk::Label>("workbench_chapter_title_label");
    auto* description_label = builder->get_widget<Gtk::Label>(
        "workbench_chapter_description_label");
    auto* icon = builder->get_widget<Gtk::Image>("workbench_chapter_icon");
    auto* source_view = GTK_SOURCE_VIEW(
        gtk_builder_get_object(builder->gobj(), "workbench_source_view"));
    auto* result_view =
        builder->get_widget<Gtk::TextView>("workbench_result_view");
    auto* run_button =
        builder->get_widget<Gtk::Button>("workbench_run_button");
    auto* spinner = builder->get_widget<Gtk::Spinner>(
        "workbench_experiment_spinner");
    auto* status_label = builder->get_widget<Gtk::Label>(
        "workbench_experiment_status_label");
    auto* experiment_title = builder->get_widget<Gtk::Label>(
        "workbench_experiment_title_label");
    auto* experiment_objective = builder->get_widget<Gtk::Label>(
        "workbench_experiment_objective_label");
    m_experiment_count_label = builder->get_widget<Gtk::Label>(
        "workbench_experiment_count_label");
    m_dock_panel =
        builder->get_widget<Gtk::Box>("workbench_dock_panel");
    auto* collapse_button =
        builder->get_widget<Gtk::Button>("workbench_collapse_button");
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

    m_experiment_dock = make_unique<ExperimentDock>(
        content_loader,
        experiment_runner,
        source_view,
        result_view,
        run_button,
        spinner,
        status_label,
        experiment_title,
        experiment_objective);

    for (const auto& subchapter : chapter.subchapters) {
        m_topic_by_function_id[subchapter.function_id] = &subchapter;
    }
    if (m_dock_panel) {
        m_dock_panel->set_visible(false);
    }
    if (collapse_button) {
        collapse_button->signal_clicked().connect([this]() {
            if (m_dock_panel) {
                m_dock_panel->set_visible(false);
            }
        });
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

    const string markdown = m_content_loader.load_document(document);
    if (markdown.empty()) {
        cerr << "Failed to load workbench document: " << document << endl;
        return;
    }

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
    if (m_dock_panel) {
        m_dock_panel->set_visible(true);
    }
    m_experiment_dock->select(
        {.function_id = subchapter.function_id,
         .title = subchapter.title,
         .description = subchapter.description,
         .source_path = subchapter.source,
         .member_name = subchapter.name});
    update_section_position(subchapter);
}

void WorkbenchPage::update_section_position(const SubChapter& selected) {
    if (!m_experiment_count_label || !selected.teaches) {
        return;
    }

    vector<const SubChapter*> section_experiments;
    for (const auto& subchapter : m_chapter.subchapters) {
        if (subchapter.teaches &&
            subchapter.teaches->document == selected.teaches->document &&
            subchapter.teaches->heading == selected.teaches->heading) {
            section_experiments.push_back(&subchapter);
        }
    }
    const auto current = find(
        section_experiments.begin(), section_experiments.end(), &selected);
    const size_t index = current == section_experiments.end()
        ? 1
        : static_cast<size_t>(distance(section_experiments.begin(), current)) + 1;
    m_experiment_count_label->set_text(
        "本节实验 " + to_string(index) + " / " +
        to_string(section_experiments.size()));
}
