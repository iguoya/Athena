#include "document_view.h"

#include <gtksourceview/gtksource.h>

#include <algorithm>
#include <iostream>
#include <utility>

using namespace std;

namespace {

string plain_text(const vector<DocInline>& inlines) {
    string text;
    for (const auto& item : inlines) {
        text += item.text;
        text += plain_text(item.children);
    }
    return text;
}

bool contains_emphasis(const DocInline& item) {
    if (item.kind == DocInlineKind::Emphasis) {
        return true;
    }
    return any_of(
        item.children.begin(), item.children.end(), contains_emphasis);
}

Gtk::TextView* make_code_view(const string& text, const string& language) {
    auto buffer = gtk_source_buffer_new(nullptr);
    auto manager = gtk_source_language_manager_get_default();
    const char* language_id =
        language == "cpp" || language == "c++" || language == "cxx"
        ? "cpp"
        : nullptr;
    if (language_id) {
        gtk_source_buffer_set_language(
            buffer, gtk_source_language_manager_get_language(manager, language_id));
    }
    gtk_source_buffer_set_highlight_syntax(buffer, true);
    gtk_text_buffer_set_text(GTK_TEXT_BUFFER(buffer), text.c_str(), -1);

    auto view = GTK_SOURCE_VIEW(gtk_source_view_new_with_buffer(buffer));
    g_object_unref(buffer);
    gtk_text_view_set_editable(GTK_TEXT_VIEW(view), false);
    gtk_text_view_set_cursor_visible(GTK_TEXT_VIEW(view), false);
    gtk_text_view_set_monospace(GTK_TEXT_VIEW(view), true);
    gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(view), GTK_WRAP_NONE);
    return Glib::wrap(GTK_TEXT_VIEW(view));
}

} // namespace

DocumentView::DocumentView(string resource_base)
    : m_resource_base(std::move(resource_base)) {
    m_scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    m_scrolled->set_hexpand(true);
    m_scrolled->set_vexpand(true);
    m_scrolled->set_policy(Gtk::PolicyType::NEVER, Gtk::PolicyType::AUTOMATIC);

    m_content = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 14);
    m_content->set_hexpand(true);
    m_content->set_margin_top(20);
    m_content->set_margin_bottom(28);
    m_content->set_margin_start(28);
    m_content->set_margin_end(28);
    m_content->add_css_class("document-content");
    m_scrolled->set_child(*m_content);
}

Gtk::Widget& DocumentView::widget() const {
    return *m_scrolled;
}

void DocumentView::set_markdown(const string& markdown) {
    set_document(parse_document_blocks(markdown));
}

void DocumentView::set_heading_actions(
    map<string, vector<HeadingAction>> actions) {
    m_heading_actions = std::move(actions);
}

void DocumentView::set_section_extensions(
    map<string, vector<SectionExtension>> extensions) {
    m_section_extensions = std::move(extensions);
}

void DocumentView::set_document(const DocModel& document) {
    while (auto* child = m_content->get_first_child()) {
        m_content->remove(*child);
    }
    m_headings.clear();
    string active_heading;
    auto append_extensions = [this](const string& heading) {
        const auto found = m_section_extensions.find(heading);
        if (found == m_section_extensions.end()) {
            return;
        }
        for (const auto& extension : found->second) {
            if (auto* widget = extension()) {
                m_content->append(*widget);
            }
        }
    };
    for (const auto& block : document.blocks) {
        if (block.kind == DocBlockKind::Heading) {
            append_extensions(active_heading);
            active_heading = plain_text(block.inlines);
        }
        append_block(block, *m_content, 0);
    }
    append_extensions(active_heading);
    m_scrolled->get_vadjustment()->set_value(0.0);
}

size_t DocumentView::heading_count() const {
    return m_headings.size();
}

void DocumentView::scroll_to_heading(size_t index) {
    if (index >= m_headings.size()) {
        return;
    }
    auto* heading = m_headings[index];
    heading->set_focusable(true);
    heading->grab_focus();
}

void DocumentView::append_block(
    const DocBlock& block, Gtk::Box& target, unsigned list_depth) {
    if (auto* widget = render_block(block, list_depth)) {
        target.append(*widget);
    }
}

Gtk::Widget* DocumentView::render_children(
    const vector<DocBlock>& blocks, unsigned list_depth) {
    auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 8);
    for (const auto& block : blocks) {
        append_block(block, *box, list_depth);
    }
    return box;
}

Gtk::Widget* DocumentView::render_block(const DocBlock& block, unsigned list_depth) {
    switch (block.kind) {
    case DocBlockKind::Heading: {
        auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 12);
        row->set_hexpand(true);
        auto label = Gtk::make_managed<Gtk::Label>();
        label->set_markup(render_inlines(block.inlines));
        label->set_halign(Gtk::Align::START);
        label->set_xalign(0.0F);
        label->set_wrap(true);
        label->add_css_class("document-heading-" + to_string(block.level));
        label->set_margin_top(block.level == 1 ? 6 : 16);
        label->set_hexpand(true);
        row->append(*label);
        const auto found = m_heading_actions.find(plain_text(block.inlines));
        if (found != m_heading_actions.end()) {
            for (const auto& action : found->second) {
                auto button = Gtk::make_managed<Gtk::Button>(action.label);
                button->add_css_class("btn-primary");
                button->set_valign(Gtk::Align::CENTER);
                button->signal_clicked().connect(action.activate);
                row->append(*button);
            }
        }
        m_headings.push_back(row);
        return row;
    }
    case DocBlockKind::Paragraph: {
        auto label = Gtk::make_managed<Gtk::Label>();
        label->set_markup(render_inlines(block.inlines));
        label->set_halign(Gtk::Align::START);
        label->set_xalign(0.0F);
        label->set_wrap(true);
        label->set_wrap_mode(Pango::WrapMode::WORD_CHAR);
        label->set_selectable(true);
        label->add_css_class("document-paragraph");
        label->signal_activate_link().connect([](const string& uri) {
            auto launcher = gtk_uri_launcher_new(uri.c_str());
            gtk_uri_launcher_launch(
                launcher,
                nullptr,
                nullptr,
                [](GObject*, GAsyncResult* result, gpointer user_data) {
                    auto* completed = GTK_URI_LAUNCHER(user_data);
                    GError* error = nullptr;
                    if (!gtk_uri_launcher_launch_finish(completed, result, &error)
                        && error) {
                        cerr << "Failed to open external link: "
                             << error->message << endl;
                        g_error_free(error);
                    }
                    g_object_unref(completed);
                },
                launcher);
            return true;
        }, false);
        return label;
    }
    case DocBlockKind::CodeBlock: {
        auto frame = Gtk::make_managed<Gtk::Frame>();
        frame->add_css_class("document-code-frame");
        auto scroll = Gtk::make_managed<Gtk::ScrolledWindow>();
        scroll->set_policy(Gtk::PolicyType::AUTOMATIC, Gtk::PolicyType::AUTOMATIC);
        scroll->set_min_content_height(120);
        auto* view = make_code_view(block.text, block.language);
        view->add_css_class("document-code");
        scroll->set_child(*view);
        frame->set_child(*scroll);
        return frame;
    }
    case DocBlockKind::BulletList:
    case DocBlockKind::OrderedList: {
        auto list = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 6);
        list->set_margin_start(static_cast<int>(list_depth) * 20);
        list->add_css_class("document-list");
        unsigned number = block.ordered_start;
        for (const auto& item : block.children) {
            auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 8);
            auto marker = Gtk::make_managed<Gtk::Label>(
                block.kind == DocBlockKind::OrderedList
                    ? to_string(number++) + "."
                    : "•");
            marker->set_valign(Gtk::Align::START);
            marker->add_css_class("document-list-marker");
            row->append(*marker);
            auto* contents = render_children(item.children, list_depth + 1);
            contents->set_hexpand(true);
            row->append(*contents);
            list->append(*row);
        }
        return list;
    }
    case DocBlockKind::BlockQuote: {
        auto frame = Gtk::make_managed<Gtk::Frame>();
        frame->add_css_class("document-quote");
        frame->set_child(*render_children(block.children, list_depth));
        return frame;
    }
    case DocBlockKind::Table: {
        auto grid = Gtk::make_managed<Gtk::Grid>();
        grid->set_row_spacing(1);
        grid->set_column_spacing(1);
        grid->add_css_class("document-table");
        auto append_row = [this, &grid](
                              const vector<DocTableCell>& row,
                              int y,
                              bool header) {
            for (size_t x = 0; x < row.size(); ++x) {
                auto label = Gtk::make_managed<Gtk::Label>();
                label->set_markup(render_inlines(row[x].inlines));
                label->set_halign(Gtk::Align::START);
                label->set_xalign(0.0F);
                label->set_wrap(true);
                label->set_hexpand(true);
                label->set_margin_top(7);
                label->set_margin_bottom(7);
                label->set_margin_start(10);
                label->set_margin_end(10);
                label->add_css_class(header ? "document-table-header" : "document-table-cell");
                grid->attach(*label, static_cast<int>(x), y, 1, 1);
            }
        };
        if (!block.table_header.empty()) {
            append_row(block.table_header, 0, true);
        }
        const int first_row = block.table_header.empty() ? 0 : 1;
        for (size_t i = 0; i < block.table_rows.size(); ++i) {
            append_row(block.table_rows[i], first_row + static_cast<int>(i), false);
        }
        return grid;
    }
    case DocBlockKind::Image: {
        auto picture = Gtk::make_managed<Gtk::Picture>();
        picture->set_can_shrink(true);
        picture->set_content_fit(Gtk::ContentFit::CONTAIN);
        picture->set_halign(Gtk::Align::CENTER);
        picture->set_size_request(-1, 300);
        picture->set_resource(m_resource_base + block.image_path);
        picture->set_tooltip_text(block.image_alt);
        picture->add_css_class("document-image");
        return picture;
    }
    case DocBlockKind::ThematicBreak: {
        auto separator = Gtk::make_managed<Gtk::Separator>(Gtk::Orientation::HORIZONTAL);
        separator->set_margin_top(8);
        separator->set_margin_bottom(8);
        return separator;
    }
    case DocBlockKind::ListItem:
        return render_children(block.children, list_depth);
    }
    return nullptr;
}

string DocumentView::render_inlines(const vector<DocInline>& inlines) const {
    string markup;
    for (const auto& item : inlines) {
        markup += render_inline(item);
    }
    return markup;
}

string DocumentView::render_inline(const DocInline& item, bool danger) const {
    const string children = [&]() {
        string markup;
        for (const auto& child : item.children) {
            markup += render_inline(child, danger || item.kind == DocInlineKind::Strong);
        }
        return markup;
    }();
    switch (item.kind) {
    case DocInlineKind::Text:
        return Glib::Markup::escape_text(item.text);
    case DocInlineKind::Code:
        return "<tt>" + Glib::Markup::escape_text(item.text) + "</tt>";
    case DocInlineKind::Emphasis:
        return danger ? "<span foreground='#dc3545'><i>" + children + "</i></span>"
                      : "<i>" + children + "</i>";
    case DocInlineKind::Strong:
        return "<span foreground='" + string(contains_emphasis(item) ? "#dc3545" : "#b45309")
            + "' weight='bold'>" + children + "</span>";
    case DocInlineKind::Link:
        return "<a href='" + Glib::Markup::escape_text(item.href)
            + "'>" + children + "</a>";
    case DocInlineKind::Image:
        return Glib::Markup::escape_text(item.text);
    case DocInlineKind::SoftBreak:
        return " ";
    case DocInlineKind::LineBreak:
        return "\n";
    }
    return {};
}
