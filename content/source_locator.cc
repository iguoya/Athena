#include "source_locator.h"

#include <cctype>

using namespace std;

namespace {

bool is_identifier_character(char value) {
    return isalnum(static_cast<unsigned char>(value)) || value == '_';
}

size_t find_closing_brace(string_view source, size_t opening_brace) {
    enum class State {
        code,
        string_literal,
        character_literal,
        line_comment,
        block_comment,
    };

    State state = State::code;
    size_t depth = 0;
    bool escaped = false;

    for (size_t index = opening_brace; index < source.size(); ++index) {
        const char current = source[index];
        const char next = index + 1 < source.size() ? source[index + 1] : '\0';

        switch (state) {
        case State::code:
            if (current == '/' && next == '/') {
                state = State::line_comment;
                ++index;
            } else if (current == '/' && next == '*') {
                state = State::block_comment;
                ++index;
            } else if (current == '"') {
                state = State::string_literal;
                escaped = false;
            } else if (current == '\'') {
                state = State::character_literal;
                escaped = false;
            } else if (current == '{') {
                ++depth;
            } else if (current == '}' && --depth == 0) {
                return index;
            }
            break;
        case State::string_literal:
        case State::character_literal:
            if (escaped) {
                escaped = false;
            } else if (current == '\\') {
                escaped = true;
            } else if ((state == State::string_literal && current == '"') ||
                       (state == State::character_literal && current == '\'')) {
                state = State::code;
            }
            break;
        case State::line_comment:
            if (current == '\n') {
                state = State::code;
            }
            break;
        case State::block_comment:
            if (current == '*' && next == '/') {
                state = State::code;
                ++index;
            }
            break;
        }
    }

    return string_view::npos;
}

} // namespace

optional<SourceRange> locate_cpp_member_function(
    string_view source,
    string_view member_name) {
    if (member_name.empty()) {
        return nullopt;
    }

    size_t search_from = 0;
    while (true) {
        const size_t match = source.find(member_name, search_from);
        if (match == string_view::npos) {
            break;
        }
        search_from = match + member_name.size();

        const bool valid_left =
            match == 0 || !is_identifier_character(source[match - 1]);
        const size_t after_name = match + member_name.size();
        const bool valid_right =
            after_name == source.size() ||
            !is_identifier_character(source[after_name]);
        if (!valid_left || !valid_right) {
            continue;
        }

        size_t cursor = after_name;
        while (cursor < source.size() &&
               isspace(static_cast<unsigned char>(source[cursor]))) {
            ++cursor;
        }
        if (cursor == source.size() || source[cursor] != '(') {
            continue;
        }

        const size_t opening_brace = source.find('{', cursor);
        const size_t declaration_end = source.find(';', cursor);
        if (opening_brace == string_view::npos ||
            (declaration_end != string_view::npos &&
             declaration_end < opening_brace)) {
            continue;
        }

        const size_t closing_brace = find_closing_brace(source, opening_brace);
        if (closing_brace == string_view::npos) {
            return nullopt;
        }

        const size_t previous_newline = source.rfind('\n', match);
        const size_t begin = previous_newline == string_view::npos
            ? 0
            : previous_newline + 1;
        size_t end = closing_brace + 1;
        if (end < source.size() && source[end] == '\n') {
            ++end;
        }
        return SourceRange{begin, end};
    }

    return nullopt;
}
