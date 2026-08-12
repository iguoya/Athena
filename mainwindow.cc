#include "mainwindow.h"
#include <iostream>
#include <gio/gio.h>
#include <nlohmann/json.hpp>

using namespace std;

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
    m_chapter_tabs     = m_main_builder->get_widget<Gtk::StackSwitcher>("chapter_tabs");

    if (!m_category_sidebar || !m_chapter_stack || !m_chapter_tabs) {
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
        meta.id            = ch["id"];
        meta.title         = ch["title"];
        meta.category      = ch.value("category", "cpp");
        meta.resource_path = ch["ui_resource"];
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
        auto page = m_chapter_stack->add(*placeholder, "__empty__", "空");
        m_active_page_names.insert("__empty__");
        return;
    }

    // 为每个章节加载内容并添加到栈
    for (auto* meta : category_chapters) {
        auto builder = get_chapter_builder(meta->id);
        string root_name = meta->id + "_page";
        auto widget = builder->get_widget<Gtk::Widget>(root_name);

        if (!widget) {
            cerr << "Failed to get root widget: " << root_name << endl;
            continue;
        }

        auto page = m_chapter_stack->add(*widget, meta->id, meta->title);
        m_active_page_names.insert(meta->id);

        // 章节特定的信号初始化（仅首次）
        if (m_loaded_chapters.find(meta->id) == m_loaded_chapters.end()) {
            if (meta->id == "basic_syntax") {
                initialize_basic_syntax_chapter(builder);
            } else if (meta->id == "functions") {
                initialize_functions_chapter(builder);
            }
            m_loaded_chapters.insert(meta->id);
        }
    }

    // 切换到第一个章节
    m_chapter_stack->set_visible_child(category_chapters[0]->id);
    m_current_chapter = category_chapters[0]->id;
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

    // 切换到目标章节标签页
    m_chapter_stack->set_visible_child(chapter_name);
    m_current_chapter = chapter_name;
    cout << "Switched to chapter: " << chapter_name << endl;
}

// ===================================================================
//  章节初始化（信号连接、代码示例填充等）
// ===================================================================

void MainWindow::initialize_basic_syntax_chapter(const Glib::RefPtr<Gtk::Builder>& builder) {
    cout << "Initializing basic syntax chapter..." << endl;

    auto variables_start   = builder->get_widget<Gtk::Button>("variables_start");
    auto datatypes_start   = builder->get_widget<Gtk::Button>("datatypes_start");
    auto operators_start   = builder->get_widget<Gtk::Button>("operators_start");
    auto io_start          = builder->get_widget<Gtk::Button>("io_start");
    auto comments_start    = builder->get_widget<Gtk::Button>("comments_start");
    auto copy_code         = builder->get_widget<Gtk::Button>("copy_code");
    auto practice_button   = builder->get_widget<Gtk::Button>("practice_button");
    auto quiz_button       = builder->get_widget<Gtk::Button>("quiz_button");
    auto next_chapter      = builder->get_widget<Gtk::Button>("next_chapter");
    auto code_view         = builder->get_widget<Gtk::TextView>("code_view");

    if (code_view) {
        auto buffer = code_view->get_buffer();
        buffer->set_text(R"(#include <iostream>
using namespace std;

int main() {
    // 变量声明和初始化
    int age = 25;
    double height = 175.5;
    char grade = 'A';
    bool isStudent = true;

    // 输出变量值
    cout << "年龄: " << age << endl;
    cout << "身高: " << height << "cm" << endl;
    cout << "成绩: " << grade << endl;
    cout << "是否学生: " << isStudent << endl;

    return 0;
})");
    }

    if (variables_start) variables_start->signal_clicked().connect([]() {
        cout << "开始学习变量与常量" << endl;
    });
    if (datatypes_start) datatypes_start->signal_clicked().connect([]() {
        cout << "开始学习数据类型" << endl;
    });
    if (operators_start) operators_start->signal_clicked().connect([]() {
        cout << "开始学习运算符" << endl;
    });
    if (io_start) io_start->signal_clicked().connect([]() {
        cout << "开始学习输入输出" << endl;
    });
    if (comments_start) comments_start->signal_clicked().connect([]() {
        cout << "开始学习注释与风格" << endl;
    });

    if (copy_code) {
        copy_code->signal_clicked().connect([code_view]() {
            if (code_view) {
                auto buffer = code_view->get_buffer();
                auto text = buffer->get_text();
                auto clipboard = Gdk::Display::get_default()->get_clipboard();
                clipboard->set_text(text);
                cout << "代码已复制到剪贴板" << endl;
            }
        });
    }

    if (practice_button) practice_button->signal_clicked().connect([]() {
        cout << "打开在线练习平台" << endl;
    });
    if (quiz_button) quiz_button->signal_clicked().connect([]() {
        cout << "开始章节测验" << endl;
    });
    if (next_chapter) next_chapter->signal_clicked().connect([this]() {
        cout << "跳转到下一章" << endl;
        load_chapter("control_flow");
    });
}

void MainWindow::initialize_functions_chapter(const Glib::RefPtr<Gtk::Builder>& builder) {
    cout << "Initializing functions chapter..." << endl;

    auto definition_start   = builder->get_widget<Gtk::Button>("definition_start");
    auto parameters_start   = builder->get_widget<Gtk::Button>("parameters_start");
    auto overloading_start  = builder->get_widget<Gtk::Button>("overloading_start");
    auto defaults_start     = builder->get_widget<Gtk::Button>("defaults_start");
    auto inline_start       = builder->get_widget<Gtk::Button>("inline_start");
    auto recursion_start    = builder->get_widget<Gtk::Button>("recursion_start");
    auto value_code         = builder->get_widget<Gtk::TextView>("value_code");
    auto reference_code     = builder->get_widget<Gtk::TextView>("reference_code");
    auto exercise_code      = builder->get_widget<Gtk::TextView>("exercise_code");
    auto run_code           = builder->get_widget<Gtk::Button>("run_code");
    auto check_answer       = builder->get_widget<Gtk::Button>("check_answer");
    auto show_hint          = builder->get_widget<Gtk::Button>("show_hint");
    auto prev_chapter       = builder->get_widget<Gtk::Button>("prev_chapter");
    auto practice_more      = builder->get_widget<Gtk::Button>("practice_more");
    auto next_chapter_btn   = builder->get_widget<Gtk::Button>("next_chapter");

    if (value_code) {
        auto buffer = value_code->get_buffer();
        buffer->set_text(R"(// 值传递示例
void swap(int a, int b) {
    int temp = a;
    a = b;
    b = temp;
}

int main() {
    int x = 5, y = 10;
    swap(x, y);
    // x=5, y=10 (未改变)
    return 0;
})");
    }

    if (reference_code) {
        auto buffer = reference_code->get_buffer();
        buffer->set_text(R"(// 引用传递示例
void swap(int &a, int &b) {
    int temp = a;
    a = b;
    b = temp;
}

int main() {
    int x = 5, y = 10;
    swap(x, y);
    // x=10, y=5 (已交换)
    return 0;
})");
    }

    if (exercise_code) {
        auto buffer = exercise_code->get_buffer();
        buffer->set_text(R"(// 请编写 max 函数
int max(int a, int b) {
    // 在此处编写代码

})");
    }

    if (definition_start) definition_start->signal_clicked().connect([]() {
        cout << "开始学习函数定义" << endl;
    });
    if (parameters_start) parameters_start->signal_clicked().connect([]() {
        cout << "开始学习参数传递" << endl;
    });
    if (overloading_start) overloading_start->signal_clicked().connect([]() {
        cout << "开始学习函数重载" << endl;
    });
    if (defaults_start) defaults_start->signal_clicked().connect([]() {
        cout << "开始学习默认参数" << endl;
    });
    if (inline_start) inline_start->signal_clicked().connect([]() {
        cout << "开始学习内联函数" << endl;
    });
    if (recursion_start) recursion_start->signal_clicked().connect([]() {
        cout << "开始学习递归函数" << endl;
    });

    if (run_code) {
        run_code->signal_clicked().connect([exercise_code]() {
            if (exercise_code) {
                auto buffer = exercise_code->get_buffer();
                auto code = buffer->get_text();
                cout << "运行代码:\n" << code << endl;
            }
        });
    }

    if (check_answer) {
        check_answer->signal_clicked().connect([exercise_code]() {
            if (exercise_code) {
                auto buffer = exercise_code->get_buffer();
                auto code = buffer->get_text();
                if (code.find("return") != string::npos &&
                    code.find(">") != string::npos) {
                    cout << "答案正确！" << endl;
                } else {
                    cout << "答案需要改进，请检查逻辑" << endl;
                }
            }
        });
    }

    if (show_hint) {
        show_hint->signal_clicked().connect([exercise_code]() {
            cout << "提示: 使用条件运算符 (a > b) ? a : b" << endl;
            if (exercise_code) {
                auto buffer = exercise_code->get_buffer();
                buffer->set_text(R"(// 请编写 max 函数
int max(int a, int b) {
    // 提示: 使用 if 语句或条件运算符
    return (a > b) ? a : b;
})");
            }
        });
    }

    if (prev_chapter) prev_chapter->signal_clicked().connect([this]() {
        cout << "跳转到上一章: 基础语法" << endl;
        load_chapter("basic_syntax");
    });
    if (practice_more) practice_more->signal_clicked().connect([]() {
        cout << "打开更多函数练习" << endl;
    });
    if (next_chapter_btn) next_chapter_btn->signal_clicked().connect([this]() {
        cout << "跳转到下一章: 指针与引用" << endl;
        load_chapter("pointers_references");
    });
}
