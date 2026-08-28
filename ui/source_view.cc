#include "source_view.h"

#include "content/source_locator.h"

#include <glib.h>

void display_project_source(
    GtkSourceView* source_view,
    const ContentLoader& content_loader,
    const string& relative_path,
    const string& member_name) {
    if (!source_view) {
        return;
    }

    string source_text;
    if (!relative_path.empty()) {
        source_text = content_loader.load_project_file(relative_path);
    }
    if (source_text.empty()) {
        source_text = relative_path.empty()
            ? "该知识点尚未添加实验源码。"
            : "无法读取源文件：" + relative_path;
    }

    auto source_buffer = GTK_SOURCE_BUFFER(
        gtk_text_view_get_buffer(GTK_TEXT_VIEW(source_view)));
    auto language_manager = gtk_source_language_manager_get_default();
    auto cpp_language = gtk_source_language_manager_get_language(
        language_manager, "cpp");
    if (cpp_language) {
        gtk_source_buffer_set_language(source_buffer, cpp_language);
    }
    gtk_source_buffer_set_highlight_syntax(source_buffer, true);
    gtk_source_buffer_set_highlight_matching_brackets(source_buffer, true);

    auto scheme_manager = gtk_source_style_scheme_manager_get_default();
    auto scheme = gtk_source_style_scheme_manager_get_scheme(
        scheme_manager, "Adwaita");
    if (scheme) {
        gtk_source_buffer_set_style_scheme(source_buffer, scheme);
    }

    auto text_buffer = GTK_TEXT_BUFFER(source_buffer);
    gtk_text_buffer_set_text(
        text_buffer, source_text.c_str(), static_cast<int>(source_text.size()));

    GtkTextIter source_begin;
    gtk_text_buffer_get_start_iter(text_buffer, &source_begin);
    gtk_text_buffer_place_cursor(text_buffer, &source_begin);

    const auto source_range = locate_cpp_member_function(source_text, member_name);
    if (!source_range) {
        return;
    }

    GtkTextIter highlight_begin;
    GtkTextIter highlight_end;
    gtk_text_buffer_get_iter_at_offset(
        text_buffer,
        &highlight_begin,
        static_cast<int>(g_utf8_pointer_to_offset(
            source_text.c_str(), source_text.c_str() + source_range->begin)));
    gtk_text_buffer_get_iter_at_offset(
        text_buffer,
        &highlight_end,
        static_cast<int>(g_utf8_pointer_to_offset(
            source_text.c_str(), source_text.c_str() + source_range->end)));

    auto tag_table = gtk_text_buffer_get_tag_table(text_buffer);
    auto highlight_tag = gtk_text_tag_table_lookup(
        tag_table, "athena-topic-highlight");
    if (!highlight_tag) {
        highlight_tag = gtk_text_buffer_create_tag(
            text_buffer,
            "athena-topic-highlight",
            "background",
            "#dbeafe",
            nullptr);
    }
    gtk_text_buffer_apply_tag(
        text_buffer, highlight_tag, &highlight_begin, &highlight_end);
    gtk_text_buffer_place_cursor(text_buffer, &highlight_begin);
    gtk_text_view_scroll_to_mark(
        GTK_TEXT_VIEW(source_view),
        gtk_text_buffer_get_insert(text_buffer),
        0.15,
        true,
        0.0,
        0.20);
}
