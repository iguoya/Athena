#include <gtest/gtest.h>
#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <regex>
#include <string>

namespace {

std::string load_text_resource(const char* path) {
    GError* error = nullptr;
    GBytes* bytes = g_resources_lookup_data(
        path, G_RESOURCE_LOOKUP_FLAGS_NONE, &error);
    if (!bytes) {
        const std::string message = error ? error->message : "unknown error";
        g_clear_error(&error);
        ADD_FAILURE() << "Failed to load " << path << ": " << message;
        return {};
    }
    gsize size = 0;
    const auto* data = static_cast<const char*>(g_bytes_get_data(bytes, &size));
    std::string text(data, size);
    g_bytes_unref(bytes);
    return text;
}

TEST(GtkResourceTest, LoadsTheMainWindowNavigationControls) {
    const auto builder = Gtk::Builder::create_from_resource("/app/window.ui");

    auto* window = builder->get_widget<Gtk::ApplicationWindow>("window");
    ASSERT_NE(window, nullptr);
    int default_width = 0;
    int default_height = 0;
    gtk_window_get_default_size(
        GTK_WINDOW(window->gobj()), &default_width, &default_height);
    EXPECT_EQ(default_width, 1440);
    EXPECT_EQ(default_height, 900);

    EXPECT_NE(builder->get_widget<Gtk::Box>("home_graph"), nullptr);
    // apps/ 下独立学习应用的入口容器（ADR 0032）。
    EXPECT_NE(builder->get_widget<Gtk::Stack>("root_stack"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Stack>("chapter_stack"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Button>("home_button"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::MenuButton>("chapter_switcher"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::PopoverMenuBar>("app_menu_bar"), nullptr);
}

TEST(GtkResourceTest, LoadsTheCodeChapterWidgetTree) {
    const auto builder = Gtk::Builder::create_from_resource(
        "/app/chapters/empty_chapter.ui");

    EXPECT_NE(builder->get_widget<Gtk::Box>("chapter_page"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("chapter_title_label"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::ListBox>("topics_list"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Label>("knowledge_description_label"),
        nullptr);
    EXPECT_EQ(builder->get_widget<Gtk::TextView>("result_view"), nullptr);
    EXPECT_EQ(gtk_builder_get_object(builder->gobj(), "source_view"), nullptr);
}

TEST(GtkResourceTest, LoadsTheFocusedExperimentPageWidgetTree) {
    const auto builder = Gtk::Builder::create_from_resource("/app/window.ui");

    EXPECT_NE(builder->get_widget<Gtk::Box>("experiment_page"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("experiment_back_button"),
        nullptr);
    EXPECT_NE(
        gtk_builder_get_object(builder->gobj(), "experiment_source_view"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::TextView>("experiment_result_view"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("experiment_run_button"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Spinner>("experiment_spinner"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Label>("experiment_status_label"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Label>("experiment_title_label"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Label>("experiment_objective_label"),
        nullptr);
    const auto notebook =
        builder->get_widget<Gtk::Notebook>("experiment_notebook");
    ASSERT_NE(notebook, nullptr);
    EXPECT_EQ(notebook->get_n_pages(), 2);
    const auto workspace =
        builder->get_widget<Gtk::Paned>("experiment_workspace_paned");
    ASSERT_NE(workspace, nullptr);
    EXPECT_EQ(workspace->get_orientation(), Gtk::Orientation::HORIZONTAL);
}

TEST(GtkResourceTest, LoadsTheNativeTypeSemanticsLearningScene) {
    const auto builder = Gtk::Builder::create_from_resource(
        "/app/chapters/type_semantics_lesson.ui");

    EXPECT_NE(
        builder->get_widget<Gtk::Box>("type_semantics_lesson_page"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Box>("type_semantics_learning_unit_host"),
        nullptr);
    const auto sections =
        builder->get_widget<Gtk::Notebook>("type_semantics_section_notebook");
    ASSERT_NE(sections, nullptr);
    // 「教学大纲」+「本章导览」+ 七个知识点小节，顺序服从大纲的推荐顺序：
    // 初始化 / 对象生命周期 / 类型推导 / enum class / 类型转换 / 值类别 / decltype。
    // 末尾还有「运行实验」：实验在页内跑，教学过程不被跳页打断。
    EXPECT_EQ(sections->get_n_pages(), 10);
    // 每一页都必须是可取到的控件：apply_tab_labels 会按下标给每页换标签，
    // 取不到的页会在运行期变成 gtk_notebook_set_tab_label 断言失败。
    for (int index = 0; index < sections->get_n_pages(); ++index) {
        EXPECT_NE(sections->get_nth_page(index), nullptr)
            << "notebook page " << index << " is not a widget";
    }
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("type_semantics_reference_button"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("type_semantics_run_button"), nullptr);
    // 章节教学大纲是第一个标签，用 GTK 控件手写而不是渲染 Markdown。
    EXPECT_NE(
        builder->get_widget<Gtk::Picture>("ts_outline_model_figure"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::TextView>("ts_lab_result_view"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("ts_lab_run_button"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Picture>("ts_map_figure"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::DrawingArea>("type_semantics_deduction_graph"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("ts_deduction_anim_playpause"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Picture>("ts_lifetime_figure"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("type_semantics_lifetime_button"),
        nullptr);
}

TEST(GtkResourceTest, LoadsTheInlineLearningUnitTemplate) {
    const auto builder = Gtk::Builder::create_from_resource("/app/learning_unit.ui");
    EXPECT_NE(builder->get_widget<Gtk::Box>("learning_unit"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Box>("learning_unit_choices"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("learning_unit_verify_button"),
        nullptr);
}

TEST(GtkResourceTest, KeepsGlobalReadableTextAtLeastFourteenPoints) {
    const std::string stylesheet = load_text_resource("/app/style.css");
    ASSERT_FALSE(stylesheet.empty());

    const std::regex point_size(R"(font-size:\s*([0-9]+(?:\.[0-9]+)?)pt)");
    for (std::sregex_iterator match(
             stylesheet.begin(), stylesheet.end(), point_size),
         end;
         match != end;
         ++match) {
        EXPECT_GE(std::stod((*match)[1].str()), 14.0)
            << "Typography rule falls below the global 14pt baseline: "
            << match->str();
    }

    EXPECT_NE(stylesheet.find("window {\n    font-size: 16pt;"),
              std::string::npos);

    const std::string article = load_text_resource("/app/article.css");
    ASSERT_FALSE(article.empty());
    EXPECT_NE(article.find("font-size: var(--article-font-size);"),
              std::string::npos);
    EXPECT_EQ(article.find("font-size: 14px;"), std::string::npos);
    EXPECT_EQ(article.find("font-size: 0.82rem;"), std::string::npos);
}

} // namespace

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    const auto application = Gtk::Application::create(
        "io.github.iguoya.athena.tests");
    gtk_source_init();
    return RUN_ALL_TESTS();
}
