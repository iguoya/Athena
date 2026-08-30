#include "workbench_page.h"

#include "render/markdown_renderer.h"
#include "ui/icon_utils.h"
#include "ui/markdown_fallback.h"
#include "ui/source_view.h"

#include <iostream>
#include <utility>

using namespace std;

WorkbenchPage::WorkbenchPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    ExperimentRunner& experiment_runner,
    Gtk::Window& parent)
    : m_chapter(chapter),
      m_content_loader(content_loader),
      m_experiment_runner(experiment_runner) {
    auto* title_label =
        builder->get_widget<Gtk::Label>("workbench_chapter_title_label");
    auto* description_label =
        builder->get_widget<Gtk::Label>("workbench_chapter_description_label");
    auto* icon = builder->get_widget<Gtk::Image>("workbench_chapter_icon");
    m_source_view = GTK_SOURCE_VIEW(
        gtk_builder_get_object(builder->gobj(), "workbench_source_view"));
    m_topics_list = builder->get_widget<Gtk::ListBox>("workbench_topics_list");
    m_run_button = builder->get_widget<Gtk::Button>("workbench_run_button");
    m_result_view = builder->get_widget<Gtk::TextView>("workbench_result_view");
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
    load_article();

    if (m_result_view) {
        m_result_view->get_buffer()->set_text(
            "点击右侧知识点即可运行实验并在此查看结果，文档也会跟着滚到对应小节。");
    }
    if (m_run_button) {
        m_run_button->set_sensitive(false);
        m_run_button->signal_clicked().connect(
            [this]() { run_current_experiment(); });
    }
    if (m_topics_list) {
        populate_topic_list();
    }
}

WorkbenchPage::~WorkbenchPage() {
    m_alive->store(false);
}

void WorkbenchPage::load_article() {
    const string& document = m_chapter.overview_document;
    if (document.empty()) {
        cerr << "Workbench chapter " << m_chapter.name
             << " has no overview_document to render as its handbook pane"
             << endl;
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
    for (const auto& heading : headings) {
        m_anchor_by_heading[heading.title] = heading.anchor;
    }

    if (!m_article_view) {
        // 尚未实现 WebView 后端的平台退回纯文本显示，避免留白；这类平台上
        // 知识点列表点击不会有滚动联动，"动手验证"卡片也不会出现（卡片
        // 本身是渲染期插入到 HTML 里的，纯文本回退不经过这条渲染路径），
        // 只影响双向联动，不影响运行实验本身。
        return;
    }

    // 渲染期挂载：只给"这份文档 + 这一节标题"确实对应到某个知识点的
    // 小节插卡片，不要求每章都补齐——见 docs/LEARNING_WORKSPACE_BENCH.md
    // 「有文档无实验是正常态，只统计孤儿实验」。
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
        [this](const string& knowledge_id) { select_by_knowledge_id(knowledge_id); });

    try {
        const string stylesheet = m_content_loader.load_resource("/app/article.css");
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

void WorkbenchPage::populate_topic_list() {
    if (m_chapter.subchapters.empty()) {
        auto row = Gtk::make_managed<Gtk::ListBoxRow>();
        row->set_selectable(false);
        row->set_activatable(false);
        auto label = Gtk::make_managed<Gtk::Label>("知识点框架待补充");
        label->set_halign(Gtk::Align::START);
        label->add_css_class("dim-label");
        label->set_margin(12);
        row->set_child(*label);
        m_topics_list->append(*row);
        return;
    }

    // 知识点数量不多，直接按行指针查表，不引入额外的 ID 间接层。同一份
    // 表也供文档里"动手验证"卡片点击时反查（select_by_knowledge_id），
    // 是双向联动共用的唯一数据源。
    Gtk::ListBoxRow* first_row = nullptr;
    for (const auto& subchapter : m_chapter.subchapters) {
        auto row = Gtk::make_managed<Gtk::ListBoxRow>();
        row->add_css_class("topic-row");

        auto content = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 10);
        content->set_margin_top(8);
        content->set_margin_bottom(8);
        content->set_margin_start(10);
        content->set_margin_end(10);
        content->append(*make_icon_image(subchapter.icon, 18));

        auto title = Gtk::make_managed<Gtk::Label>(subchapter.title);
        title->set_halign(Gtk::Align::START);
        title->set_hexpand(true);
        content->append(*title);
        row->set_child(*content);

        m_topic_by_function_id[subchapter.function_id] = {row, &subchapter};
        m_topics_list->append(*row);
        if (!first_row) {
            first_row = row;
        }
    }

    m_topics_list->signal_row_activated().connect([this](Gtk::ListBoxRow* row) {
        for (const auto& [function_id, entry] : m_topic_by_function_id) {
            if (entry.first == row) {
                select_subchapter(*row, *entry.second);
                return;
            }
        }
    });

    if (first_row) {
        select_subchapter(
            *first_row, m_chapter.subchapters.front(), /*scroll_source_view=*/false);
    }
}

void WorkbenchPage::select_subchapter(
    Gtk::ListBoxRow& row, const SubChapter& subchapter, bool scroll_source_view) {
    if (m_active_row) {
        m_active_row->remove_css_class("topic-active");
    }
    row.add_css_class("topic-active");
    m_active_row = &row;

    m_current_function_id = subchapter.function_id;
    m_current_source_path = subchapter.source;
    m_current_member_name = subchapter.name;

    // 构造期间的初始自动选中不跳转源码：这一刻页面刚被切进 Stack，控件树
    // 大概率还没经过第一次真实布局分配，此时定位没有意义。跳转本身的
    // "GtkTextView 行高懒验证"问题已经在 display_project_source 里用
    // 调用两次 scroll_to_mark 解决，这里不需要再额外处理。
    display_project_source(
        m_source_view,
        m_content_loader,
        subchapter.source,
        scroll_source_view ? subchapter.name : "");

    if (m_run_button) {
        m_run_button->set_sensitive(true);
    }
    if (m_result_view) {
        m_result_view->get_buffer()->set_text("尚未运行。");
    }

    if (subchapter.teaches && m_article_view) {
        const auto anchor = m_anchor_by_heading.find(subchapter.teaches->heading);
        if (anchor != m_anchor_by_heading.end()) {
            m_article_view->scroll_to_anchor(anchor->second);
        } else {
            // 标题文本对不上：文档可能被重新措辞过，athena.json 里的
            // teaches.heading 没有同步更新。不阻断，只是这次不跳转。
            cerr << "Workbench: teaches.heading not found in "
                 << m_chapter.overview_document << ": '"
                 << subchapter.teaches->heading << "'" << endl;
        }
    }
}

void WorkbenchPage::select_by_knowledge_id(const string& knowledge_id) {
    const auto found = m_topic_by_function_id.find(knowledge_id);
    if (found == m_topic_by_function_id.end()) {
        // 文档里的卡片和知识点数据来自同一次渲染，正常不会找不到；出现
        // 这种情况多半是知识点在别处被改了 function_id，值得留个痕迹。
        cerr << "Workbench: no subchapter for knowledge id '" << knowledge_id
             << "'" << endl;
        return;
    }
    select_subchapter(*found->second.first, *found->second.second);
}

void WorkbenchPage::run_current_experiment() {
    if (m_current_function_id.empty()) {
        return;
    }
    auto alive = m_alive;
    const bool started = m_experiment_runner.start(
        {.function_id = m_current_function_id,
         .source_path = m_current_source_path,
         .member_name = m_current_member_name},
        [this, alive](const ExperimentResult& result) {
            if (!alive->load()) {
                return;
            }
            if (m_result_view) {
                m_result_view->get_buffer()->set_text(result.display_output);
            }
            if (m_run_button) {
                m_run_button->set_sensitive(true);
            }
        });
    if (!started) {
        return;
    }
    if (m_result_view) {
        m_result_view->get_buffer()->set_text("运行中…");
    }
    if (m_run_button) {
        m_run_button->set_sensitive(false);
    }
}
