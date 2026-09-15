import {
  autocompletion,
  closeBrackets,
  closeBracketsKeymap,
  completionKeymap,
  type CompletionContext,
} from "@codemirror/autocomplete";
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentLess,
  indentMore,
  indentWithTab,
  insertNewlineAndIndent,
  toggleComment,
} from "@codemirror/commands";
import { cpp } from "@codemirror/lang-cpp";
import {
  bracketMatching,
  defaultHighlightStyle,
  foldGutter,
  foldKeymap,
  indentOnInput,
  indentUnit,
  syntaxHighlighting,
} from "@codemirror/language";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
import { EditorState, Prec } from "@codemirror/state";
import {
  drawSelection,
  dropCursor,
  EditorView,
  highlightActiveLine,
  highlightActiveLineGutter,
  highlightSpecialChars,
  keymap,
  lineNumbers,
  placeholder,
  rectangularSelection,
} from "@codemirror/view";

let view: EditorView | null = null;

const lightShell = EditorView.theme(
  {
    "&": {
      height: "100%",
      fontSize: "0.85em",
      backgroundColor: "#f8f9fa",
      color: "#212529",
      borderRadius: "0 0 0.7em 0.7em",
    },
    ".cm-scroller": {
      fontFamily: '"SF Mono", Menlo, Consolas, ui-monospace, monospace',
      lineHeight: "1.5",
      overflow: "auto",
    },
    ".cm-content": {
      padding: "0.55em 0",
      caretColor: "#0a58ca",
    },
    ".cm-gutters": {
      backgroundColor: "#eef1f4",
      color: "#8a939c",
      border: "none",
      borderRight: "1px solid #dee2e6",
    },
    ".cm-activeLine": { backgroundColor: "rgba(10, 88, 202, 0.06)" },
    ".cm-activeLineGutter": { backgroundColor: "rgba(10, 88, 202, 0.08)" },
    ".cm-matchingBracket": {
      backgroundColor: "rgba(10, 88, 202, 0.18)",
      outline: "1px solid rgba(10, 88, 202, 0.45)",
    },
    ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": {
      backgroundColor: "rgba(10, 88, 202, 0.18) !important",
    },
    ".cm-tooltip-autocomplete": {
      border: "1px solid #ced4da",
      background: "#fff",
      fontSize: "0.85em",
    },
    "&.cm-focused": { outline: "none" },
  },
  { dark: false },
);

const CPP_SNIPPETS = [
  { label: "for", detail: "循环", type: "keyword", apply: "for (int i = 0; i < n; ++i) {\n    \n}" },
  { label: "forr", detail: "范围 for", type: "keyword", apply: "for (auto &&x : xs) {\n    \n}" },
  { label: "while", detail: "循环", type: "keyword", apply: "while (cond) {\n    \n}" },
  { label: "if", detail: "分支", type: "keyword", apply: "if (cond) {\n    \n}" },
  { label: "ife", detail: "if/else", type: "keyword", apply: "if (cond) {\n    \n} else {\n    \n}" },
  { label: "cout", detail: "输出", type: "function", apply: "cout <<  << '\\n';" },
  { label: "cin", detail: "输入", type: "function", apply: "cin >> ;" },
  { label: "vector", detail: "容器", type: "type", apply: "vector<int> " },
  { label: "string", detail: "字符串", type: "type", apply: "string " },
  { label: "int64", detail: "长整型", type: "type", apply: "int64_t " },
  { label: "uint64", detail: "无符号长整型", type: "type", apply: "uint64_t " },
  { label: "include", detail: "头文件", type: "keyword", apply: "#include <>" },
  { label: "main", detail: "入口", type: "function", apply: "int main() {\n    \n    return 0;\n}" },
  { label: "TODO", detail: "待填", type: "text", apply: "// TODO: " },
];

const CPP_KEYWORDS = [
  "auto", "bool", "break", "case", "catch", "char", "class", "const", "constexpr",
  "continue", "default", "delete", "do", "double", "else", "enum", "false", "float",
  "friend", "goto", "inline", "int", "long", "namespace", "new", "nullptr", "operator",
  "private", "protected", "public", "return", "short", "signed", "sizeof", "static",
  "struct", "switch", "template", "this", "throw", "true", "try", "typedef", "typename",
  "union", "unsigned", "using", "virtual", "void", "volatile", "while",
  "std", "size_t", "cerr", "endl",
].map((label) => ({ label, type: "keyword" as const }));

function cppCompletions(context: CompletionContext) {
  const word = context.matchBefore(/[#\w]*/);
  if (!word || (word.from === word.to && !context.explicit)) return null;
  return {
    from: word.from,
    options: [...CPP_SNIPPETS, ...CPP_KEYWORDS],
    validFor: /^[#\w]*$/,
  };
}

const PAIR: Record<string, string> = {
  "(": ")",
  "[": "]",
  "{": "}",
  '"': '"',
  "'": "'",
};

function deleteBracketPair(target: EditorView): boolean {
  const { from, empty } = target.state.selection.main;
  if (!empty || from === 0) return false;
  const left = target.state.doc.sliceString(from - 1, from);
  const right = target.state.doc.sliceString(from, from + 1);
  if (PAIR[left] !== right) return false;
  target.dispatch({
    changes: { from: from - 1, to: from + 1 },
    userEvent: "delete.backward",
  });
  return true;
}

function enterBetweenBrackets(target: EditorView): boolean {
  const { from, empty } = target.state.selection.main;
  if (!empty || from === 0) return false;
  const left = target.state.doc.sliceString(from - 1, from);
  const right = target.state.doc.sliceString(from, from + 1);
  if ((left !== "{" && left !== "(" && left !== "[") || PAIR[left] !== right) {
    return false;
  }
  const line = target.state.doc.lineAt(from);
  const base = /^[ \t]*/.exec(line.text)?.[0] ?? "";
  const inner = `${base}    `;
  target.dispatch({
    changes: { from, insert: `\n${inner}\n${base}` },
    selection: { anchor: from + 1 + inner.length },
    userEvent: "input",
  });
  return true;
}

/** 输入开括号 / 引号时立刻补另一半；再敲闭合符则跳过已有的那个。 */
const pairInput = EditorView.inputHandler.of((target, from, to, text) => {
  if (target.composing || text.length !== 1) return false;
  const close = PAIR[text];
  if (close) {
    const selected = target.state.doc.sliceString(from, to);
    target.dispatch({
      changes: { from, to, insert: text + selected + close },
      selection: { anchor: from + 1, head: from + 1 + selected.length },
      userEvent: "input.type",
    });
    return true;
  }
  if (")]}'\"".includes(text) && target.state.doc.sliceString(to, to + 1) === text) {
    target.dispatch({
      selection: { anchor: to + 1 },
      userEvent: "select",
    });
    return true;
  }
  return false;
});

/** 输入 `(` `[` `{` `"` `'` 时自动补另一半；Enter 按语法缩进。 */
const editorExtensions = [
  lineNumbers(),
  highlightActiveLineGutter(),
  highlightSpecialChars(),
  history(),
  foldGutter(),
  drawSelection(),
  dropCursor(),
  EditorState.allowMultipleSelections.of(true),
  indentOnInput(),
  syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
  bracketMatching(),
  closeBrackets(),
  Prec.highest(pairInput),
  autocompletion({
    override: [cppCompletions],
    activateOnTyping: true,
    maxRenderedOptions: 24,
  }),
  rectangularSelection(),
  highlightActiveLine(),
  highlightSelectionMatches(),
  indentUnit.of("    "),
  EditorState.tabSize.of(4),
  cpp(),
  lightShell,
  EditorView.lineWrapping,
  placeholder(
    "输入 ( [ { \" ' 会补另一半；在括号中间回车会缩进；运行后自动格式化",
  ),
  Prec.highest(
    keymap.of([
      indentWithTab,
      { key: "Enter", run: enterBetweenBrackets },
      { key: "Enter", run: insertNewlineAndIndent },
      { key: "Backspace", run: deleteBracketPair },
      { key: "Mod-/", run: toggleComment },
      { key: "Mod-]", run: indentMore },
      { key: "Mod-[", run: indentLess },
      { key: "Shift-Tab", run: indentLess },
      ...closeBracketsKeymap,
    ]),
  ),
  keymap.of([
    ...completionKeymap,
    ...searchKeymap,
    ...historyKeymap,
    ...foldKeymap,
    ...defaultKeymap,
  ]),
];

/** 挂到实验区宿主；重复调用会销毁上一份。 */
export function mountLabEditor(
  host: HTMLElement,
  doc: string,
  onChange?: (text: string) => void,
): EditorView {
  destroyLabEditor();
  const extras = onChange
    ? [
        EditorView.updateListener.of((update) => {
          if (update.docChanged) onChange(update.state.doc.toString());
        }),
      ]
    : [];
  view = new EditorView({
    parent: host,
    state: EditorState.create({
      doc,
      extensions: [...editorExtensions, ...extras],
    }),
  });
  queueMicrotask(() => view?.focus());
  return view;
}

export function getLabSource(): string {
  return view?.state.doc.toString() ?? "";
}

export function setLabSource(doc: string): void {
  if (!view) return;
  view.dispatch({
    changes: { from: 0, to: view.state.doc.length, insert: doc },
  });
}

export function destroyLabEditor(): void {
  view?.destroy();
  view = null;
}

export function hasLabEditor(): boolean {
  return view != null;
}
