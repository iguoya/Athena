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
    EXPECT_EQ(sections->get_n_pages(), 9);
    // 每一页都必须是可取到的控件：apply_tab_labels 会按下标给每页换标签，
    // 取不到的页会在运行期变成 gtk_notebook_set_tab_label 断言失败。
    for (int index = 0; index < sections->get_n_pages(); ++index) {
        EXPECT_NE(sections->get_nth_page(index), nullptr)
            << "notebook page " << index << " is not a widget";
    }
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("type_semantics_run_button"), nullptr);
    // 「本章导览」与教学大纲都用 GTK 控件手写，不渲染 Markdown。
    EXPECT_NE(
        builder->get_widget<Gtk::Picture>("ts_outline_model_figure"), nullptr);
    // 两张路线图由 render/roadmap_view 按 requires 与评级数据实时绘制，
    // .blp 里只留容器；换回 Gtk::Picture 就意味着又引入一份会和
    // athena.json 漂移的副本。
    EXPECT_NE(
        builder->get_widget<Gtk::Box>("ts_guide_roadmap_host"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Box>("ts_outline_roadmap_host"), nullptr);
    EXPECT_EQ(builder->get_widget<Gtk::Picture>("ts_map_figure"), nullptr);
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

// 字号只有一个绝对基准（window），其余一律 em。这个测试把规则钉住：
// 再有人写 pt，基准对那一处就失效——那正是改了基准却"感觉没生效"的成因。
TEST(GtkResourceTest, KeepsASingleAbsoluteFontSizeBaseline) {
    const std::string stylesheet = load_text_resource("/app/style.css");
    ASSERT_FALSE(stylesheet.empty());

    EXPECT_NE(stylesheet.find("window {\n    font-size: 20pt;"), std::string::npos)
        << "基准字号应当是 window 上的 20pt";

    const std::regex absolute(R"(font-size:\s*([0-9.]+)(pt|px))");
    int absolute_count = 0;
    for (std::sregex_iterator match(
             stylesheet.begin(), stylesheet.end(), absolute),
         end;
         match != end;
         ++match) {
        ++absolute_count;
        EXPECT_EQ(match->str(), "font-size: 20pt")
            << "除基准外不得使用绝对字号，改用 em: " << match->str();
    }
    EXPECT_EQ(absolute_count, 1) << "绝对字号只应出现在基准那一处";

    // em 值下限：0.75em 配 22pt 基准约合 16.5pt，仍在可读范围内。
    const std::regex relative(R"(font-size:\s*([0-9.]+)em)");
    for (std::sregex_iterator match(
             stylesheet.begin(), stylesheet.end(), relative),
         end;
         match != end;
         ++match) {
        EXPECT_GE(std::stod((*match)[1].str()), 0.75)
            << "相对字号过小，低于可读下限: " << match->str();
    }
}

} // namespace

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    const auto application = Gtk::Application::create(
        "io.github.iguoya.athena.tests");
    gtk_source_init();
    return RUN_ALL_TESTS();
}
