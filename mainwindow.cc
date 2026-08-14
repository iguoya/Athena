#include "mainwindow.h"
#include "render/markdown_renderer.h"

#include <gio/gio.h>
#include <gtksourceview/gtksource.h>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>

using namespace std;

namespace {

string read_file(const string& path) {
    ifstream file(path);
    if (!file) {
        return {};
    }

    ostringstream content;
    content << file.rdbuf();
    return content.str();
}

string read_resource_file(const string& resource_path) {
    GError* error = nullptr;
    GBytes* bytes = g_resources_lookup_data(
        resource_path.c_str(),
        G_RESOURCE_LOOKUP_FLAGS_NONE,
        &error);
    if (!bytes) {
        if (error) {
            g_error_free(error);
        }
        return {};
    }

    gsize size = 0;
    const char* data = static_cast<const char*>(g_bytes_get_data(bytes, &size));
    string content(data, size);
    g_bytes_unref(bytes);
    return content;
}

string read_project_document(const string& path) {
    constexpr string_view resources_prefix = "resources/";
    if (path.rfind(resources_prefix, 0) == 0) {
        const string resource_path =
            "/app/" + path.substr(resources_prefix.size());
        if (string content = read_resource_file(resource_path); !content.empty()) {
            return content;
        }
    }

    return read_file(string(ATHENA_SOURCE_ROOT) + "/" + path);
}

string project_document_directory(const string& path) {
    const size_t slash = path.find_last_of('/');
    const string directory = slash == string::npos ? "" : path.substr(0, slash);
    return string(ATHENA_SOURCE_ROOT) + "/" + directory;
}

string chapter_key(const string& category_name, const string& chapter_name) {
    return category_name + "." + chapter_name;
}

const ChapterGroup* find_group(const ChapterMeta& chapter, const string& name) {
    auto found = find_if(
        chapter.groups.begin(),
        chapter.groups.end(),
        [&name](const ChapterGroup& group) { return group.name == name; });
    return found == chapter.groups.end() ? nullptr : &*found;
}

} // namespace

MainWindow::MainWindow(
    BaseObjectType* cobject,
    const Glib::RefPtr<Gtk::Builder>& builder)
    : Gtk::ApplicationWindow(cobject),
      m_main_builder(builder),
      m_function_registry(create_default_function_registry()) {
    maximize();

    auto css = Gtk::CssProvider::create();
    css->load_from_resource("/app/style.css");
    Gtk::StyleContext::add_provider_for_display(
        get_display(),
        css,
        GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

    m_category_sidebar = m_main_builder->get_widget<Gtk::Box>("category_sidebar");
    m_chapter_stack = m_main_builder->get_widget<Gtk::Stack>("chapter_stack");
    m_chapter_tab_box = m_main_builder->get_widget<Gtk::FlowBox>("chapter_tab_box");

    if (!m_category_sidebar || !m_chapter_stack || !m_chapter_tab_box) {
        throw runtime_error("Failed to get required widgets from main UI");
    }

    load_chapter_metadata();
    setup_category_sidebar();

    cout << "MainWindow initialized successfully" << endl;
}

void MainWindow::load_chapter_metadata() {
    GBytes* bytes = g_resources_lookup_data(
        "/app/data/athena.json",
        G_RESOURCE_LOOKUP_FLAGS_NONE,
        nullptr);

    if (!bytes) {
        throw runtime_error("athena.json not found in GResource");
    }

    gsize size = 0;
    const char* data = static_cast<const char*>(g_bytes_get_data(bytes, &size));

    const string source(data, size);
    g_bytes_unref(bytes);
    m_catalog = ChapterCatalog::from_json(source);
    cout << "Loaded " << m_catalog.categories().size() << " categories and "
         << m_catalog.chapter_count() << " chapters from athena.json" << endl;
}

void MainWindow::configure_image(
    Gtk::Image& image,
    const IconSpec& icon,
    int pixel_size) const {
    if (icon.type == "resource" && !icon.path.empty()) {
        string resource_path = icon.path;
        constexpr string_view resources_prefix = "resources/";
        if (resource_path.rfind(resources_prefix, 0) == 0) {
            resource_path = "/app/" + resource_path.substr(resources_prefix.size());
        }
        image.set_from_resource(resource_path);
    } else if (!icon.name.empty()) {
        image.set_from_icon_name(icon.name);
    } else {
        image.set_visible(false);
        return;
    }

    image.set_pixel_size(pixel_size);
}

Gtk::Image* MainWindow::create_icon(const IconSpec& icon, int pixel_size) const {
    auto image = Gtk::make_managed<Gtk::Image>();
    configure_image(*image, icon, pixel_size);
    return image;
}

void MainWindow::setup_category_sidebar() {
    for (const auto& category : m_catalog.categories()) {
        auto button = Gtk::make_managed<Gtk::ToggleButton>();
        button->add_css_class("nav-button");
        button->set_tooltip_text(category.description);

        auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
        box->set_valign(Gtk::Align::CENTER);
        box->set_margin_top(12);
        box->set_margin_bottom(12);

        box->append(*create_icon(category.icon, 24));

        auto label = Gtk::make_managed<Gtk::Label>(category.title);
        label->set_wrap(true);
        label->set_justify(Gtk::Justification::CENTER);
        label->set_max_width_chars(7);
        box->append(*label);
        button->set_child(*box);

        if (!m_category_buttons.empty()) {
            button->set_group(*m_category_buttons.front());
        }

        button->signal_toggled().connect(
            [this, category_name = category.name, button]() {
                if (button->get_active()) {
                    on_category_selected(category_name);
                }
            });

        m_category_sidebar->append(*button);
        m_category_buttons.push_back(button);
    }

    if (!m_category_buttons.empty()) {
        m_category_buttons.front()->set_active(true);
    }
}

void MainWindow::on_category_selected(const string& category_name) {
    if (category_name == m_current_category) {
        return;
    }

    m_current_category = category_name;
    build_chapter_tabs(category_name);
}

void MainWindow::build_chapter_tabs(const string& category_name) {
    for (const auto& name : m_active_page_names) {
        if (auto child = m_chapter_stack->get_child_by_name(name)) {
            m_chapter_stack->remove(*child);
        }
    }
    m_active_page_names.clear();

    for (auto* button : m_tab_buttons) {
        m_chapter_tab_box->remove(*button);
    }
    m_tab_buttons.clear();

    const auto& all_chapters = m_catalog.chapters();
    auto category = all_chapters.find(category_name);
    if (category == all_chapters.end() || category->second.empty()) {
        auto placeholder = Gtk::make_managed<Gtk::Label>("该分类暂无章节");
        placeholder->set_halign(Gtk::Align::CENTER);
        placeholder->set_valign(Gtk::Align::CENTER);
        const string empty_key = category_name + ".__empty__";
        m_chapter_stack->add(*placeholder, empty_key, "空");
        m_active_page_names.insert(empty_key);
        return;
    }

    for (const auto& chapter : category->second) {
        const string page_key = chapter_key(category_name, chapter.name);
        auto builder = get_chapter_builder(category_name, chapter.name);
        if (!builder) {
            cerr << "Failed to create builder for " << page_key << endl;
            continue;
        }

        auto widget = builder->get_widget<Gtk::Widget>(chapter.widget_name);
        if (!widget) {
            cerr << "Failed to get root widget '" << chapter.widget_name
                 << "' for " << page_key << endl;
            continue;
        }

        m_chapter_stack->add(*widget, page_key, chapter.title);
        m_active_page_names.insert(page_key);

        auto tab_button = Gtk::make_managed<Gtk::ToggleButton>();
        tab_button->add_css_class("pill");
        tab_button->add_css_class("chapter-tab");
        tab_button->set_tooltip_text(chapter.description);

        auto tab_content = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
        tab_content->append(*create_icon(chapter.icon, 16));
        tab_content->append(*Gtk::make_managed<Gtk::Label>(chapter.title));
        tab_button->set_child(*tab_content);

        if (!m_tab_buttons.empty()) {
            tab_button->set_group(*m_tab_buttons.front());
        }

        tab_button->signal_toggled().connect(
            [this, page_key, tab_button, widget]() {
                if (tab_button->get_active()) {
                    m_chapter_stack->set_visible_child(*widget);
                    m_current_chapter = page_key;
                }
            });

        m_chapter_tab_box->append(*tab_button);
        m_tab_buttons.push_back(tab_button);

        if (m_loaded_chapters.find(page_key) != m_loaded_chapters.end()) {
            continue;
        }

        const bool uses_article_page = chapter.widget_name == "article_page";
        if (uses_article_page) {
            auto article_web_host =
                builder->get_widget<Gtk::DrawingArea>("article_web_host");

            if (!article_web_host) {
                cerr << "Article page is missing its WebView host for "
                     << page_key << endl;
                continue;
            }

            const string markdown = read_project_document(chapter.document);
            if (markdown.empty()) {
                cerr << "Failed to load article document for " << page_key
                     << ": " << chapter.document << endl;
            } else {
                try {
                    const auto headings = parse_markdown_headings(markdown);
                    const string stylesheet = read_resource_file("/app/article.css");
                    if (stylesheet.empty()) {
                        throw runtime_error("Article stylesheet is unavailable");
                    }

                    auto view = athena::create_platform_article_view(
                        *article_web_host,
                        *this);
                    if (!view) {
                        throw runtime_error("No WebView backend is available");
                    }
                    view->load_html(
                        render_markdown_html(markdown, stylesheet, headings),
                        project_document_directory(chapter.document));
                    m_article_views[page_key] = std::move(view);
                } catch (const exception& error) {
                    cerr << "Failed to render article for " << page_key
                         << ": " << error.what() << endl;
                }
            }

            m_loaded_chapters.insert(page_key);
            continue;
        }

        const bool uses_code_page = chapter.widget_name == "chapter_page";
        if (!uses_code_page) {
            continue;
        }

        auto title_label = builder->get_widget<Gtk::Label>("chapter_title_label");
        auto description_label =
            builder->get_widget<Gtk::Label>("chapter_description_label");
        auto chapter_icon = builder->get_widget<Gtk::Image>("chapter_icon");
        auto source_view = GTK_SOURCE_VIEW(
            gtk_builder_get_object(builder->gobj(), "source_view"));
        auto run_button = builder->get_widget<Gtk::Button>("run_button");
        auto result_view = builder->get_widget<Gtk::TextView>("result_view");
        auto topics_label = builder->get_widget<Gtk::Label>("topics_label");
        auto topics_list = builder->get_widget<Gtk::ListBox>("topics_list");
        auto knowledge_description_label =
            builder->get_widget<Gtk::Label>("knowledge_description_label");

        if (title_label) {
            title_label->set_text(chapter.title);
        }
        if (description_label) {
            description_label->set_text(chapter.description);
        }
        if (chapter_icon) {
            configure_image(*chapter_icon, chapter.icon, 36);
        }
        if (run_button) {
            run_button->set_visible(false);
        }

        if (source_view) {
            string source_text;
            if (!chapter.source.empty()) {
                source_text = read_file(string(ATHENA_SOURCE_ROOT) + "/" + chapter.source);
            }
            if (source_text.empty()) {
                source_text = "该章节尚未添加实验源码。";
            }

            auto source_buffer = GTK_SOURCE_BUFFER(
                gtk_text_view_get_buffer(GTK_TEXT_VIEW(source_view)));
            auto language_manager = gtk_source_language_manager_get_default();
            auto cpp_language = gtk_source_language_manager_get_language(
                language_manager,
                "cpp");
            if (cpp_language) {
                gtk_source_buffer_set_language(source_buffer, cpp_language);
            }
            gtk_source_buffer_set_highlight_syntax(source_buffer, true);
            gtk_source_buffer_set_highlight_matching_brackets(source_buffer, true);

            auto scheme_manager = gtk_source_style_scheme_manager_get_default();
            auto scheme = gtk_source_style_scheme_manager_get_scheme(
                scheme_manager,
                "Adwaita");
            if (scheme) {
                gtk_source_buffer_set_style_scheme(source_buffer, scheme);
            }

            auto text_buffer = GTK_TEXT_BUFFER(source_buffer);
            gtk_text_buffer_set_text(
                text_buffer,
                source_text.c_str(),
                static_cast<int>(source_text.size()));
            GtkTextIter source_begin;
            gtk_text_buffer_get_start_iter(text_buffer, &source_begin);
            gtk_text_buffer_place_cursor(text_buffer, &source_begin);
        }

        if (result_view) {
            auto result_buffer = result_view->get_buffer();
            result_buffer->set_text("请选择知识点并点击“运行”查看实验结果。");
            auto result_begin = result_buffer->begin();
            result_buffer->place_cursor(result_begin);
        }

        if (topics_label && topics_list) {
            if (chapter.subchapters.empty()) {
                auto row = Gtk::make_managed<Gtk::ListBoxRow>();
                row->set_selectable(false);
                row->set_activatable(false);

                auto label = Gtk::make_managed<Gtk::Label>("知识点框架待补充");
                label->set_halign(Gtk::Align::START);
                label->add_css_class("dim-label");
                label->set_margin_top(12);
                label->set_margin_bottom(12);
                label->set_margin_start(12);
                label->set_margin_end(12);
                row->set_child(*label);
                topics_list->append(*row);

                if (knowledge_description_label) {
                    knowledge_description_label->set_text(chapter.description);
                }
            } else {
                auto description_by_row =
                    make_shared<std::map<Gtk::ListBoxRow*, string>>();
                Gtk::ListBoxRow* first_topic_row = nullptr;
                string current_group;
                for (const auto& subchapter : chapter.subchapters) {
                    if (!subchapter.group.empty() && subchapter.group != current_group) {
                        current_group = subchapter.group;
                        if (const auto* group = find_group(chapter, current_group)) {
                            auto header = Gtk::make_managed<Gtk::ListBoxRow>();
                            header->set_selectable(false);
                            header->set_activatable(false);
                            header->add_css_class("topic-group");

                            auto header_box = Gtk::make_managed<Gtk::Box>(
                                Gtk::Orientation::HORIZONTAL,
                                10);
                            header_box->set_margin_top(12);
                            header_box->set_margin_bottom(4);
                            header_box->append(*create_icon(group->icon, 18));

                            auto text_box = Gtk::make_managed<Gtk::Box>(
                                Gtk::Orientation::VERTICAL,
                                2);
                            text_box->set_hexpand(true);

                            auto group_title = Gtk::make_managed<Gtk::Label>(group->title);
                            group_title->set_halign(Gtk::Align::START);
                            group_title->add_css_class("heading");
                            text_box->append(*group_title);

                            auto group_description =
                                Gtk::make_managed<Gtk::Label>(group->description);
                            group_description->set_halign(Gtk::Align::START);
                            group_description->set_xalign(0);
                            group_description->set_wrap(true);
                            group_description->add_css_class("dim-label");
                            text_box->append(*group_description);

                            header_box->append(*text_box);
                            header->set_child(*header_box);
                            topics_list->append(*header);
                        }
                    }

                    auto row = Gtk::make_managed<Gtk::ListBoxRow>();
                    row->set_selectable(true);
                    row->set_activatable(true);
                    row->add_css_class("topic-row");

                    (*description_by_row)[row] = subchapter.description;
                    if (!first_topic_row) {
                        first_topic_row = row;
                    }

                    auto row_box = Gtk::make_managed<Gtk::Box>(
                        Gtk::Orientation::HORIZONTAL,
                        12);
                    row_box->append(*create_icon(subchapter.icon, 20));

                    auto text_box = Gtk::make_managed<Gtk::Box>(
                        Gtk::Orientation::VERTICAL,
                        4);
                    text_box->set_hexpand(true);

                    auto point_title = Gtk::make_managed<Gtk::Label>(subchapter.title);
                    point_title->set_halign(Gtk::Align::START);
                    point_title->add_css_class("heading");
                    text_box->append(*point_title);

                    auto point_description =
                        Gtk::make_managed<Gtk::Label>(subchapter.description);
                    point_description->set_halign(Gtk::Align::START);
                    point_description->set_xalign(0);
                    point_description->set_wrap(true);
                    point_description->add_css_class("dim-label");
                    text_box->append(*point_description);

                    row_box->append(*text_box);

                    auto run = Gtk::make_managed<Gtk::Button>("运行");
                    run->add_css_class("suggested-action");
                    run->add_css_class("btn-primary");
                    run->add_css_class("btn-sm");
                    run->add_css_class("topic-run");
                    const string function_id = make_function_id(
                        category_name,
                        chapter.name,
                        subchapter.name);
                    const bool can_run = m_function_registry.contains(function_id);
                    run->set_sensitive(can_run);
                    run->set_tooltip_text(can_run
                        ? "运行该知识点的实验代码"
                        : "该知识点尚未实现可运行实验");
                    if (can_run && result_view) {
                        run->signal_clicked().connect(
                            [this, function_id, result_view]() {
                                ostringstream output;
                                try {
                                    m_function_registry.run(function_id, output);
                                    result_view->get_buffer()->set_text(output.str());
                                } catch (const exception& error) {
                                    result_view->get_buffer()->set_text(
                                        "运行失败：" + string(error.what()));
                                }
                            });
                    }
                    row_box->append(*run);

                    row->set_child(*row_box);
                    topics_list->append(*row);
                }

                if (knowledge_description_label) {
                    topics_list->signal_row_selected().connect(
                        [description_by_row,
                         knowledge_description_label](Gtk::ListBoxRow* row) {
                            auto found = description_by_row->find(row);
                            if (found == description_by_row->end()) {
                                return;
                            }

                            knowledge_description_label->set_text(found->second);
                        });

                    if (first_topic_row) {
                        topics_list->select_row(*first_topic_row);
                    }
                }
            }
        }

        m_loaded_chapters.insert(page_key);
    }

    if (!m_tab_buttons.empty()) {
        m_tab_buttons.front()->set_active(true);
    }
}

Glib::RefPtr<Gtk::Builder> MainWindow::get_chapter_builder(
    const string& category_name,
    const string& chapter_name) {
    const string key = chapter_key(category_name, chapter_name);
    if (auto cached = m_chapter_builders.find(key);
        cached != m_chapter_builders.end()) {
        return cached->second;
    }

    const auto* chapter = m_catalog.find_chapter(category_name, chapter_name);
    if (!chapter) {
        cerr << "Chapter not found: " << key << endl;
        return {};
    }

    auto builder = Gtk::Builder::create_from_resource(chapter->resource_path);
    m_chapter_builders[key] = builder;
    return builder;
}
