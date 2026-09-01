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

    EXPECT_NE(builder->get_widget<Gtk::Box>("home_graph"), nullptr);
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

TEST(GtkResourceTest, LoadsTheExperimentDialogWidgetTree) {
    const auto builder =
        Gtk::Builder::create_from_resource("/app/experiment_dialog.ui");

    EXPECT_NE(
        builder->get_widget<Gtk::Window>("experiment_dialog_window"),
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
}

TEST(GtkResourceTest, KeepsTheWorkbenchFocusedOnTheArticle) {
    const auto builder = Gtk::Builder::create_from_resource(
        "/app/chapters/workbench_chapter.ui");

    EXPECT_NE(
        builder->get_widget<Gtk::Box>("workbench_chapter_page"),
        nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::DrawingArea>("workbench_article_host"),
        nullptr);
    EXPECT_EQ(builder->get_widget<Gtk::Box>("workbench_dock_panel"), nullptr);
    EXPECT_EQ(
        gtk_builder_get_object(builder->gobj(), "workbench_source_view"),
        nullptr);
    EXPECT_EQ(
        builder->get_widget<Gtk::TextView>("workbench_result_view"),
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
