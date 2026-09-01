#include "cpp_syntax_highlighter.h"

#include <algorithm>
#include <unordered_set>

using namespace std;

namespace {

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

string decode_code_html(const string& html) {
    string decoded;
    decoded.reserve(html.size());
    for (size_t index = 0; index < html.size();) {
        if (html.compare(index, 5, "&amp;") == 0) {
            decoded += '&';
            index += 5;
        } else if (html.compare(index, 4, "&lt;") == 0) {
            decoded += '<';
            index += 4;
        } else if (html.compare(index, 4, "&gt;") == 0) {
            decoded += '>';
            index += 4;
        } else if (html.compare(index, 6, "&quot;") == 0) {
            decoded += '"';
            index += 6;
        } else if (html.compare(index, 5, "&#39;") == 0) {
            decoded += '\'';
            index += 5;
        } else {
            decoded += html[index++];
        }
    }
    return decoded;
}

void append_syntax_span(
    string& html, const string& css_class, const string& code) {
    html += "<span class=\"" + css_class + "\">";
    html += escape_html(code);
    html += "</span>";
}

bool is_cpp_keyword(const string& token) {
    static const unordered_set<string> keywords = {
        "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand",
        "bitor", "break", "case", "catch", "class", "compl", "concept",
        "const", "consteval", "constexpr", "constinit", "const_cast",
        "continue", "co_await", "co_return", "co_yield", "decltype",
        "default", "delete", "do", "dynamic_cast", "else", "enum",
        "explicit", "export", "extern", "false", "for", "friend", "goto",
        "if", "inline", "mutable", "namespace", "new", "noexcept", "not",
        "not_eq", "nullptr", "operator", "or", "or_eq", "private",
        "protected", "public", "register", "reinterpret_cast", "requires",
        "return", "sizeof", "static", "static_assert", "static_cast",
        "struct", "switch", "template", "this", "thread_local", "throw",
        "true", "try", "typedef", "typeid", "typename", "union", "using",
        "virtual", "volatile", "while", "xor", "xor_eq"};
    return keywords.contains(token);
}

bool is_cpp_builtin_type(const string& token) {
    static const unordered_set<string> types = {
        "bool", "char", "char8_t", "char16_t", "char32_t", "double",
        "float", "int", "long", "short", "signed", "unsigned", "void",
        "wchar_t", "size_t", "string", "string_view", "vector", "array",
        "map", "set", "unique_ptr", "shared_ptr", "ostream", "istream"};
    return types.contains(token);
}

string highlight_cpp_code(const string& code) {
    string html;
    html.reserve(code.size() + code.size() / 3);
    bool line_has_only_whitespace = true;

    for (size_t index = 0; index < code.size();) {
        const char character = code[index];
        if (character == '\n') {
            html += '\n';
            ++index;
            line_has_only_whitespace = true;
            continue;
        }
        if (character == ' ' || character == '\t' || character == '\r') {
            html += character;
            ++index;
            continue;
        }

        if (line_has_only_whitespace && character == '#') {
            const size_t start = index;
            while (index < code.size() && code[index] != '\n') {
                ++index;
            }
            append_syntax_span(
                html, "syntax-preprocessor", code.substr(start, index - start));
            line_has_only_whitespace = false;
            continue;
        }
        line_has_only_whitespace = false;

        if (character == '/' && index + 1 < code.size() &&
            code[index + 1] == '/') {
            const size_t start = index;
            while (index < code.size() && code[index] != '\n') {
                ++index;
            }
            append_syntax_span(
                html, "syntax-comment", code.substr(start, index - start));
            continue;
        }
        if (character == '/' && index + 1 < code.size() &&
            code[index + 1] == '*') {
            const size_t start = index;
            index += 2;
            while (index + 1 < code.size() &&
                   !(code[index] == '*' && code[index + 1] == '/')) {
                ++index;
            }
            index = min(code.size(), index + 2);
            append_syntax_span(
                html, "syntax-comment", code.substr(start, index - start));
            continue;
        }
        if (character == '"' || character == '\'') {
            const char quote = character;
            const size_t start = index++;
            bool escaped = false;
            while (index < code.size()) {
                const char current = code[index++];
                if (current == quote && !escaped) {
                    break;
                }
                if (current == '\n' && !escaped) {
                    break;
                }
                if (current == '\\' && !escaped) {
                    escaped = true;
                } else {
                    escaped = false;
                }
            }
            append_syntax_span(
                html, "syntax-string", code.substr(start, index - start));
            continue;
        }
        if (character >= '0' && character <= '9') {
            const size_t start = index++;
            while (index < code.size()) {
                const char current = code[index];
                const bool continues_number =
                    (current >= '0' && current <= '9') ||
                    (current >= 'a' && current <= 'z') ||
                    (current >= 'A' && current <= 'Z') || current == '.' ||
                    current == '\'' || current == '_';
                if (!continues_number) {
                    break;
                }
                ++index;
            }
            append_syntax_span(
                html, "syntax-number", code.substr(start, index - start));
            continue;
        }
        const bool starts_identifier =
            (character >= 'a' && character <= 'z') ||
            (character >= 'A' && character <= 'Z') || character == '_';
        if (starts_identifier) {
            const size_t start = index++;
            while (index < code.size()) {
                const char current = code[index];
                const bool continues_identifier =
                    (current >= 'a' && current <= 'z') ||
                    (current >= 'A' && current <= 'Z') ||
                    (current >= '0' && current <= '9') || current == '_';
                if (!continues_identifier) {
                    break;
                }
                ++index;
            }
            const string token = code.substr(start, index - start);
            if (is_cpp_keyword(token)) {
                append_syntax_span(html, "syntax-keyword", token);
            } else if (is_cpp_builtin_type(token)) {
                append_syntax_span(html, "syntax-type", token);
            } else {
                html += escape_html(token);
            }
            continue;
        }

        html += escape_html(string(1, character));
        ++index;
    }
    return html;
}

} // namespace

string highlight_cpp_code_blocks(string html) {
    static const string prefix = "<pre><code class=\"language-";
    static const string suffix = "</code></pre>";
    size_t search_from = 0;
    while (true) {
        const size_t block = html.find(prefix, search_from);
        if (block == string::npos) {
            break;
        }
        const size_t language_start = block + prefix.size();
        const size_t language_end = html.find("\">", language_start);
        if (language_end == string::npos) {
            break;
        }
        const string language =
            html.substr(language_start, language_end - language_start);
        const size_t code_start = language_end + 2;
        const size_t code_end = html.find(suffix, code_start);
        if (code_end == string::npos) {
            break;
        }
        if (language == "cpp" || language == "c++" || language == "cxx") {
            const string code = decode_code_html(
                html.substr(code_start, code_end - code_start));
            const string highlighted = highlight_cpp_code(code);
            html.replace(code_start, code_end - code_start, highlighted);
            search_from = code_start + highlighted.size() + suffix.size();
        } else {
            search_from = code_end + suffix.size();
        }
    }
    return html;
}
