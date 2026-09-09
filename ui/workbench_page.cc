#include "workbench_page.h"

#include "ui/icon_utils.h"

#include <algorithm>
#include <iostream>
#include <utility>
#include <vector>

using namespace std;

namespace {

string inline_text(const vector<DocInline>& inlines) {
    string text;
    for (const auto& item : inlines) {
        text += item.text;
        text += inline_text(item.children);
    }
    return text;
}

string tab_title(const string& heading) {
    const size_t space = heading.find(' ');
    return space == string::npos ? heading : heading.substr(space + 1);
}

struct DocumentSection {
    string title;
    string heading;
    vector<DocBlock> blocks;
};

vector<DocumentSection> split_document_sections(const DocModel& document) {
    vector<DocumentSection> sections;
    DocumentSection current{.title = "概览", .heading = ""};
    for (const auto& block : document.blocks) {
        if (block.kind == DocBlockKind::Heading && block.level == 2) {
            if (!current.blocks.empty()) {
                sections.push_back(std::move(current));
            }
            const string heading = inline_text(block.inlines);
            current = {.title = tab_title(heading), .heading = heading};
        }
        current.blocks.push_back(block);
    }
    if (!current.blocks.empty()) {
        sections.push_back(std::move(current));
    }
    return sections;
}

string importance_stars(int importance) {
    string stars;
    for (int index = 0; index < importance; ++index) {
        stars += "★";
    }
    return stars;
}

Gtk::Widget* make_section_tab(
    const DocumentSection& section,
    const vector<const SubChapter*>& topics) {
    auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 5);
    row->set_tooltip_text(section.title);
    auto title = Gtk::make_managed<Gtk::Label>(section.title);
    row->append(*title);
    if (topics.empty()) {
        return row;
    }

    int max_importance = 0;
    string tooltip = section.title + "：";
    for (size_t index = 0; index < topics.size(); ++index) {
        const auto& topic = *topics[index];
        max_importance = max(max_importance, topic.importance);
        if (index != 0) {
            tooltip += "；";
        }
        tooltip += topic.title + " " + importance_stars(topic.importance);
    }
    if (max_importance > 0) {
        auto stars = Gtk::make_managed<Gtk::Label>(
            importance_stars(max_importance));
        stars->add_css_class(
            "workbench-tab-importance-" + to_string(max_importance));
        row->append(*stars);
    }
    row->set_tooltip_text(tooltip);
    return row;
}

} // namespace

WorkbenchPage::WorkbenchPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    Gtk::Window&,
    function<void(const ExperimentSelection&, bool)> on_experiment_requested)
    : m_chapter(chapter),
      m_content_loader(content_loader),
      m_on_experiment_requested(std::move(on_experiment_requested)) {
    auto* title_label =
        builder->get_widget<Gtk::Label>("workbench_chapter_title_label");
    auto* description_label = builder->get_widget<Gtk::Label>(
        "workbench_chapter_description_label");
    auto* icon = builder->get_widget<Gtk::Image>("workbench_chapter_icon");
    m_section_notebook =
        builder->get_widget<Gtk::Notebook>("workbench_section_notebook");

    if (title_label) {
        title_label->set_text(chapter.title);
    }
    if (description_label) {
        description_label->set_text(chapter.description);
    }
    if (icon) {
        configure_icon_image(*icon, chapter.icon, 34);
    }
    if (m_section_notebook) {
        const auto slash = chapter.overview_document.find_last_of('/');
        m_resource_base = slash == string::npos
            ? "/app/"
            : "/app/" + chapter.overview_document.substr(0, slash + 1);
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
    if (!m_section_notebook) {
        return;
    }

    map<string, vector<DocumentView::HeadingAction>> actions;
    map<string, vector<const SubChapter*>> topics_by_heading;
    for (const auto& subchapter : m_chapter.subchapters) {
        if (subchapter.teaches && subchapter.teaches->document == document) {
            actions[subchapter.teaches->heading].push_back(
                {.label = "运行「" + subchapter.title + "」实验",
                 .activate = [this, knowledge_id = subchapter.function_id]() {
                     select_by_knowledge_id(knowledge_id);
                 }});
            topics_by_heading[subchapter.teaches->heading].push_back(&subchapter);
        }
    }
    map<string, vector<DocumentView::SectionExtension>> section_extensions;
    m_learning_units.clear();
    for (const auto& unit : m_chapter.learning_units) {
        const LearningUnit* unit_data = &unit;
        section_extensions[unit.heading].push_back([this, unit_data]() {
            auto unit_view = make_unique<LearningUnitView>(
                *unit_data,
                [this](const string& function_id) {
                    select_by_knowledge_id(function_id);
                });
            auto& widget = unit_view->widget();
            m_learning_units.push_back(std::move(unit_view));
            return &widget;
        });
    }
    try {
        while (auto* page = m_section_notebook->get_nth_page(0)) {
            m_section_notebook->remove_page(*page);
        }
        m_document_views.clear();
        const DocModel document = parse_document_blocks(raw);
        for (auto& section : split_document_sections(document)) {
            auto view = make_unique<DocumentView>(m_resource_base);
            view->set_heading_actions(actions);
            view->set_section_extensions(section_extensions);
            view->set_document({.blocks = std::move(section.blocks)});
            const auto related = topics_by_heading.find(section.heading);
            const vector<const SubChapter*> no_topics;
            auto* tab = make_section_tab(
                section,
                related == topics_by_heading.end() ? no_topics : related->second);
            m_section_notebook->append_page(view->widget(), *tab);
            m_document_views.push_back(std::move(view));
        }
    } catch (const exception& error) {
        cerr << "Failed to render GTK workbench document " << document << ": "
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
