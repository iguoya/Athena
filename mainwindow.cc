#include "mainwindow.h"
#include "markdown_renderer.h"

#include <gio/gio.h>
#include <gtksourceview/gtksource.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>

using namespace std;

namespace {

using json = nlohmann::json;

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

IconSpec parse_icon(const json& value, const IconSpec& fallback = {}) {
    if (!value.is_object()) {
        return fallback;
    }

    IconSpec icon;
    icon.type = value.value("type", "");
    icon.name = value.value("name", "");
    icon.path = value.value("path", "");
    return icon;
}

string file_stem(const string& path) {
    auto slash = path.find_last_of('/');
    auto filename = slash == string::npos ? path : path.substr(slash + 1);
    auto dot = filename.find_last_of('.');
    return dot == string::npos ? filename : filename.substr(0, dot);
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
      m_main_builder(builder) {
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
        "/app/data/chapters.json",
        G_RESOURCE_LOOKUP_FLAGS_NONE,
        nullptr);

    if (!bytes) {
        throw runtime_error("chapters.json not found in GResource");
    }

    gsize size = 0;
    const char* data = static_cast<const char*>(g_bytes_get_data(bytes, &size));

    json config;
    try {
        config = json::parse(string_view(data, size));
    } catch (...) {
        g_bytes_unref(bytes);
        throw;
    }
    g_bytes_unref(bytes);

    if (config.value("schema", 0) != 1) {
        throw runtime_error("Unsupported chapters.json schema");
    }

    const auto& defaults = config.at("defaults");
    m_default_chapter_content = defaults.value("content", "code");
    const auto& chapter_ui = defaults.at("chapter_ui");
    m_default_code_chapter_blueprint =
        chapter_ui.at("code").at("blueprint").get<string>();
    m_default_article_chapter_blueprint =
        chapter_ui.at("article").at("blueprint").get<string>();
    m_default_chapter_icon = parse_icon(defaults.value("chapter_icon", json::object()));
    m_default_subchapter_icon =
        parse_icon(defaults.value("subchapter_icon", json::object()));

    for (const auto& category_value : config.at("categories")) {
        CategoryInfo category;
        category.name = category_value.at("name").get<string>();
        category.title = category_value.at("title").get<string>();
        category.description = category_value.at("description").get<string>();
        category.icon = parse_icon(
            category_value.value("icon", json::object()),
            m_default_chapter_icon);
        m_categories.push_back(category);

        auto& chapters = m_chapters[category.name];
        for (const auto& chapter_value : category_value.at("chapters")) {
            ChapterMeta chapter;
            chapter.name = chapter_value.at("name").get<string>();
            chapter.title = chapter_value.at("title").get<string>();
            chapter.description = chapter_value.at("description").get<string>();
            chapter.category = category.name;
            chapter.content = chapter_value.value(
                "content",
                m_default_chapter_content);
            if (chapter.content != "code" && chapter.content != "article") {
                throw runtime_error(
                    "Unsupported chapter content type for " + category.name + "." +
                    chapter.name + ": " + chapter.content);
            }
            chapter.document = chapter_value.value("document", "");
            chapter.source = chapter_value.value("source", "");
            chapter.icon = parse_icon(
                chapter_value.value("icon", json::object()),
                m_default_chapter_icon);

            chapter.blueprint = chapter.content == "article"
                ? m_default_article_chapter_blueprint
                : m_default_code_chapter_blueprint;
            if (chapter_value.contains("ui")) {
                chapter.blueprint = chapter_value.at("ui").value(
                    "blueprint",
                    chapter.blueprint);
            } else if (chapter.content == "article" && chapter.document.empty()) {
                throw runtime_error(
                    "Article chapter requires document: " + category.name + "." +
                    chapter.name);
            }

            const string stem = file_stem(chapter.blueprint);
            chapter.resource_path = "/app/chapters/" + stem + ".ui";
            if (chapter.blueprint == m_default_code_chapter_blueprint) {
                chapter.widget_name = "chapter_page";
            } else if (chapter.blueprint == m_default_article_chapter_blueprint) {
                chapter.widget_name = "article_page";
            } else {
                chapter.widget_name = stem + "_page";
            }

            for (const auto& group_value :
                 chapter_value.value("groups", json::array())) {
                ChapterGroup group;
                group.name = group_value.at("name").get<string>();
                group.title = group_value.at("title").get<string>();
                group.description = group_value.at("description").get<string>();
                group.source = group_value.value("source", "");
                group.icon = parse_icon(
                    group_value.value("icon", json::object()),
                    chapter.icon);
                chapter.groups.push_back(group);
            }

            for (const auto& subchapter_value : chapter_value.at("subchapters")) {
                SubChapter subchapter;
                subchapter.name = subchapter_value.at("name").get<string>();
                subchapter.title = subchapter_value.at("title").get<string>();
                subchapter.description =
                    subchapter_value.at("description").get<string>();
                subchapter.group = subchapter_value.value("group", "");
                subchapter.source = subchapter_value.value("source", "");
                subchapter.icon = parse_icon(
                    subchapter_value.value("icon", json::object()),
                    m_default_subchapter_icon);
                chapter.subchapters.push_back(subchapter);
            }

            cout << "Chapter loaded: " << category.name << "::" << chapter.name
                 << " -> \"" << chapter.title << "\"" << endl;
            chapters.push_back(chapter);
        }
    }

    size_t chapter_count = 0;
    for (const auto& [category_name, chapters] : m_chapters) {
        chapter_count += chapters.size();
    }
    cout << "Loaded " << m_categories.size() << " categories and "
         << chapter_count << " chapters from chapters.json" << endl;
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
    for (const auto& category : m_categories) {
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

    auto category = m_chapters.find(category_name);
    if (category == m_chapters.end() || category->second.empty()) {
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
            auto article_view = builder->get_widget<Gtk::TextView>("article_view");
            auto toc_box = builder->get_widget<Gtk::Box>("article_toc_box");
            auto toc_scroll =
                builder->get_widget<Gtk::ScrolledWindow>("article_toc_scroll");

            if (!article_view || !toc_box) {
                cerr << "Article page is missing required widgets for "
                     << page_key << endl;
                continue;
            }

            const string markdown = read_project_document(chapter.document);
            if (markdown.empty()) {
                article_view->get_buffer()->set_text(
                    "无法载入文章：" + chapter.document);
                cerr << "Failed to load article document for " << page_key
                     << ": " << chapter.document << endl;
            } else {
                try {
                    const auto headings = render_markdown(*article_view, markdown);
                    for (const auto& heading : headings) {
                        if (heading.level > 3) {
                            continue;
                        }

                        auto button = Gtk::make_managed<Gtk::Button>();
                        button->add_css_class("article-toc-button");
                        button->set_focusable(false);
                        button->set_margin_start(
                            static_cast<int>((heading.level - 1) * 16));

                        auto label = Gtk::make_managed<Gtk::Label>(heading.title);
                        label->set_halign(Gtk::Align::START);
                        label->set_xalign(0);
                        label->set_wrap(true);
                        button->set_child(*label);

                        button->signal_clicked().connect(
                            [article_view, offset = heading.text_offset]() {
                                auto buffer = article_view->get_buffer();
                                auto position = buffer->get_iter_at_offset(offset);
                                buffer->place_cursor(position);
                                article_view->scroll_to(position, 0.08, 0.0, 0.0);
                            });
                        toc_box->append(*button);
                    }

                    if (toc_scroll) {
                        auto adjustment = toc_scroll->get_vadjustment();
                        adjustment->set_value(adjustment->get_lower());
                    }
                } catch (const exception& error) {
                    article_view->get_buffer()->set_text(
                        string("Markdown 解析失败：") + error.what());
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
            result_buffer->set_text(
                "章节类与运行按钮的映射尚未接入。\n"
                "当前阶段只验证课程结构与界面展示。");
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
                    run->set_sensitive(false);
                    run->set_tooltip_text("章节类映射将在后续阶段接入");
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

const ChapterMeta* MainWindow::find_chapter(
    const string& category_name,
    const string& chapter_name) const {
    auto category = m_chapters.find(category_name);
    if (category == m_chapters.end()) {
        return nullptr;
    }

    auto chapter = find_if(
        category->second.begin(),
        category->second.end(),
        [&chapter_name](const ChapterMeta& value) {
            return value.name == chapter_name;
        });
    return chapter == category->second.end() ? nullptr : &*chapter;
}

Glib::RefPtr<Gtk::Builder> MainWindow::get_chapter_builder(
    const string& category_name,
    const string& chapter_name) {
    const string key = chapter_key(category_name, chapter_name);
    if (auto cached = m_chapter_builders.find(key);
        cached != m_chapter_builders.end()) {
        return cached->second;
    }

    const auto* chapter = find_chapter(category_name, chapter_name);
    if (!chapter) {
        cerr << "Chapter not found: " << key << endl;
        return {};
    }

    auto builder = Gtk::Builder::create_from_resource(chapter->resource_path);
    m_chapter_builders[key] = builder;
    return builder;
}
