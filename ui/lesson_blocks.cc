#include "lesson_blocks.h"

#include <stdexcept>

using namespace std;

namespace lesson {
namespace {

// 每次实例化都重新加载模板：Builder 析构后，已经 append 进容器的控件由父
// 容器持有，不会被回收。
Glib::RefPtr<Gtk::Builder> load() {
    return Gtk::Builder::create_from_resource("/app/lesson_blocks.ui");
}

template <typename T>
T& take(const Glib::RefPtr<Gtk::Builder>& builder, const char* id) {
    auto* widget = builder->get_widget<T>(id);
    if (!widget) {
        throw runtime_error(string("lesson block not found in template: ") + id);
    }
    return *widget;
}

const char* callout_style(CalloutKind kind) {
    switch (kind) {
    case CalloutKind::Why:
        return "lesson-callout-why";
    case CalloutKind::Key:
        return "lesson-callout-key";
    case CalloutKind::Note:
        return "lesson-callout-note";
    case CalloutKind::Trap:
        return "lesson-callout-trap";
    case CalloutKind::Use:
        return "lesson-callout-use";
    }
    return "lesson-callout-note";
}

} // namespace

Gtk::Box& section(Gtk::Box& host, const string& title) {
    const auto builder = load();
    auto& frame = take<Gtk::Frame>(builder, "lesson_section");
    auto& body = take<Gtk::Box>(builder, "lesson_section_body");
    frame.set_label(title);
    host.append(frame);
    return body;
}

Gtk::Box& callout(Gtk::Box& host, CalloutKind kind, const string& title) {
    const auto builder = load();
    auto& root = take<Gtk::Box>(builder, "lesson_callout");
    auto& heading = take<Gtk::Label>(builder, "lesson_callout_title");
    auto& body = take<Gtk::Box>(builder, "lesson_callout_body");
    root.add_css_class(callout_style(kind));
    heading.set_text(title);
    heading.set_visible(!title.empty());
    host.append(root);
    return body;
}

Gtk::Label& prose(Gtk::Box& host, const string& text) {
    const auto builder = load();
    auto& label = take<Gtk::Label>(builder, "lesson_prose");
    label.set_text(text);
    host.append(label);
    return label;
}

void bullets(Gtk::Box& host, const vector<string>& items) {
    for (const auto& item : items) {
        prose(host, "· " + item);
    }
}

void figure(
    Gtk::Box& host,
    const string& resource_path,
    int height,
    const string& caption) {
    const auto builder = load();
    auto& root = take<Gtk::Box>(builder, "lesson_figure");
    auto& image = take<Gtk::Picture>(builder, "lesson_figure_image");
    auto& note = take<Gtk::Label>(builder, "lesson_figure_caption");
    image.set_resource(resource_path);
    image.set_size_request(-1, height);
    note.set_text(caption);
    note.set_visible(!caption.empty());
    host.append(root);
}

} // namespace lesson
