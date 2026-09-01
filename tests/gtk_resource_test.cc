#include <gtest/gtest.h>
#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

namespace {

TEST(GtkResourceTest, LoadsTheMainWindowNavigationControls) {
    const auto builder = Gtk::Builder::create_from_resource("/app/window.ui");

    EXPECT_NE(builder->get_widget<Gtk::FlowBox>("home_grid"), nullptr);
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

} // namespace

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    const auto application = Gtk::Application::create(
        "io.github.iguoya.athena.tests");
    gtk_source_init();
    return RUN_ALL_TESTS();
}
