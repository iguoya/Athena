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

    EXPECT_NE(builder->get_widget<Gtk::Stack>("root_stack"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Stack>("chapter_stack"), nullptr);
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
    // 验证工作台 / 动手实验 / 探索（暂定）。动手实验是 ADR 0053 加的，
    // 与验证工作台并列——那边看真实源码，这边自己写。
    EXPECT_EQ(notebook->get_n_pages(), 3);
    const auto workspace =
        builder->get_widget<Gtk::Paned>("experiment_workspace_paned");
    ASSERT_NE(workspace, nullptr);
    EXPECT_EQ(workspace->get_orientation(), Gtk::Orientation::HORIZONTAL);

    // 动手实验那一页的控件，CaseDock 按这些名字取（ADR 0053）。
    const auto case_paned =
        builder->get_widget<Gtk::Paned>("case_workspace_paned");
    ASSERT_NE(case_paned, nullptr);
    EXPECT_EQ(case_paned->get_orientation(), Gtk::Orientation::HORIZONTAL);
    EXPECT_NE(
        gtk_builder_get_object(builder->gobj(), "case_source_view"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::TextView>("case_output_view"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("case_prompt_label"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("case_goal_label"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("case_hint_label"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("case_file_label"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("case_status_label"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Button>("case_run_button"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Button>("case_reset_button"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Spinner>("case_spinner"), nullptr);

    // 源码框必须可编辑——整条 ADR 0053 就是为了让学员能写。
    auto* case_source = GTK_TEXT_VIEW(
        gtk_builder_get_object(builder->gobj(), "case_source_view"));
    ASSERT_NE(case_source, nullptr);
    EXPECT_TRUE(gtk_text_view_get_editable(case_source));
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
    // 「教学大纲」+ 七个知识点小节，顺序服从大纲的推荐顺序：初始化 /
    // 对象生命周期 / 类型推导 / enum class / 类型转换 / 值类别 / decltype。
    // ADR 0039 撤销了原先排在最前的「本章导览」，所以是 8 页不是 9 页。
    EXPECT_EQ(sections->get_n_pages(), 8);
    // 每一页都必须是可取到的控件：apply_tab_labels 会按下标给每页换标签，
    // 取不到的页会在运行期变成 gtk_notebook_set_tab_label 断言失败。
    for (int index = 0; index < sections->get_n_pages(); ++index) {
        EXPECT_NE(sections->get_nth_page(index), nullptr)
            << "notebook page " << index << " is not a widget";
    }
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("type_semantics_run_button"), nullptr);
    // 教学大纲用 GTK 控件手写，不渲染 Markdown。
    EXPECT_NE(
        builder->get_widget<Gtk::DrawingArea>("ts_outline_loop_figure"), nullptr);
    // 路线图由 render/roadmap_view 按 requires 与评级数据实时绘制，.blp 里
    // 只留容器；换回 Gtk::Picture 就意味着又引入一份会和 athena.json 漂移的
    // 副本。合并导览之后只剩这一张（ADR 0039）。
    EXPECT_NE(
        builder->get_widget<Gtk::Box>("ts_outline_roadmap_host"), nullptr);
    EXPECT_EQ(
        builder->get_widget<Gtk::Box>("ts_guide_roadmap_host"), nullptr);
    EXPECT_EQ(builder->get_widget<Gtk::Picture>("ts_map_figure"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::DrawingArea>("type_semantics_deduction_graph"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("ts_deduction_anim_playpause"),
        nullptr);
    // 插图按 ADR 0038 改成自绘：Picture 变 DrawingArea，页面代码接画笔。
    EXPECT_NE(
        builder->get_widget<Gtk::DrawingArea>("ts_lifetime_figure"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Button>("type_semantics_lifetime_button"),
        nullptr);
    // decltype 节的活对照：表达式按钮与两列结果标签都由页面构造函数按 id 取，
    // 少一个就会在打开这一章时抛异常，所以在这里一并守住。
    EXPECT_NE(builder->get_widget<Gtk::Button>("ts_dt_expr_paren"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Button>("ts_dt_expr_ref"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("ts_dt_auto_result"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("ts_dt_decltype_result"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::Box>("type_semantics_decltype_unit_host"),
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
