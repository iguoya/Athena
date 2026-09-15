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

void code(Gtk::Box& host, const string& text, const string& caption) {
    const auto builder = load();
    auto& root = take<Gtk::Box>(builder, "lesson_code");
    auto& body = take<Gtk::Label>(builder, "lesson_code_text");
    auto& note = take<Gtk::Label>(builder, "lesson_code_caption");
    body.set_text(text);
    note.set_text(caption);
    note.set_visible(!caption.empty());
    host.append(root);
}

void table(
    Gtk::Box& host,
    const vector<string>& head,
    const vector<vector<string>>& rows,
    const string& note) {
    const auto builder = load();
    auto& root = take<Gtk::Box>(builder, "lesson_table");
    auto& grid = take<Gtk::Grid>(builder, "lesson_table_grid");
    auto& footer = take<Gtk::Label>(builder, "lesson_table_note");

    // 行列数来自数据，格子只能由代码填（AGENTS.md GTK 规则第 2 条）；
    // 单元格本身仍然是模板实例，不在这里拼属性。
    const auto cell = [&grid](const string& text, int column, int row,
                              const char* extra) {
        const auto cell_builder = load();
        auto& label = take<Gtk::Label>(cell_builder, "lesson_table_cell");
        // 「!」前缀表示这格是判定，用强调配色。
        const bool verdict = !text.empty() && text.front() == '!';
        label.set_text(verdict ? text.substr(1) : text);
        if (verdict) {
            label.add_css_class("figure-verdict");
        }
        if (extra != nullptr) {
            label.add_css_class(extra);
        }
        grid.attach(label, column, row);
    };

    int row_index = 0;
    if (!head.empty()) {
        for (size_t column = 0; column < head.size(); ++column) {
            cell(head[column], static_cast<int>(column), row_index, "figure-head");
        }
        ++row_index;
    }
    for (const auto& row : rows) {
        for (size_t column = 0; column < row.size(); ++column) {
            cell(row[column], static_cast<int>(column), row_index, nullptr);
        }
        ++row_index;
    }

    footer.set_text(note);
    footer.set_visible(!note.empty());
    host.append(root);
}

void steps(Gtk::Box& host, const vector<string>& items) {
    for (size_t index = 0; index < items.size(); ++index) {
        const auto builder = load();
        auto& root = take<Gtk::Box>(builder, "lesson_step");
        auto& number = take<Gtk::Label>(builder, "lesson_step_index");
        auto& text = take<Gtk::Label>(builder, "lesson_step_text");
        number.set_text(to_string(index + 1));
        text.set_text(items[index]);
        host.append(root);
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
