#include "ui/lesson_page.h"

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "ui/lesson_figures.h"

#include <gtest/gtest.h>

#include <gtkmm.h>

using namespace std;

namespace {

int count_widgets(Gtk::Widget& root) {
    int total = 0;
    for (Gtk::Widget* child = root.get_first_child(); child != nullptr;
         child = child->get_next_sibling()) {
        total += 1 + count_widgets(*child);
    }
    return total;
}

}  // namespace

// 完整走一遍 MainWindow 构建章节页的流程。截图只能看一眼当下，这条能挡住
// 「课文写了、页面却是空的」这类问题——白屏在测试里表现为控件数为个位数。
TEST(LessonPageTest, BuildsTabsForTheShippedChapter) {
    ContentLoader loader;
    const ChapterCatalog catalog = ChapterCatalog::from_runtime_json(
        loader.load_resource("/app/data/chapter_catalog.json"));

    const ChapterMeta* chapter = catalog.find_chapter("cpp", "ValueSemantics");
    ASSERT_NE(chapter, nullptr);
    // 写了课文的章节应当被生成器自动指到数据驱动页面（ADR 0055）。
    EXPECT_EQ(chapter->widget_name, "lesson_page");
    EXPECT_EQ(chapter->resource_path, "/app/chapters/lesson.ui");

    const auto builder =
        Gtk::Builder::create_from_resource(chapter->resource_path);
    auto* root = builder->get_widget<Gtk::Widget>(chapter->widget_name);
    ASSERT_NE(root, nullptr);

    const LessonPage page(*chapter, builder, make_lesson_figure, {});

    auto* notebook = builder->get_widget<Gtk::Notebook>("lesson_page_notebook");
    ASSERT_NE(notebook, nullptr);
    // 教学大纲 + 五个知识点。
    EXPECT_EQ(notebook->get_n_pages(), 6);
    EXPECT_EQ(notebook->get_tab_label_text(*notebook->get_nth_page(0)), "教学大纲");
    EXPECT_EQ(notebook->get_tab_label_text(*notebook->get_nth_page(1)), "拷贝控制");

    // 每一页都要有实际内容——这条才是真正挡白屏的断言。
    for (int index = 0; index < notebook->get_n_pages(); ++index) {
        Gtk::Widget* tab = notebook->get_nth_page(index);
        ASSERT_NE(tab, nullptr) << index;
        EXPECT_GT(count_widgets(*tab), 10)
            << "第 " << index << " 页几乎是空的";
    }
}
