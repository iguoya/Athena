#include "mainwindow.h"
#include <iostream>
#include <gio/gio.h>
#include <nlohmann/json.hpp>

using namespace std;

MainWindow::MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder)
    : Gtk::ApplicationWindow(cobject)
    , m_main_builder(builder)
    , m_current_widget(nullptr)
{
    // 设置窗口控制
    setup_window_controls();
    maximize();
    // fullscreen();    
    
    // 获取主要 UI 组件
    m_menu_list = m_main_builder->get_widget<Gtk::ListBox>("menu_list");
    m_content_container = m_main_builder->get_widget<Gtk::Box>("content_container");
    m_content_title = m_main_builder->get_widget<Gtk::Label>("content_title");
    
    // 检查所有必要的UI组件是否成功获取
    if (!m_menu_list || !m_content_container || !m_content_title) {
        throw runtime_error("Failed to get required widgets from main UI");
    }
    
    // 连接菜单点击事件，当用户点击任意一行时，会触发 on_menu_row_activated
    m_menu_list->signal_row_activated().connect(
        sigc::mem_fun(*this, &MainWindow::on_menu_row_activated));
    
    // 运行时加载章节元数据（替代硬编码 map）
    load_chapter_metadata();

    load_chapter("welcome");
    cout << "MainWindow initialized successfully" << endl;
}

void MainWindow::setup_window_controls() {
    // set_resizable(true);        // 允许调整大小
    // set_deletable(false);       // 禁用关闭按钮
    
    // 处理窗口关闭请求
    // signal_close_request().connect([]() -> bool {
    //     return true;  // 返回 true 阻止关闭
    // }, false);
}

void MainWindow::on_menu_row_activated(Gtk::ListBoxRow* row) {
    if (!row) return;
    
    // string chapter_name;
        // 直接使用行的名称（在 Glade UI 文件中设置）作为章节ID
    string chapter_name = row->get_name();

    // string row_name = row->get_name();
    
    cout << "Menu row activated: " << chapter_name << endl;
    
    // 如果章节名称不为空且不是当前章节，则加载新章节
    if (!chapter_name.empty() && chapter_name != m_current_chapter) {
        load_chapter(chapter_name);
    }
}

void MainWindow::load_chapter_metadata() {
    // 从 GResource 加载 chapters.json，用 nlohmann/json 解析
    GBytes* bytes = g_resources_lookup_data(
        "/app/data/chapters.json",
        G_RESOURCE_LOOKUP_FLAGS_NONE, nullptr);

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
        meta.id = ch["id"];
        meta.title = ch["title"];
        meta.resource_path = ch["ui_resource"];
        m_chapters[meta.id] = meta;

        cout << "Chapter loaded: " << meta.id
                  << " -> \"" << meta.title << "\""
                  << " @ " << meta.resource_path << endl;
    }

    cout << "Loaded " << m_chapters.size() << " chapter(s) from chapters.json" << endl;
}

void MainWindow::load_chapter(const string& chapter_name) {

        // 移除旧内容
    // 这个步骤至关重要，它确保了在添加新内容前，旧的欢迎页面被移除
    auto children = m_content_container->get_children();
    for (const auto& child : children)
    {
        m_content_container->remove(*child);
    }


    // 检查章节是否存在
    auto it = m_chapters.find(chapter_name);
    if (it == m_chapters.end()) {
        cerr << "Chapter not found: " << chapter_name << endl;
        return;
    }

    try {
        cout << "Loading chapter: " << chapter_name << endl;

        // // 移除当前章节
        // if (m_current_widget) {
        //     m_content_container->remove(*m_current_widget);
        //     m_current_widget = nullptr;
        // }

        // 检查是否已经加载过这个章节的构建器
        auto builder_it = m_chapter_builders.find(chapter_name);
        Glib::RefPtr<Gtk::Builder> chapter_builder;

        if (builder_it == m_chapter_builders.end()) {
            // 首次加载，创建新的构建器
            cout << "Creating new builder for: " << chapter_name << endl;
            chapter_builder = Gtk::Builder::create_from_resource(it->second.resource_path);
            m_chapter_builders[chapter_name] = chapter_builder;
        } else {
            // 使用已缓存的构建器
            cout << "Using cached builder for: " << chapter_name << endl;
            chapter_builder = builder_it->second;
        }
        
        // 获取章节根 widget
        string root_widget_name = chapter_name + "_page";
        auto chapter_widget = chapter_builder->get_widget<Gtk::Widget>(root_widget_name);
        
        if (!chapter_widget) {
            cerr << "Failed to get root widget: " << root_widget_name << endl;
            return;
        }
        
        // 添加到内容容器
        m_content_container->append(*chapter_widget);
        m_current_widget = chapter_widget;
        m_current_chapter = chapter_name;
        
        chapter_widget->show();

        // 更新标题（已通过 m_chapters 查找，直接使用 it->second.title）
        m_content_title->set_text(it->second.title);
        
        // 根据章节类型进行特殊初始化
        if (chapter_name == "basic_syntax") {
            initialize_basic_syntax_chapter(chapter_builder);
        } else if (chapter_name == "functions") {
            initialize_functions_chapter(chapter_builder);
        }
        
        cout << "Chapter loaded successfully: " << chapter_name << endl;
        
    } catch (const exception& e) {
        cerr << "Error loading chapter " << chapter_name << ": " << e.what() << endl;
    }
}

void MainWindow::initialize_basic_syntax_chapter(const Glib::RefPtr<Gtk::Builder>& builder) {
    cout << "Initializing basic syntax chapter..." << endl;
    
    // 获取基础语法章节的特定组件
    auto variables_start = builder->get_widget<Gtk::Button>("variables_start");
    auto datatypes_start = builder->get_widget<Gtk::Button>("datatypes_start");
    auto operators_start = builder->get_widget<Gtk::Button>("operators_start");
    auto io_start = builder->get_widget<Gtk::Button>("io_start");
    auto comments_start = builder->get_widget<Gtk::Button>("comments_start");
    
    auto copy_code = builder->get_widget<Gtk::Button>("copy_code");
    auto practice_button = builder->get_widget<Gtk::Button>("practice_button");
    auto quiz_button = builder->get_widget<Gtk::Button>("quiz_button");
    auto next_chapter = builder->get_widget<Gtk::Button>("next_chapter");
    
    auto code_view = builder->get_widget<Gtk::TextView>("code_view");
    
    // 设置代码示例
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
    
    // 连接按钮事件
    if (variables_start) {
        variables_start->signal_clicked().connect([this]() {
            cout << "开始学习变量与常量" << endl;
            // 这里可以打开详细的变量学习页面
        });
    }
    
    if (datatypes_start) {
        datatypes_start->signal_clicked().connect([this]() {
            cout << "开始学习数据类型" << endl;
            // 这里可以打开数据类型学习页面
        });
    }
    
    if (operators_start) {
        operators_start->signal_clicked().connect([this]() {
            cout << "开始学习运算符" << endl;
            // 这里可以打开运算符学习页面
        });
    }
    
    if (io_start) {
        io_start->signal_clicked().connect([this]() {
            cout << "开始学习输入输出" << endl;
        });
    }
    
    if (comments_start) {
        comments_start->signal_clicked().connect([this]() {
            cout << "开始学习注释与风格" << endl;
        });
    }
    
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
    
    if (practice_button) {
        practice_button->signal_clicked().connect([this]() {
            cout << "打开在线练习平台" << endl;
        });
    }
    
    if (quiz_button) {
        quiz_button->signal_clicked().connect([this]() {
            cout << "开始章节测验" << endl;
        });
    }
    
    if (next_chapter) {
        next_chapter->signal_clicked().connect([this]() {
            cout << "跳转到下一章" << endl;
            load_chapter("control_flow");
        });
    }
}

void MainWindow::initialize_functions_chapter(const Glib::RefPtr<Gtk::Builder>& builder) {
    cout << "Initializing functions chapter..." << endl;
    
    // 获取函数章节的特定组件
    auto definition_start = builder->get_widget<Gtk::Button>("definition_start");
    auto parameters_start = builder->get_widget<Gtk::Button>("parameters_start");
    auto overloading_start = builder->get_widget<Gtk::Button>("overloading_start");
    auto defaults_start = builder->get_widget<Gtk::Button>("defaults_start");
    auto inline_start = builder->get_widget<Gtk::Button>("inline_start");
    auto recursion_start = builder->get_widget<Gtk::Button>("recursion_start");
    
    auto value_code = builder->get_widget<Gtk::TextView>("value_code");
    auto reference_code = builder->get_widget<Gtk::TextView>("reference_code");
    auto exercise_code = builder->get_widget<Gtk::TextView>("exercise_code");
    
    auto run_code = builder->get_widget<Gtk::Button>("run_code");
    auto check_answer = builder->get_widget<Gtk::Button>("check_answer");
    auto show_hint = builder->get_widget<Gtk::Button>("show_hint");
    
    auto prev_chapter = builder->get_widget<Gtk::Button>("prev_chapter");
    auto practice_more = builder->get_widget<Gtk::Button>("practice_more");
    auto next_chapter_btn = builder->get_widget<Gtk::Button>("next_chapter");
    
    // 设置代码示例
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
    
    // 连接按钮事件
    if (definition_start) {
        definition_start->signal_clicked().connect([this]() {
            cout << "开始学习函数定义" << endl;
        });
    }
    
    if (parameters_start) {
        parameters_start->signal_clicked().connect([this]() {
            cout << "开始学习参数传递" << endl;
        });
    }
    
    if (overloading_start) {
        overloading_start->signal_clicked().connect([this]() {
            cout << "开始学习函数重载" << endl;
        });
    }
    
    if (defaults_start) {
        defaults_start->signal_clicked().connect([this]() {
            cout << "开始学习默认参数" << endl;
        });
    }
    
    if (inline_start) {
        inline_start->signal_clicked().connect([this]() {
            cout << "开始学习内联函数" << endl;
        });
    }
    
    if (recursion_start) {
        recursion_start->signal_clicked().connect([this]() {
            cout << "开始学习递归函数" << endl;
        });
    }
    
    if (run_code) {
        run_code->signal_clicked().connect([exercise_code]() {
            if (exercise_code) {
                auto buffer = exercise_code->get_buffer();
                auto code = buffer->get_text();
                cout << "运行代码:\n" << code << endl;
                // 这里可以集成代码执行引擎
            }
        });
    }
    
    if (check_answer) {
        check_answer->signal_clicked().connect([exercise_code]() {
            if (exercise_code) {
                auto buffer = exercise_code->get_buffer();
                auto code = buffer->get_text();
                
                // 简单的答案检查
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
    
    if (prev_chapter) {
        prev_chapter->signal_clicked().connect([this]() {
            cout << "跳转到上一章: 基础语法" << endl;
            load_chapter("basic_syntax");
        });
    }
    
    if (practice_more) {
        practice_more->signal_clicked().connect([this]() {
            cout << "打开更多函数练习" << endl;
        });
    }
    
    if (next_chapter_btn) {
        next_chapter_btn->signal_clicked().connect([this]() {
            cout << "跳转到下一章: 指针与引用" << endl;
            load_chapter("pointers_references");
        });
    }
}
