#include <gtest/gtest.h>
#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

namespace {

TEST(GtkResourceTest, LoadsTheCodeChapterWidgetTree) {
    const auto builder = Gtk::Builder::create_from_resource(
        "/app/chapters/empty_chapter.ui");

    EXPECT_NE(builder->get_widget<Gtk::Box>("chapter_page"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::Label>("chapter_title_label"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::ListBox>("topics_list"), nullptr);
    EXPECT_NE(builder->get_widget<Gtk::TextView>("result_view"), nullptr);
    EXPECT_NE(
        gtk_builder_get_object(builder->gobj(), "source_view"),
        nullptr);
}

TEST(GtkResourceTest, LoadsTheArticleWebViewHost) {
    const auto builder = Gtk::Builder::create_from_resource(
        "/app/chapters/article_chapter.ui");

    EXPECT_NE(builder->get_widget<Gtk::Box>("article_page"), nullptr);
    EXPECT_NE(
        builder->get_widget<Gtk::DrawingArea>("article_web_host"),
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
