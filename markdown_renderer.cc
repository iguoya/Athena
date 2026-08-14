#include "markdown_renderer.h"

#include <md4c.h>
#include <md4c-html.h>

#include <algorithm>
#include <climits>
#include <stdexcept>
#include <string_view>

using namespace std;

namespace {

struct ListState {
    bool ordered = false;
    unsigned next_number = 1;
};

struct RenderState {
    GtkTextBuffer* buffer = nullptr;
    vector<string> active_tags;
    vector<ListState> lists;
    vector<MarkdownHeading> headings;
    string heading_text;
    string tail;
    unsigned heading_level = 0;
    int heading_offset = 0;
    bool in_code_block = false;
    bool failed = false;
};

struct HtmlRenderState {
    string body;
    bool failed = false;
};

void create_tags(GtkTextBuffer* buffer) {
    gtk_text_buffer_create_tag(
        buffer,
        "md-h1",
        "weight", PANGO_WEIGHT_BOLD,
        "scale", 1.75,
        "foreground", "#212529",
        "pixels-above-lines", 20,
        "pixels-below-lines", 12,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-h2",
        "weight", PANGO_WEIGHT_BOLD,
        "scale", 1.50,
        "foreground", "#212529",
        "pixels-above-lines", 18,
        "pixels-below-lines", 10,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-h3",
        "weight", PANGO_WEIGHT_BOLD,
        "scale", 1.25,
        "foreground", "#212529",
        "pixels-above-lines", 14,
        "pixels-below-lines", 8,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-h4",
        "weight", PANGO_WEIGHT_BOLD,
        "scale", 1.12,
        "foreground", "#212529",
        "pixels-above-lines", 12,
        "pixels-below-lines", 6,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-bold",
        "weight", PANGO_WEIGHT_BOLD,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-emphasis",
        "style", PANGO_STYLE_ITALIC,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-inline-code",
        "family", "monospace",
        "background", "#eef1f4",
        "foreground", "#b42318",
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-code-block",
        "family", "monospace",
        "background", "#f1f3f5",
        "foreground", "#212529",
        "left-margin", 20,
        "right-margin", 20,
        "pixels-above-lines", 5,
        "pixels-below-lines", 5,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-quote",
        "style", PANGO_STYLE_ITALIC,
        "foreground", "#495057",
        "background", "#f8f9fa",
        "left-margin", 24,
        "right-margin", 16,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-link",
        "foreground", "#0a58ca",
        "underline", PANGO_UNDERLINE_SINGLE,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-delete",
        "strikethrough", TRUE,
        nullptr);
    gtk_text_buffer_create_tag(
        buffer,
        "md-table-header",
        "weight", PANGO_WEIGHT_BOLD,
        "background", "#f1f3f5",
        nullptr);
}

int end_offset(const RenderState& state) {
    return gtk_text_buffer_get_char_count(state.buffer);
}

bool is_empty(const RenderState& state) {
    return end_offset(state) == 0;
}

void insert_text(RenderState& state, string_view text) {
    if (text.empty()) {
        return;
    }

    const int start_offset = end_offset(state);
    GtkTextIter end;
    gtk_text_buffer_get_end_iter(state.buffer, &end);
    gtk_text_buffer_insert(
        state.buffer,
        &end,
        text.data(),
        static_cast<int>(text.size()));

    const int finish_offset = end_offset(state);
    GtkTextIter start;
    GtkTextIter finish;
    gtk_text_buffer_get_iter_at_offset(state.buffer, &start, start_offset);
    gtk_text_buffer_get_iter_at_offset(state.buffer, &finish, finish_offset);
    for (const auto& tag : state.active_tags) {
        gtk_text_buffer_apply_tag_by_name(
            state.buffer,
            tag.c_str(),
            &start,
            &finish);
    }

    state.tail.append(text);
    if (state.tail.size() > 2) {
        state.tail.erase(0, state.tail.size() - 2);
    }

    if (state.heading_level > 0) {
        state.heading_text.append(text);
    }
}

void ensure_blank_line(RenderState& state) {
    if (is_empty(state)) {
        return;
    }

    if (state.tail.ends_with("\n\n")) {
        return;
    }
    if (state.tail.ends_with('\n')) {
        insert_text(state, "\n");
    } else {
        insert_text(state, "\n\n");
    }
}

void push_tag(RenderState& state, string tag) {
    state.active_tags.emplace_back(tag);
}

void pop_tag(RenderState& state, string_view tag) {
    auto found = find(state.active_tags.rbegin(), state.active_tags.rend(), tag);
    if (found != state.active_tags.rend()) {
        state.active_tags.erase(next(found).base());
    }
}

string heading_tag(unsigned level) {
    return "md-h" + to_string(min(level, 4u));
}

string trim_heading(string text) {
    while (!text.empty() && (text.back() == '\n' || text.back() == ' ')) {
        text.pop_back();
    }
    while (!text.empty() && text.front() == ' ') {
        text.erase(text.begin());
    }
    return text;
}

string heading_anchor(size_t index) {
    return "athena-heading-" + to_string(index);
}

string add_heading_anchors(string html) {
    size_t search_from = 0;
    size_t heading_index = 0;
    while (true) {
        const size_t position = html.find("<h", search_from);
        if (position == string::npos) {
            break;
        }

        if (position + 3 < html.size() &&
            html[position + 2] >= '1' && html[position + 2] <= '6' &&
            html[position + 3] == '>') {
            const string attribute =
                " id=\"" + heading_anchor(heading_index++) + "\"";
            html.insert(position + 3, attribute);
            search_from = position + 3 + attribute.size();
        } else {
            search_from = position + 2;
        }
    }
    return html;
}

void append_html(const MD_CHAR* text, MD_SIZE size, void* userdata) noexcept {
    auto& state = *static_cast<HtmlRenderState*>(userdata);
    try {
        state.body.append(text, size);
    } catch (...) {
        state.failed = true;
    }
}

int enter_block_impl(MD_BLOCKTYPE type, void* detail, RenderState& state) {
    switch (type) {
    case MD_BLOCK_QUOTE:
        ensure_blank_line(state);
        push_tag(state, "md-quote");
        insert_text(state, "提示：");
        break;
    case MD_BLOCK_UL:
        state.lists.push_back({false, 1});
        break;
    case MD_BLOCK_OL: {
        const auto* ordered = static_cast<const MD_BLOCK_OL_DETAIL*>(detail);
        state.lists.push_back({true, ordered ? ordered->start : 1});
        break;
    }
    case MD_BLOCK_LI: {
        if (!is_empty(state) && !state.tail.ends_with('\n')) {
            insert_text(state, "\n");
        }
        const string indent(state.lists.empty() ? 0 : (state.lists.size() - 1) * 2, ' ');
        string prefix = indent + "• ";
        if (!state.lists.empty() && state.lists.back().ordered) {
            prefix = indent + to_string(state.lists.back().next_number++) + ". ";
        }
        const auto* item = static_cast<const MD_BLOCK_LI_DETAIL*>(detail);
        if (item && item->is_task) {
            prefix += item->task_mark == 'x' || item->task_mark == 'X' ? "☑ " : "☐ ";
        }
        insert_text(state, prefix);
        break;
    }
    case MD_BLOCK_H: {
        ensure_blank_line(state);
        const auto* heading = static_cast<const MD_BLOCK_H_DETAIL*>(detail);
        state.heading_level = heading ? heading->level : 1;
        state.heading_offset = end_offset(state);
        state.heading_text.clear();
        push_tag(state, heading_tag(state.heading_level));
        break;
    }
    case MD_BLOCK_CODE:
        ensure_blank_line(state);
        state.in_code_block = true;
        push_tag(state, "md-code-block");
        break;
    case MD_BLOCK_P:
        ensure_blank_line(state);
        break;
    case MD_BLOCK_TABLE:
        ensure_blank_line(state);
        break;
    case MD_BLOCK_TH:
        push_tag(state, "md-table-header");
        break;
    default:
        break;
    }
    return 0;
}

int leave_block_impl(MD_BLOCKTYPE type, void*, RenderState& state) {
    switch (type) {
    case MD_BLOCK_QUOTE:
        pop_tag(state, "md-quote");
        ensure_blank_line(state);
        break;
    case MD_BLOCK_UL:
    case MD_BLOCK_OL:
        if (!state.lists.empty()) {
            state.lists.pop_back();
        }
        ensure_blank_line(state);
        break;
    case MD_BLOCK_LI:
        insert_text(state, "\n");
        break;
    case MD_BLOCK_H: {
        pop_tag(state, heading_tag(state.heading_level));
        const string title = trim_heading(state.heading_text);
        if (!title.empty()) {
            state.headings.push_back({
                title,
                heading_anchor(state.headings.size()),
                state.heading_level,
                state.heading_offset});
        }
        state.heading_level = 0;
        state.heading_text.clear();
        insert_text(state, "\n\n");
        break;
    }
    case MD_BLOCK_CODE:
        pop_tag(state, "md-code-block");
        state.in_code_block = false;
        ensure_blank_line(state);
        break;
    case MD_BLOCK_P:
        ensure_blank_line(state);
        break;
    case MD_BLOCK_HR:
        insert_text(state, "────────────────────────────────\n\n");
        break;
    case MD_BLOCK_TR:
        insert_text(state, "\n");
        break;
    case MD_BLOCK_TH:
        pop_tag(state, "md-table-header");
        insert_text(state, "  │  ");
        break;
    case MD_BLOCK_TD:
        insert_text(state, "  │  ");
        break;
    case MD_BLOCK_TABLE:
        ensure_blank_line(state);
        break;
    default:
        break;
    }
    return 0;
}

int enter_span_impl(MD_SPANTYPE type, void*, RenderState& state) {
    switch (type) {
    case MD_SPAN_EM:
        push_tag(state, "md-emphasis");
        break;
    case MD_SPAN_STRONG:
        push_tag(state, "md-bold");
        break;
    case MD_SPAN_A:
        push_tag(state, "md-link");
        break;
    case MD_SPAN_CODE:
        push_tag(state, "md-inline-code");
        break;
    case MD_SPAN_DEL:
        push_tag(state, "md-delete");
        break;
    default:
        break;
    }
    return 0;
}

int leave_span_impl(MD_SPANTYPE type, void*, RenderState& state) {
    switch (type) {
    case MD_SPAN_EM:
        pop_tag(state, "md-emphasis");
        break;
    case MD_SPAN_STRONG:
        pop_tag(state, "md-bold");
        break;
    case MD_SPAN_A:
        pop_tag(state, "md-link");
        break;
    case MD_SPAN_CODE:
        pop_tag(state, "md-inline-code");
        break;
    case MD_SPAN_DEL:
        pop_tag(state, "md-delete");
        break;
    default:
        break;
    }
    return 0;
}

int text_impl(MD_TEXTTYPE type, const MD_CHAR* text, MD_SIZE size, RenderState& state) {
    switch (type) {
    case MD_TEXT_NULLCHAR:
        insert_text(state, "�");
        break;
    case MD_TEXT_BR:
        insert_text(state, "\n");
        break;
    case MD_TEXT_SOFTBR:
        insert_text(state, state.in_code_block ? "\n" : " ");
        break;
    case MD_TEXT_NORMAL:
    case MD_TEXT_ENTITY:
    case MD_TEXT_CODE:
    case MD_TEXT_HTML:
    case MD_TEXT_LATEXMATH:
        insert_text(state, string_view(text, size));
        break;
    }
    return 0;
}

template <typename Callback>
int safe_callback(void* userdata, Callback&& callback) {
    auto& state = *static_cast<RenderState*>(userdata);
    try {
        return callback(state);
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

int enter_block(MD_BLOCKTYPE type, void* detail, void* userdata) {
    return safe_callback(userdata, [type, detail](RenderState& state) {
        return enter_block_impl(type, detail, state);
    });
}

int leave_block(MD_BLOCKTYPE type, void* detail, void* userdata) {
    return safe_callback(userdata, [type, detail](RenderState& state) {
        return leave_block_impl(type, detail, state);
    });
}

int enter_span(MD_SPANTYPE type, void* detail, void* userdata) {
    return safe_callback(userdata, [type, detail](RenderState& state) {
        return enter_span_impl(type, detail, state);
    });
}

int leave_span(MD_SPANTYPE type, void* detail, void* userdata) {
    return safe_callback(userdata, [type, detail](RenderState& state) {
        return leave_span_impl(type, detail, state);
    });
}

int text_callback(
    MD_TEXTTYPE type,
    const MD_CHAR* text,
    MD_SIZE size,
    void* userdata) {
    return safe_callback(userdata, [type, text, size](RenderState& state) {
        return text_impl(type, text, size, state);
    });
}

} // namespace

vector<MarkdownHeading> render_markdown(
    Gtk::TextView& text_view,
    const string& markdown) {
    if (markdown.size() > UINT_MAX) {
        throw runtime_error("Markdown document is too large");
    }

    auto buffer = text_view.get_buffer();
    buffer->set_text("");
    create_tags(buffer->gobj());

    RenderState state;
    state.buffer = buffer->gobj();

    MD_PARSER parser{};
    parser.flags = MD_DIALECT_GITHUB | MD_FLAG_NOHTML;
    parser.enter_block = enter_block;
    parser.leave_block = leave_block;
    parser.enter_span = enter_span;
    parser.leave_span = leave_span;
    parser.text = text_callback;

    const int result = md_parse(
        markdown.data(),
        static_cast<MD_SIZE>(markdown.size()),
        &parser,
        &state);
    if (result != 0 || state.failed) {
        throw runtime_error("Failed to parse Markdown document");
    }

    auto begin = buffer->begin();
    buffer->place_cursor(begin);
    return state.headings;
}

string render_markdown_html(
    const string& markdown,
    const string& stylesheet) {
    if (markdown.size() > UINT_MAX) {
        throw runtime_error("Markdown document is too large");
    }

    HtmlRenderState state;
    const int result = md_html(
        markdown.data(),
        static_cast<MD_SIZE>(markdown.size()),
        append_html,
        &state,
        MD_DIALECT_GITHUB | MD_FLAG_NOHTML,
        MD_HTML_FLAG_SKIP_UTF8_BOM);
    if (result != 0 || state.failed) {
        throw runtime_error("Failed to convert Markdown to HTML");
    }

    const string body = add_heading_anchors(std::move(state.body));
    return
        "<!doctype html>\n"
        "<html lang=\"zh-CN\">\n"
        "<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta http-equiv=\"Content-Security-Policy\" "
        "content=\"default-src 'none'; img-src file: data:; "
        "style-src 'unsafe-inline'; font-src file: data:;\">\n"
        "<style>\n" + stylesheet + "\n</style>\n"
        "</head>\n"
        "<body><main class=\"athena-article\">\n" + body +
        "\n</main></body>\n"
        "</html>\n";
}
