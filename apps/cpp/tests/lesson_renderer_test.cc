#include "ui/lesson_renderer.h"

#include <gtest/gtest.h>

#include <gtkmm.h>

#include <vector>

using namespace std;

namespace {

// 数一个容器下面所有后代控件，用来确认块真的被渲染成了控件树。
int count_descendants(Gtk::Widget& root) {
    int total = 0;
    for (Gtk::Widget* child = root.get_first_child(); child != nullptr;
         child = child->get_next_sibling()) {
        total += 1 + count_descendants(*child);
    }
    return total;
}

LessonBlock make(const string& type) {
    LessonBlock block;
    block.type = type;
    return block;
}

}  // namespace

// GTK 由 gtk_resource_test.cc 的 main 统一初始化（一个可执行文件一份），
// 这里不再自己来一遍。

TEST(LessonRendererTest, RendersEveryBlockTypeWithoutFiguresRegistered) {
    LessonDoc doc;
    doc.blocks.push_back(make("lead"));
    doc.blocks.push_back(make("prose"));
    LessonBlock bullets = make("bullets");
    bullets.items = {"一", "二"};
    doc.blocks.push_back(bullets);
    doc.blocks.push_back(make("code"));
    LessonBlock steps = make("steps");
    steps.items = {"第一步"};
    doc.blocks.push_back(steps);
    LessonBlock table = make("table");
    table.head = {"列一", "列二"};
    table.rows = {{"a", "!b"}};
    doc.blocks.push_back(table);

    Gtk::Box host(Gtk::Orientation::VERTICAL);
    LessonRenderer().render(host, doc);
    EXPECT_GT(count_descendants(host), 6);
}

TEST(LessonRendererTest, RecursesIntoSectionsAndCallouts) {
    LessonBlock inner = make("prose");
    inner.text = "最里层";
    LessonBlock callout = make("callout");
    callout.kind = "trap";
    callout.blocks = {inner};
    LessonBlock section = make("section");
    section.title = "小节";
    section.blocks = {callout};

    LessonDoc doc;
    doc.blocks = {section};

    Gtk::Box host(Gtk::Orientation::VERTICAL);
    LessonRenderer().render(host, doc);
    // 嵌套三层都要落到控件树上，不能只渲染最外层。
    EXPECT_GT(count_descendants(host), 4);
}

TEST(LessonRendererTest, UsesRegisteredFigureAndKeepsCaption) {
    LessonBlock figure = make("figure");
    figure.id = "demo";
    figure.caption = "图注";
    LessonDoc doc;
    doc.blocks = {figure};

    Gtk::Label drawn("我是图");
    string asked;
    LessonRenderer renderer([&](const string& id) -> Gtk::Widget* {
        asked = id;
        return &drawn;
    });

    Gtk::Box host(Gtk::Orientation::VERTICAL);
    renderer.render(host, doc);
    EXPECT_EQ(asked, "demo");
    EXPECT_EQ(drawn.get_parent(), &host);
}

TEST(LessonRendererTest, UnknownBlockTypeIsVisibleNotSilent) {
    // 渲染器不认识的块必须看得见——静默跳过会让一段内容凭空消失。
    LessonDoc doc;
    doc.blocks = {make("no_such_block")};

    Gtk::Box host(Gtk::Orientation::VERTICAL);
    LessonRenderer().render(host, doc);
    ASSERT_NE(host.get_first_child(), nullptr);
    auto* label = dynamic_cast<Gtk::Label*>(host.get_first_child());
    ASSERT_NE(label, nullptr);
    // 取成 std::string 再找：Glib::ustring::npos 没有定义体，取它的地址链接不过。
    const string shown = label->get_text().raw();
    EXPECT_NE(shown.find("no_such_block"), string::npos);
}
