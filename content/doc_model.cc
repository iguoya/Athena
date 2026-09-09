#include "doc_model.h"

#include <md4c.h>

#include <climits>
#include <stdexcept>
#include <utility>

using namespace std;

namespace {

struct InlineFrame {
    DocInlineKind kind = DocInlineKind::Text;
    string href;
    vector<DocInline> children;
};

struct BlockFrame {
    DocBlock block;
};

struct ParseState {
    DocModel model;
    vector<BlockFrame> blocks;
    vector<InlineFrame> spans;
    vector<DocTableCell> table_row;
    DocTableCell table_cell;
    bool in_table_row = false;
    bool in_table_cell = false;
    bool table_row_is_header = false;
    unsigned table_header_depth = 0;
    bool failed = false;
};

string attribute_text(const MD_ATTRIBUTE& attribute) {
    return attribute.text ? string(attribute.text, attribute.size) : string();
}

string inline_text(const vector<DocInline>& inlines) {
    string text;
    for (const auto& item : inlines) {
        text += item.text;
        text += inline_text(item.children);
    }
    return text;
}

DocBlockKind block_kind(MD_BLOCKTYPE type) {
    switch (type) {
    case MD_BLOCK_QUOTE: return DocBlockKind::BlockQuote;
    case MD_BLOCK_UL: return DocBlockKind::BulletList;
    case MD_BLOCK_OL: return DocBlockKind::OrderedList;
    case MD_BLOCK_LI: return DocBlockKind::ListItem;
    case MD_BLOCK_H: return DocBlockKind::Heading;
    case MD_BLOCK_CODE: return DocBlockKind::CodeBlock;
    case MD_BLOCK_P: return DocBlockKind::Paragraph;
    case MD_BLOCK_TABLE: return DocBlockKind::Table;
    default: return DocBlockKind::Paragraph;
    }
}

vector<DocInline>* active_inlines(ParseState& state) {
    if (!state.spans.empty()) {
        return &state.spans.back().children;
    }
    if (state.in_table_cell) {
        return &state.table_cell.inlines;
    }
    if (!state.blocks.empty()) {
        return &state.blocks.back().block.inlines;
    }
    return nullptr;
}

void append_inline(ParseState& state, DocInline item) {
    if (auto* target = active_inlines(state)) {
        target->push_back(std::move(item));
    }
}

void append_block(ParseState& state, DocBlock block) {
    if (state.blocks.empty()) {
        state.model.blocks.push_back(std::move(block));
    } else {
        state.blocks.back().block.children.push_back(std::move(block));
    }
}

BlockFrame* current_table(ParseState& state) {
    for (auto it = state.blocks.rbegin(); it != state.blocks.rend(); ++it) {
        if (it->block.kind == DocBlockKind::Table) {
            return &*it;
        }
    }
    return nullptr;
}

void open_block(ParseState& state, MD_BLOCKTYPE type, void* detail) {
    BlockFrame frame;
    frame.block.kind = block_kind(type);
    if (type == MD_BLOCK_H) {
        frame.block.level = static_cast<MD_BLOCK_H_DETAIL*>(detail)->level;
    } else if (type == MD_BLOCK_CODE) {
        frame.block.language = attribute_text(
            static_cast<MD_BLOCK_CODE_DETAIL*>(detail)->lang);
    } else if (type == MD_BLOCK_OL) {
        frame.block.ordered_start =
            static_cast<MD_BLOCK_OL_DETAIL*>(detail)->start;
    }
    state.blocks.push_back(std::move(frame));
}

void close_block(ParseState& state, MD_BLOCKTYPE type) {
    if (state.blocks.empty()) {
        state.failed = true;
        return;
    }
    DocBlock block = std::move(state.blocks.back().block);
    state.blocks.pop_back();
    if (type == MD_BLOCK_P && block.inlines.size() == 1
        && block.inlines.front().kind == DocInlineKind::Image) {
        block.kind = DocBlockKind::Image;
        block.image_alt = block.inlines.front().text;
        block.image_path = block.inlines.front().href;
        block.inlines.clear();
    }
    append_block(state, std::move(block));
}

int enter_block(MD_BLOCKTYPE type, void* detail, void* userdata) noexcept {
    auto& state = *static_cast<ParseState*>(userdata);
    try {
        switch (type) {
        case MD_BLOCK_QUOTE:
        case MD_BLOCK_UL:
        case MD_BLOCK_OL:
        case MD_BLOCK_LI:
        case MD_BLOCK_H:
        case MD_BLOCK_CODE:
        case MD_BLOCK_P:
        case MD_BLOCK_TABLE:
            open_block(state, type, detail);
            break;
        case MD_BLOCK_HR:
            append_block(state, {.kind = DocBlockKind::ThematicBreak});
            break;
        case MD_BLOCK_THEAD:
            ++state.table_header_depth;
            break;
        case MD_BLOCK_TR:
            state.in_table_row = true;
            state.table_row_is_header = state.table_header_depth > 0;
            state.table_row.clear();
            break;
        case MD_BLOCK_TH:
        case MD_BLOCK_TD:
            state.in_table_cell = true;
            state.table_cell = {};
            break;
        default:
            break;
        }
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

int leave_block(MD_BLOCKTYPE type, void*, void* userdata) noexcept {
    auto& state = *static_cast<ParseState*>(userdata);
    try {
        switch (type) {
        case MD_BLOCK_QUOTE:
        case MD_BLOCK_UL:
        case MD_BLOCK_OL:
        case MD_BLOCK_LI:
        case MD_BLOCK_H:
        case MD_BLOCK_CODE:
        case MD_BLOCK_P:
        case MD_BLOCK_TABLE:
            close_block(state, type);
            break;
        case MD_BLOCK_THEAD:
            --state.table_header_depth;
            break;
        case MD_BLOCK_TH:
        case MD_BLOCK_TD:
            if (!state.in_table_cell) {
                state.failed = true;
                return 1;
            }
            state.table_row.push_back(std::move(state.table_cell));
            state.table_cell = {};
            state.in_table_cell = false;
            break;
        case MD_BLOCK_TR: {
            auto* table = current_table(state);
            if (!table || !state.in_table_row) {
                state.failed = true;
                return 1;
            }
            if (state.table_row_is_header) {
                table->block.table_header = std::move(state.table_row);
            } else {
                table->block.table_rows.push_back(std::move(state.table_row));
            }
            state.table_row.clear();
            state.in_table_row = false;
            break;
        }
        default:
            break;
        }
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

DocInlineKind span_kind(MD_SPANTYPE type) {
    switch (type) {
    case MD_SPAN_EM: return DocInlineKind::Emphasis;
    case MD_SPAN_STRONG: return DocInlineKind::Strong;
    case MD_SPAN_A: return DocInlineKind::Link;
    case MD_SPAN_IMG: return DocInlineKind::Image;
    case MD_SPAN_CODE: return DocInlineKind::Code;
    default: return DocInlineKind::Text;
    }
}

int enter_span(MD_SPANTYPE type, void* detail, void* userdata) noexcept {
    auto& state = *static_cast<ParseState*>(userdata);
    try {
        InlineFrame frame;
        frame.kind = span_kind(type);
        if (type == MD_SPAN_A) {
            frame.href = attribute_text(static_cast<MD_SPAN_A_DETAIL*>(detail)->href);
        } else if (type == MD_SPAN_IMG) {
            frame.href = attribute_text(static_cast<MD_SPAN_IMG_DETAIL*>(detail)->src);
        }
        state.spans.push_back(std::move(frame));
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

int leave_span(MD_SPANTYPE, void*, void* userdata) noexcept {
    auto& state = *static_cast<ParseState*>(userdata);
    try {
        if (state.spans.empty()) {
            state.failed = true;
            return 1;
        }
        InlineFrame frame = std::move(state.spans.back());
        state.spans.pop_back();
        DocInline item;
        item.kind = frame.kind;
        item.href = std::move(frame.href);
        item.children = std::move(frame.children);
        if (item.kind == DocInlineKind::Image) {
            item.text = inline_text(item.children);
        }
        append_inline(state, std::move(item));
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

int append_text(
    MD_TEXTTYPE type,
    const MD_CHAR* text,
    MD_SIZE size,
    void* userdata) noexcept {
    auto& state = *static_cast<ParseState*>(userdata);
    try {
        if (type == MD_TEXT_CODE && !state.blocks.empty()
            && state.blocks.back().block.kind == DocBlockKind::CodeBlock) {
            state.blocks.back().block.text.append(text, size);
            return 0;
        }

        DocInline item;
        if (type == MD_TEXT_BR) {
            item.kind = DocInlineKind::LineBreak;
        } else if (type == MD_TEXT_SOFTBR) {
            item.kind = DocInlineKind::SoftBreak;
        } else {
            item.kind = type == MD_TEXT_CODE ? DocInlineKind::Code
                                             : DocInlineKind::Text;
            item.text.assign(text, size);
        }
        append_inline(state, std::move(item));
        return 0;
    } catch (...) {
        state.failed = true;
        return 1;
    }
}

} // namespace

DocModel parse_document_blocks(const string& markdown) {
    if (markdown.size() > UINT_MAX) {
        throw runtime_error("Markdown document is too large");
    }

    ParseState state;
    MD_PARSER parser{};
    parser.flags = MD_DIALECT_GITHUB | MD_FLAG_NOHTML;
    parser.enter_block = enter_block;
    parser.leave_block = leave_block;
    parser.enter_span = enter_span;
    parser.leave_span = leave_span;
    parser.text = append_text;

    const int result = md_parse(
        markdown.data(),
        static_cast<MD_SIZE>(markdown.size()),
        &parser,
        &state);
    if (result != 0 || state.failed || !state.blocks.empty()
        || !state.spans.empty()) {
        throw runtime_error("Failed to parse Markdown document blocks");
    }
    return state.model;
}
