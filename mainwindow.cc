#include "mainwindow.h"
#include <iostream>
#include <gio/gio.h>
#include <nlohmann/json.hpp>
#include <sstream>

using namespace std;

// ============================================================
// 章节演示类
// 每个章节对应一个类，run() 把结果输出到 ostream
// 按钮点击事件直接绑定这些类的 run() 成员函数
// ============================================================

// 02_pointers_references: 指针与引用 —— 值传递 vs 引用传递
class Functions06 {
public:
    void run(ostream& os) {
        int x = 5, y = 10;

        swapByValue(x, y);
        os << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << endl;

        swapByRef(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << endl;
    }

private:
    void swapByValue(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swapByRef(int& a, int& b) {
        int temp = a;
        a = b;
        b = temp;
    }
};

// 章节源码文本（源码框显示用）
static const char* FUNCTIONS06_SOURCE = R"SNIP(class Functions06 {
public:
    void run(ostream& os) {
        int x = 5, y = 10;

        swapByValue(x, y);
        os << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << endl;

        swapByRef(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << endl;
    }

private:
    void swapByValue(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swapByRef(int& a, int& b) {
        int temp = a;
        a = b;
        b = temp;
    }
};)SNIP";

// ===================================================================
//  构造 & 初始化
// ===================================================================

MainWindow::MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder)
    : Gtk::ApplicationWindow(cobject)
    , m_main_builder(builder)
{
    maximize();

    // 获取 UI 组件
    m_category_sidebar = m_main_builder->get_widget<Gtk::Box>("category_sidebar");
    m_chapter_stack    = m_main_builder->get_widget<Gtk::Stack>("chapter_stack");
    m_chapter_tab_box  = m_main_builder->get_widget<Gtk::FlowBox>("chapter_tab_box");

    if (!m_category_sidebar || !m_chapter_stack || !m_chapter_tab_box) {
        throw runtime_error("Failed to get required widgets from main UI");
    }

    // 运行时加载章节元数据
    load_chapter_metadata();

    // 构建左侧分类导航
    setup_category_sidebar();

    cout << "MainWindow initialized successfully" << endl;
}

void MainWindow::load_chapter_metadata() {
    GBytes* bytes = g_resources_lookup_data(
        "/app/data/chapters.json", G_RESOURCE_LOOKUP_FLAGS_NONE, nullptr);

    if (!bytes) {
        cerr << "Warning: chapters.json not found in resources" << endl;
        return;
    }

    gsize size;
    const char* data = static_cast<const char*>(g_bytes_get_data(bytes, &size));
    auto config = nlohmann::json::parse(string_view(data, size));
    g_bytes_unref(bytes);

    for (const auto& ch : config["chapters"]) {
        ChapterMeta meta;
        meta.id       = ch["id"];
        meta.title    = ch["title"];
        meta.category = ch.value("category", "cpp");

        // ui_resource 存 blp 路径，派生 GResource 路径和根控件名
        string blp_path = ch["ui_resource"];                 // "resources/ui/chapters/welcome.blp"
        size_t slash = blp_path.find_last_of('/');
        string filename = blp_path.substr(slash + 1);        // "welcome.blp"
        string stem = filename.substr(0, filename.size() - 4); // "welcome"

        meta.resource_path = "/app/chapters/" + stem + ".ui"; // "/app/chapters/welcome.ui"
        meta.widget_name   = stem + "_page";                  // "welcome_page"

        // 子章节标题列表
        if (ch.contains("subchapters")) {
            for (const auto& sub : ch["subchapters"]) {
                meta.subchapters.push_back(sub.get<string>());
            }
        }

        m_chapters[meta.id] = meta;

        cout << "Chapter loaded: " << meta.id
             << " -> \"" << meta.title << "\""
             << " [" << meta.category << "]"
             << " @ " << meta.resource_path << endl;
    }

    cout << "Loaded " << m_chapters.size() << " chapter(s) from chapters.json" << endl;
}

// ===================================================================
//  左侧分类导航
// ===================================================================

void MainWindow::setup_category_sidebar() {
    for (const auto& cat : m_categories) {
        auto btn = Gtk::make_managed<Gtk::ToggleButton>();

        // 按钮内部布局：图标 + 标签
        auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
        box->set_valign(Gtk::Align::CENTER);
        box->set_margin_top(12);
        box->set_margin_bottom(12);

        auto icon = Gtk::make_managed<Gtk::Image>();
        icon->set_from_icon_name(cat.icon_name);
        icon->set_pixel_size(24);

        auto label = Gtk::make_managed<Gtk::Label>(cat.title);
        label->set_wrap(true);
        label->set_justify(Gtk::Justification::CENTER);
        label->set_max_width_chars(6);

        box->append(*icon);
        box->append(*label);
        btn->set_child(*box);

        // 互斥分组
        if (!m_category_buttons.empty()) {
            btn->set_group(*m_category_buttons[0]);
        }

        btn->signal_toggled().connect([this, id = cat.id, btn]() {
            if (btn->get_active()) {
                on_category_selected(id);
            }
        });

        m_category_sidebar->append(*btn);
        m_category_buttons.push_back(btn);
    }

    // 默认选中第一个分类
    if (!m_category_buttons.empty()) {
        m_category_buttons[0]->set_active(true);
    }
}

void MainWindow::on_category_selected(const string& category_id) {
    if (category_id == m_current_category) return;
    m_current_category = category_id;

    build_chapter_tabs(category_id);
}

// ===================================================================
//  章节标签页
// ===================================================================

void MainWindow::build_chapter_tabs(const string& category_id) {
    // 移除栈中所有旧页面
    for (const auto& name : m_active_page_names) {
        auto child = m_chapter_stack->get_child_by_name(name);
        if (child) {
            m_chapter_stack->remove(*child);
        }
    }
    m_active_page_names.clear();

    // 移除 FlowBox 中所有旧标签按钮
    for (auto* btn : m_tab_buttons) {
        m_chapter_tab_box->remove(*btn);
    }
    m_tab_buttons.clear();
    m_tab_button_map.clear();

    // 收集该分类下的章节
    vector<ChapterMeta*> category_chapters;
    for (auto& [id, meta] : m_chapters) {
        if (meta.category == category_id) {
            category_chapters.push_back(&meta);
        }
    }

    if (category_chapters.empty()) {
        auto placeholder = Gtk::make_managed<Gtk::Label>("该分类暂无章节");
        placeholder->set_halign(Gtk::Align::CENTER);
        placeholder->set_valign(Gtk::Align::CENTER);
        m_chapter_stack->add(*placeholder, "__empty__", "空");
        m_active_page_names.insert("__empty__");
        return;
    }

    // 为每个章节加载内容并添加到栈 + 创建标签按钮
    for (size_t i = 0; i < category_chapters.size(); ++i) {
        auto* meta = category_chapters[i];
        auto builder = get_chapter_builder(meta->id);

        // 根据资源路径判断：空模板章节用 chapter_page 根控件，否则用 widget_name
        bool is_template = meta->resource_path.find("empty_chapter") != string::npos;
        Gtk::Widget* widget = nullptr;
        if (is_template) {
            widget = builder->get_widget<Gtk::Widget>("chapter_page");
        } else {
            widget = builder->get_widget<Gtk::Widget>(meta->widget_name);
        }

        if (!widget) {
            cerr << "Failed to get root widget for: " << meta->id << endl;
            continue;
        }

        m_chapter_stack->add(*widget, meta->id, meta->title);
        m_active_page_names.insert(meta->id);

        // 创建章节标签按钮（FlowBox 内自动换行，互斥分组）
        auto tab_btn = Gtk::make_managed<Gtk::ToggleButton>(meta->title);
        tab_btn->add_css_class("pill");
        if (!m_tab_buttons.empty()) {
            tab_btn->set_group(*m_tab_buttons[0]);
        }
        tab_btn->signal_toggled().connect([this, id = meta->id, tab_btn]() {
            if (tab_btn->get_active()) {
                m_chapter_stack->set_visible_child(id);
                m_current_chapter = id;
            }
        });
        m_chapter_tab_box->append(*tab_btn);
        m_tab_buttons.push_back(tab_btn);
        m_tab_button_map[meta->id] = tab_btn;

        // 空模板章节：注入标题 + 连接前后章导航（仅初始化一次）
        if (is_template && m_loaded_chapters.find(meta->id) == m_loaded_chapters.end()) {
            auto title_label = builder->get_widget<Gtk::Label>("chapter_title_label");
            if (title_label) {
                title_label->set_text(meta->title);
            }

            // 源码显示 + 运行按钮 + 结果框（按章节直接绑定对应类）
            auto source_view = builder->get_widget<Gtk::TextView>("source_view");
            auto run_button  = builder->get_widget<Gtk::Button>("run_button");
            auto result_view = builder->get_widget<Gtk::TextView>("result_view");
            auto topics_label = builder->get_widget<Gtk::Label>("topics_label");
            auto topics_list  = builder->get_widget<Gtk::ListBox>("topics_list");

            // 本章知识点列表：每个子章节一个条目 + 运行按钮
            if (topics_label && topics_list) {
                if (meta->subchapters.empty()) {
                    topics_label->set_visible(false);
                    topics_list->set_visible(false);
                } else {
                    for (const auto& title : meta->subchapters) {
                        auto row = Gtk::make_managed<Gtk::ListBoxRow>();

                        auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 12);

                        auto label_box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
                        label_box->set_hexpand(true);
                        auto title_label = Gtk::make_managed<Gtk::Label>(title);
                        title_label->set_halign(Gtk::Align::START);
                        title_label->add_css_class("heading");
                        label_box->append(*title_label);
                        box->append(*label_box);

                        auto run_btn = Gtk::make_managed<Gtk::Button>("运行");
                        run_btn->add_css_class("suggested-action");
                        run_btn->signal_clicked().connect([result_view, title]() {
                            result_view->get_buffer()->set_text("【" + title + "】暂无运行示例");
                        });
                        box->append(*run_btn);

                        row->set_child(*box);
                        topics_list->append(*row);
                    }
                }
            }

            if (meta->id == "02_pointers_references") {
                // 源码显示
                if (source_view) {
                    source_view->get_buffer()->set_text(FUNCTIONS06_SOURCE);
                }
                // 点击事件绑定类成员函数 run()
                if (run_button && result_view) {
                    auto demo = make_shared<Functions06>();
                    run_button->signal_clicked().connect([demo, result_view]() {
                        ostringstream oss;
                        demo->run(oss);   // 调用类成员函数
                        result_view->get_buffer()->set_text(oss.str());
                    });
                }
            } else {
                // 暂无演示类的章节：源码框空，运行按钮禁用
                if (source_view) {
                    source_view->get_buffer()->set_text("");
                }
                if (run_button) {
                    run_button->set_sensitive(false);
                }
            }

            auto prev_btn = builder->get_widget<Gtk::Button>("prev_button");
            auto next_btn = builder->get_widget<Gtk::Button>("next_button");

            if (prev_btn) {
                bool has_prev = i > 0;
                prev_btn->set_sensitive(has_prev);
                if (has_prev) {
                    string prev_id = category_chapters[i - 1]->id;
                    prev_btn->signal_clicked().connect([this, prev_id]() {
                        load_chapter(prev_id);
                    });
                }
            }

            if (next_btn) {
                bool has_next = i < category_chapters.size() - 1;
                next_btn->set_sensitive(has_next);
                if (has_next) {
                    string next_id = category_chapters[i + 1]->id;
                    next_btn->signal_clicked().connect([this, next_id]() {
                        load_chapter(next_id);
                    });
                }
            }

            m_loaded_chapters.insert(meta->id);
        }
    }

    // 激活第一个标签（触发切换到第一个章节）
    if (!m_tab_buttons.empty()) {
        m_tab_buttons[0]->set_active(true);
    }
}

Glib::RefPtr<Gtk::Builder> MainWindow::get_chapter_builder(const string& chapter_name) {
    auto it = m_chapter_builders.find(chapter_name);
    if (it != m_chapter_builders.end()) {
        return it->second;
    }

    auto meta_it = m_chapters.find(chapter_name);
    if (meta_it == m_chapters.end()) {
        cerr << "Chapter not found: " << chapter_name << endl;
        return {};
    }

    auto builder = Gtk::Builder::create_from_resource(meta_it->second.resource_path);
    m_chapter_builders[chapter_name] = builder;
    return builder;
}

// ===================================================================
//  章节切换（供章节内部按钮调用，如"下一章"）
// ===================================================================

void MainWindow::load_chapter(const string& chapter_name) {
    auto it = m_chapters.find(chapter_name);
    if (it == m_chapters.end()) {
        cerr << "Chapter not found: " << chapter_name << endl;
        return;
    }

    // 如果目标章节在不同分类，先切换分类
    if (it->second.category != m_current_category) {
        for (size_t i = 0; i < m_categories.size(); ++i) {
            if (m_categories[i].id == it->second.category) {
                m_category_buttons[i]->set_active(true);
                break;
            }
        }
    }

    // 激活对应的标签按钮（触发切换 + 高亮同步）
    auto btn_it = m_tab_button_map.find(chapter_name);
    if (btn_it != m_tab_button_map.end()) {
        btn_it->second->set_active(true);
    } else {
        // 兜底：按钮不存在时直接切换栈
        m_chapter_stack->set_visible_child(chapter_name);
    }
    m_current_chapter = chapter_name;
    cout << "Switched to chapter: " << chapter_name << endl;
}

