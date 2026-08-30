#include "markdown_renderer.h"

#include <md4c-html.h>
#include <md4c.h>

#include <climits>
#include <map>
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

// 在每个匹配小节的标题正下方插入一张可点的实验入口卡片。只在渲染期
// 发生，操作的是 md_html() 已经产出的 HTML 字符串，不改动 markdown
// 原文、不依赖自定义 Markdown 语法。跟 add_heading_anchors 同一种手法
// （按出现顺序扫描裸 <hN> 标签），必须在 add_heading_anchors 往标签里
// 插 id 属性之前调用，否则标签形状变了，这里的裸标签匹配会失效。
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

    size_t search_from = 0;
    size_t heading_index = 0;
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

        const size_t current_index = heading_index++;
        const string closing_tag = string("</h") + html[open_pos + 2] + ">";
        const size_t close_pos = html.find(closing_tag, open_pos);
        if (close_pos == string::npos) {
            search_from = open_pos + 4;
            continue;
        }
        const size_t after_close = close_pos + closing_tag.size();

        const string heading_title = current_index < headings.size()
            ? headings[current_index].title
            : string();
        const auto found = link_by_heading.find(heading_title);
        if (found == link_by_heading.end()) {
            search_from = after_close;
            continue;
        }

        string card;
        for (const auto* link : found->second) {
            card +=
                "\n<div class=\"athena-experiment-link\">"
                "<a href=\"athena://knowledge/" + escape_html(link->knowledge_id) +
                "\">▶ 动手验证：" + escape_html(link->label) + "</a>"
                "</div>\n";
        }
        html.insert(after_close, card);
        search_from = after_close + card.size();
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
    settings.fontSize = Math.max(16, Math.min(26, Number(settings.fontSize) || 21));
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

    const string linked =
        insert_experiment_links(std::move(state.body), headings, experiment_links);
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
