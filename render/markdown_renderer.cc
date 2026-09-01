#include "markdown_renderer.h"

#include "cpp_syntax_highlighter.h"

#include <md4c-html.h>
#include <md4c.h>

#include <algorithm>
#include <climits>
#include <map>
#include <regex>
#include <stdexcept>
#include <utility>

using namespace std;

namespace {

struct HeadingState {
    vector<MarkdownHeading> headings;
    string text;
    unsigned level = 0;
    bool failed = false;
};

struct HtmlState {
    string body;
    bool failed = false;
};

string heading_anchor(size_t index) {
    return "athena-heading-" + to_string(index);
}

string normalize_heading(string text) {
    for (char& character : text) {
        if (character == '\n' || character == '\r' || character == '\t') {
            character = ' ';
        }
    }

    const auto first = text.find_first_not_of(' ');
    if (first == string::npos) {
        return {};
    }
    const auto last = text.find_last_not_of(' ');
    return text.substr(first, last - first + 1);
}

int enter_block(MD_BLOCKTYPE type, void* detail, void* userdata) noexcept {
    auto& state = *static_cast<HeadingState*>(userdata);
    try {
        if (type == MD_BLOCK_H) {
            state.level = static_cast<MD_BLOCK_H_DETAIL*>(detail)->level;
            state.text.clear();
        }
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

int leave_block(MD_BLOCKTYPE type, void*, void* userdata) noexcept {
    auto& state = *static_cast<HeadingState*>(userdata);
    try {
        if (type == MD_BLOCK_H) {
            state.headings.push_back({
                normalize_heading(std::move(state.text)),
                heading_anchor(state.headings.size()),
                state.level});
            state.level = 0;
            state.text.clear();
        }
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

int collect_heading_text(
    MD_TEXTTYPE type,
    const MD_CHAR* text,
    MD_SIZE size,
    void* userdata) noexcept {
    auto& state = *static_cast<HeadingState*>(userdata);
    if (state.level == 0) {
        return 0;
    }

    try {
        if (type == MD_TEXT_BR || type == MD_TEXT_SOFTBR) {
            state.text += ' ';
        } else {
            state.text.append(text, size);
        }
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

int ignore_span(MD_SPANTYPE, void*, void*) noexcept {
    return 0;
}

void append_html(const MD_CHAR* text, MD_SIZE size, void* userdata) noexcept {
    auto& state = *static_cast<HtmlState*>(userdata);
    try {
        state.body.append(text, size);
    } catch (...) {
        state.failed = true;
    }
}

string base64_encode(const string& data) {
    static constexpr char table[] =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    string out;
    out.reserve((data.size() + 2) / 3 * 4);
    size_t index = 0;
    for (; index + 2 < data.size(); index += 3) {
        const unsigned triple =
            (static_cast<unsigned char>(data[index]) << 16) |
            (static_cast<unsigned char>(data[index + 1]) << 8) |
            static_cast<unsigned char>(data[index + 2]);
        out += table[(triple >> 18) & 63];
        out += table[(triple >> 12) & 63];
        out += table[(triple >> 6) & 63];
        out += table[triple & 63];
    }
    if (index < data.size()) {
        const bool has_second = index + 1 < data.size();
        unsigned triple = static_cast<unsigned char>(data[index]) << 16;
        if (has_second) {
            triple |= static_cast<unsigned char>(data[index + 1]) << 8;
        }
        out += table[(triple >> 18) & 63];
        out += table[(triple >> 12) & 63];
        out += has_second ? table[(triple >> 6) & 63] : '=';
        out += '=';
    }
    return out;
}

string escape_html(const string& text) {
    string escaped;
    escaped.reserve(text.size());
    for (const char character : text) {
        switch (character) {
        case '&': escaped += "&amp;"; break;
        case '<': escaped += "&lt;"; break;
        case '>': escaped += "&gt;"; break;
        case '"': escaped += "&quot;"; break;
        default: escaped += character; break;
        }
    }
    return escaped;
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

// 在匹配小节的正文末尾插入实验入口组。讲解先完整展开，读者形成预测后
// 再进入验证；同一小节的多个实验放在一组里，不重复打断阅读。只在渲染
// 期操作 md_html() 产出的 HTML，不修改 Markdown 原文。
string insert_experiment_links(
    string html,
    const vector<MarkdownHeading>& headings,
    const vector<HeadingExperimentLink>& experiment_links) {
    if (experiment_links.empty()) {
        return html;
    }

    // 一个小节可能同时讲了不止一个知识点（比如 auto/decltype 类型推导
    // 常常放在同一节里对比着讲）——用 vector 而不是覆盖式的单值映射，
    // 否则后一个知识点的卡片会静默吃掉前一个的，界面上却看不出少了
    // 什么，比找不到卡片更容易被忽略。
    map<string, vector<const HeadingExperimentLink*>> link_by_heading;
    for (const auto& link : experiment_links) {
        link_by_heading[link.heading].push_back(&link);
    }

    struct HtmlHeading {
        size_t position;
        unsigned level;
    };
    vector<HtmlHeading> html_headings;

    size_t search_from = 0;
    while (true) {
        const size_t open_pos = html.find("<h", search_from);
        if (open_pos == string::npos) {
            break;
        }
        if (!(open_pos + 3 < html.size() && html[open_pos + 2] >= '1' &&
              html[open_pos + 2] <= '6' && html[open_pos + 3] == '>')) {
            search_from = open_pos + 2;
            continue;
        }

        html_headings.push_back(
            {open_pos, static_cast<unsigned>(html[open_pos + 2] - '0')});
        search_from = open_pos + 4;
    }

    struct Insertion {
        size_t position;
        string html;
    };
    vector<Insertion> insertions;
    const size_t count = min(headings.size(), html_headings.size());
    for (size_t current_index = 0; current_index < count; ++current_index) {
        const auto& heading = headings[current_index];
        const auto found = link_by_heading.find(heading.title);
        if (found == link_by_heading.end()) {
            continue;
        }

        size_t section_end = html.size();
        for (size_t next = current_index + 1; next < html_headings.size(); ++next) {
            if (html_headings[next].level <= html_headings[current_index].level) {
                section_end = html_headings[next].position;
                break;
            }
        }

        string group =
            "\n<section class=\"athena-experiment-group\" "
            "aria-label=\"本节实验\">\n"
            "<div class=\"athena-experiment-group-title\">"
            "讲解完成 · 动手验证</div>\n"
            "<div class=\"athena-experiment-actions\">\n";
        for (const auto* link : found->second) {
            group +=
                "<a class=\"athena-experiment-link\" "
                "href=\"athena://knowledge/" +
                escape_html(link->knowledge_id) + "\">▶ " +
                escape_html(link->label) + "</a>\n";
        }
        group += "</div>\n</section>\n";
        insertions.push_back({section_end, std::move(group)});
    }

    // 从后向前插入，前面记录的 HTML 位置不会因后面的插入而漂移。
    for (auto insertion = insertions.rbegin(); insertion != insertions.rend();
         ++insertion) {
        html.insert(insertion->position, insertion->html);
    }
    return html;
}

string render_html_toc(const vector<MarkdownHeading>& headings) {
    string toc;
    for (const auto& heading : headings) {
        if (heading.title.empty() || heading.level > 3) {
            continue;
        }
        toc +=
            "<a class=\"toc-level-" + to_string(heading.level) +
            "\" href=\"#" + heading.anchor + "\">" +
            escape_html(heading.title) + "</a>\n";
    }
    if (toc.empty()) {
        return {};
    }
    return
        "<aside class=\"article-toc\">\n"
        "<div class=\"article-toc-title\">本文目录</div>\n"
        "<nav>\n" + toc + "</nav>\n"
        "</aside>\n";
}

string reader_toolbar() {
    return R"HTML(
<div class="article-tools" role="toolbar" aria-label="阅读设置">
  <div class="tool-group" aria-label="字体大小">
    <button type="button" data-font="decrease" title="缩小字体">A−</button>
    <button type="button" data-font="reset" title="恢复默认字体">A</button>
    <button type="button" data-font="increase" title="放大字体">A＋</button>
  </div>
  <div class="tool-group" aria-label="主题">
    <button type="button" data-theme-value="auto" title="跟随系统">自动</button>
    <button type="button" data-theme-value="light" title="浅色主题">浅色</button>
    <button type="button" data-theme-value="dark" title="深色主题">深色</button>
  </div>
</div>
)HTML";
}

string reader_script() {
    return R"HTML(
<script>
(() => {
  const root = document.documentElement;
  const storageKey = 'athena-reader-settings';
  let settings = { fontSize: 21, theme: 'auto' };

  try {
    settings = { ...settings, ...JSON.parse(localStorage.getItem(storageKey) || '{}') };
  } catch (_) {}

  const save = () => {
    try { localStorage.setItem(storageKey, JSON.stringify(settings)); } catch (_) {}
  };

  const applyFont = () => {
    // CSS px 按 96dpi 换算：19px ≈ 14.25pt，不能再缩到全局可读基线以下。
    settings.fontSize = Math.max(19, Math.min(26, Number(settings.fontSize) || 21));
    root.style.setProperty('--article-font-size', `${settings.fontSize}px`);
  };

  const applyTheme = () => {
    if (settings.theme === 'light' || settings.theme === 'dark') {
      root.dataset.theme = settings.theme;
    } else {
      settings.theme = 'auto';
      delete root.dataset.theme;
    }
    document.querySelectorAll('[data-theme-value]').forEach(button => {
      const active = button.dataset.themeValue === settings.theme;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
  };

  document.querySelectorAll('[data-font]').forEach(button => {
    button.addEventListener('click', () => {
      if (button.dataset.font === 'increase') settings.fontSize += 1;
      if (button.dataset.font === 'decrease') settings.fontSize -= 1;
      if (button.dataset.font === 'reset') settings.fontSize = 21;
      applyFont();
      save();
    });
  });

  document.querySelectorAll('[data-theme-value]').forEach(button => {
    button.addEventListener('click', () => {
      settings.theme = button.dataset.themeValue;
      applyTheme();
      save();
    });
  });

  applyFont();
  applyTheme();
})();
</script>
)HTML";
}

} // namespace

vector<MarkdownHeading> parse_markdown_headings(const string& markdown) {
    if (markdown.size() > UINT_MAX) {
        throw runtime_error("Markdown document is too large");
    }

    HeadingState state;
    MD_PARSER parser{};
    parser.flags = MD_DIALECT_GITHUB | MD_FLAG_NOHTML;
    parser.enter_block = enter_block;
    parser.leave_block = leave_block;
    parser.enter_span = ignore_span;
    parser.leave_span = ignore_span;
    parser.text = collect_heading_text;

    const int result = md_parse(
        markdown.data(),
        static_cast<MD_SIZE>(markdown.size()),
        &parser,
        &state);
    if (result != 0 || state.failed) {
        throw runtime_error("Failed to parse Markdown headings");
    }
    return state.headings;
}

string inline_markdown_images(
    const string& markdown,
    const function<string(const string&)>& load_relative) {
    // ![说明](路径.svg)，路径不含空白和右括号。
    static const regex image_pattern(R"(!\[([^\]]*)\]\(([^)\s]+\.svg)\))");

    string result;
    result.reserve(markdown.size());
    size_t last = 0;
    const auto end = sregex_iterator();
    for (auto it = sregex_iterator(markdown.begin(), markdown.end(), image_pattern);
         it != end;
         ++it) {
        const smatch& match = *it;
        const size_t position = static_cast<size_t>(match.position());
        result.append(markdown, last, position - last);
        last = position + static_cast<size_t>(match.length());

        const string path = match[2].str();
        const bool is_local = !path.empty() && path.front() != '/' &&
                              path.find("://") == string::npos;
        const string svg = is_local ? load_relative(path) : string();
        if (svg.empty()) {
            result.append(match.str()); // 解析失败时原样保留，不阻断渲染
            continue;
        }

        result.append("![");
        result.append(match[1].str());
        result.append("](data:image/svg+xml;base64,");
        result.append(base64_encode(svg));
        result.push_back(')');
    }
    result.append(markdown, last, string::npos);
    return result;
}

string render_markdown_html(
    const string& markdown,
    const string& stylesheet,
    const vector<MarkdownHeading>& headings,
    const vector<HeadingExperimentLink>& experiment_links) {
    if (markdown.size() > UINT_MAX) {
        throw runtime_error("Markdown document is too large");
    }

    HtmlState state;
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

    const string highlighted = highlight_cpp_code_blocks(std::move(state.body));
    const string linked = insert_experiment_links(
        std::move(highlighted), headings, experiment_links);
    const string body = add_heading_anchors(std::move(linked));
    const string toc = render_html_toc(headings);
    const string layout_class = toc.empty()
        ? "article-layout article-layout-without-toc"
        : "article-layout";

    return
        "<!doctype html>\n"
        "<html lang=\"zh-CN\">\n"
        "<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta http-equiv=\"Content-Security-Policy\" "
        "content=\"default-src 'none'; img-src file: data:; "
        "style-src 'unsafe-inline'; font-src file: data:; "
        "script-src 'unsafe-inline';\">\n"
        "<style>\n" + stylesheet + "\n</style>\n"
        "</head>\n"
        "<body>\n" + reader_toolbar() +
        "<div class=\"" + layout_class + "\">\n" + toc +
        "<main class=\"athena-article\">\n" + body +
        "\n</main></div>\n" + reader_script() +
        "</body>\n"
        "</html>\n";
}
