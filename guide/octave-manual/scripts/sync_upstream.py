#!/usr/bin/env python3
"""从上游（GNU Octave 官方手册，Texinfo）生成段落快照与课表。

  python3 scripts/sync_upstream.py            重新生成 content/sections/*.json 与 content/curriculum.json
  python3 scripts/sync_upstream.py --check    只核对快照与上游是否一致（check.py 调用）
  python3 scripts/sync_upstream.py <页 id>…   只重新生成这几页

上游克隆在 upstream/octave（gitignore，稀疏检出 doc/interpreter），基准在 upstream.json。
手册里的函数说明（`@DOCSTRING(名字)`）实际在源码注释里：同步时用**本机同版本的 Octave** 的 get_help_text 展开
（所以同步，不是使用，需要装有与钉点同版本的 Octave）；展开结果缓存在 upstream/docstrings.json。

每个可译单元是 {en, sha, zh}：en 是上游原文（Texinfo 行内命令规整成 markdown 风格，公式 $…$、代码 `…`），
sha 是 en 的指纹，zh 是手写译文。重新同步时按指纹带过已有译文，原文变了的旧译文放进 stale_zh。
代码（@example 块、函数签名）逐字保留，不翻译、不产生可译单元。
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UP = ROOT / "upstream" / "octave" / "doc" / "interpreter"
DOC_CACHE = ROOT / "upstream" / "docstrings.json"
OUT = ROOT / "content" / "sections"
EXERCISES = ROOT / "content" / "exercises"
OCTAVE = shutil.which("octave-cli") or shutil.which("octave")


def sha(en: str) -> str:
    return hashlib.sha1(en.encode("utf-8")).hexdigest()[:12]


def unit(en: str) -> dict:
    return {"en": en, "sha": sha(en), "zh": ""}


# ---------------------------------------------------------------------------------------------
# 函数说明：向本机 Octave 要 texinfo 文本

def fetch_docstrings(names: list[str]) -> dict[str, str]:
    cache = json.loads(DOC_CACHE.read_text(encoding="utf-8")) if DOC_CACHE.is_file() else {}
    missing = [n for n in names if n not in cache]
    if missing:
        if OCTAVE is None:
            raise SystemExit("需要本机 Octave 来展开函数说明（@DOCSTRING），但没找到 octave / octave-cli")
        quoted = ",".join(f"'{n}'" for n in missing)
        prog = ("names = {" + quoted + "}; for i = 1:numel(names) [t, f] = get_help_text (names{i}); "
                "printf ('\\x01%s\\x02%s\\x03%s\\x04', names{i}, f, t); end")
        r = subprocess.run([OCTAVE, "--no-gui", "--no-window-system", "--norc", "--quiet", "--eval", prog],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise SystemExit(f"Octave 取函数说明失败：{r.stderr[-300:]}")
        for m in re.finditer(r"\x01([^\x02]*)\x02([^\x03]*)\x03(.*?)\x04", r.stdout, re.S):
            name, fmt, text = m.groups()
            if fmt != "texinfo":
                raise SystemExit(f"{name}：说明格式是 {fmt!r}，不是 texinfo（函数不存在或没有文档）")
            cache[name] = text
        still = [n for n in missing if n not in cache]
        if still:
            raise SystemExit(f"没取到这些函数的说明：{still}")
        DOC_CACHE.parent.mkdir(parents=True, exist_ok=True)
        DOC_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return cache


# ---------------------------------------------------------------------------------------------
# 行内命令：Texinfo → markdown 风格

CODE_CMDS = {"code", "qcode", "samp", "file", "command", "option", "env", "kbd", "key", "verb", "tcode", "t", "asis"}
EMPH_CMDS = {"emph", "dfn", "cite", "i", "slanted", "var"}
STRONG_CMDS = {"strong", "b"}
PLAIN_CMDS = {"sc", "nospell", "w", "r", "sansserif", "titlefont", "math_plain"}
DROP_CMDS = {"sortas", "anchor", "cindex", "findex", "vindex", "kindex", "image", "footnotestyle", "noindent", "tie_"}
SPECIAL = {"@": "@", "{": "{", "}": "}", "*": " ", ":": "", ".": ".", "-": "", "!": "!", "?": "?", " ": " ", "\n": " "}
ACCENTS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303", ",": "\u0327"}
GLYPHS = {"dots": "…", "result": "⇒", "print": "-|", "error": "error→", "equiv": "≡", "TeX": "TeX", "LaTeX": "LaTeX",
          "tie": " ", "minus": "−", "bullet": "•", "pounds": "£", "copyright": "©", "expansion": "→", "arrow": "→",
          "enddots": "…", "pi": "π", "textdegree": "°", "AA": "Å", "backslashchar": "\\", "comma": ",",
          "hashchar": "#", "atchar": "@", "lbracechar": "{", "rbracechar": "}"}


def match_brace(s: str, i: int) -> int:
    """s[i] 是 '{'；返回配对的 '}' 下标（尊重 @{ @} 转义）。"""
    depth = 0
    k = i
    while k < len(s):
        c = s[k]
        if c == "@" and k + 1 < len(s):
            k += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return len(s) - 1


def split_args(body: str) -> list[str]:
    out, depth, cur, k = [], 0, [], 0
    while k < len(body):
        c = body[k]
        if c == "@" and k + 1 < len(body):
            cur.append(body[k:k + 2])
            k += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if c == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        k += 1
    out.append("".join(cur))
    return [a.strip() for a in out]


def brace_group(t: str, i: int) -> int:
    """t[i] 是 '{'，返回配对的 '}'（plain TeX，没有 @ 转义）。"""
    depth = 0
    for k in range(i, len(t)):
        if t[k] == "\\" and k + 1 < len(t):
            continue
        if t[k] == "{":
            depth += 1
        elif t[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    return len(t) - 1


def plain_tex(t: str) -> str:
    """plain TeX 的 \\matrix{…\\cr…}、\\pmatrix、\\cases、\\eqalign 转成 KaTeX 认得的环境。"""
    envs = {"matrix": "matrix", "pmatrix": "pmatrix", "cases": "cases", "eqalign": "aligned"}
    for cmd, env in envs.items():
        while True:
            m = re.search(r"\\" + cmd + r"\s*\{", t)
            if not m:
                break
            o = m.end() - 1
            c = brace_group(t, o)
            body = t[o + 1:c].replace("\\cr", "\\\\")
            body = re.sub(r"(\\\\)\s*$", "", body.rstrip())
            if env == "cases":
                body = body.replace("$", "").replace(";", "")
            t = t[:m.start()] + f"\\begin{{{env}}}" + body + f"\\end{{{env}}}" + t[c + 1:]
    return t


def math_tex(body: str) -> str:
    """@math{…} 里的内容转成 LaTeX（手册里的 @math 基本是简单的下标、上标和 @var）。"""
    t = body
    t = re.sub(r"@var\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"@dots\{\}", r"\\ldots{}", t)
    t = re.sub(r"@code\{([^{}]*)\}", r"\\mathtt{\1}", t)
    t = t.replace("@@", "@").replace("@{", "\\{").replace("@}", "\\}")
    return plain_tex(t.strip())


def conv(s: str, code: bool = False) -> str:
    """转换一段含 Texinfo 行内命令的文字；code=True 时在代码片段里（强调标记全部去掉）。"""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c != "@":
            out.append(c)
            i += 1
            continue
        if i + 1 >= n:
            i += 1
            continue
        nx = s[i + 1]
        if nx in ACCENTS:
            m = re.match(r"\{?([A-Za-z])\}?", s[i + 2:])
            if m:
                out.append(unicodedata.normalize("NFC", m.group(1) + ACCENTS[nx]))
                i += 2 + m.end()
                continue
        if nx in SPECIAL:
            out.append(SPECIAL[nx])
            i += 2
            continue
        m = re.match(r"@([A-Za-z]+)", s[i:])
        if not m:
            out.append("@")
            i += 1
            continue
        name = m.group(1)
        j = i + 1 + len(name)
        if j < n and s[j] == "{":
            k = match_brace(s, j)
            body = s[j + 1:k]
            i = k + 1
            if name in CODE_CMDS:
                inner = conv(body, True).replace("`", "'")
                out.append(inner if code else f"`{inner}`")
            elif name in EMPH_CMDS:
                inner = conv(body, code)
                out.append(inner if code else f"*{inner}*")
            elif name in STRONG_CMDS:
                inner = conv(body, code)
                out.append(inner if code else f"**{inner}**")
            elif name == "sc":
                out.append(conv(body, code).upper())
            elif name in PLAIN_CMDS:
                out.append(conv(body, code))
            elif name == "math":
                out.append(math_tex(body) if code else f"${math_tex(body)}$")
            elif name in ("ref", "xref", "pxref", "inforef"):
                label = conv(split_args(body)[0], True)
                if label.startswith("fig:"):
                    out.append("the figure")
                elif label.startswith("tab:"):
                    out.append("the table")
                elif label.startswith("XREF"):  # 函数文档里指向另一个函数的内部锚点（XREFnorm → norm）
                    out.append(label[4:] if code else f"`{label[4:]}`")
                else:
                    out.append({"xref": f"See {label}", "pxref": f"see {label}"}.get(name, label))
            elif name == "url":
                out.append(conv(body, True))
            elif name == "uref":
                a = split_args(body)
                out.append(f"{conv(a[1], code)} ({conv(a[0], True)})" if len(a) > 1 and a[1] else conv(a[0], True))
            elif name == "footnote":
                out.append(f" ({conv(body, code)})")
            elif name in ("seealso", "xseealso"):
                items = [conv(a, True) for a in split_args(body)]
                out.append("See also: " + ", ".join(f"`{x}`" for x in items) + ".")
            elif name in GLYPHS:
                out.append(GLYPHS[name])
            elif name in DROP_CMDS:
                pass
            else:
                out.append(conv(body, code))  # 不认识的命令：留内容
            continue
        i = j
        if name in GLYPHS:
            out.append(GLYPHS[name])
        # 无花括号的命令（@noindent、@refill 等）直接丢
    return "".join(out)


def typography(s: str) -> str:
    s = re.sub(r"``(.*?)''", "\u201c\\1\u201d", s)
    s = re.sub(r"`([^`'@{}]*)'", "\u2018\\1\u2019", s)
    return s.replace("---", "\u2014")


def inline(s: str) -> str:
    s = conv(typography(s))
    s = re.sub(r"\s+", " ", s).strip()
    return s


def verbatim(lines: list[str]) -> str:
    """@example 里的文字：命令转换（@result → ⇒ 等），不要强调标记；保留换行与缩进。"""
    return "\n".join(conv(l, True).rstrip() for l in lines if not re.match(r"\s*@(group|end group)\s*$", l)).strip("\n")


# ---------------------------------------------------------------------------------------------
# 块结构

SKIP_LINE = re.compile(r"^@(c|comment|cindex|findex|vindex|kindex|opindex|prindex|tindex|anchor|noindent|need|page|sp|node|include|"
                       r"setfilename|settitle|group|end group|refill|top|vskip|exdent|ifclear|ifset|set|clear|"
                       r"headitem_end)\b", re.I)
HEADING_RE = re.compile(r"^@(chapter|section|subsection|subsubsection|unnumbered\w*|heading|subheading|subsubheading|appendix\w*)\s+(.*)$")
DEF_RE = re.compile(r"^@(deftypefnx?|deftypevrx?|defvrx?|deffnx?)\s+(.*)$")
VERBATIM_ENVS = {"example", "smallexample", "display", "smalldisplay", "format", "verbatim", "lisp"}
SKIP_ENVS = {"menu", "ifnottex", "ifinfo", "ifhtml", "iftex", "ifnothtml_", "direntry", "titlepage", "copying", "macro"}
KEEP_ENVS = {"ifnotinfo", "ifnothtml", "ifnotplaintext", "group", "ifplaintext_"}


def find_end(lines: list[str], i: int, env: str) -> int:
    """lines[i] 是 @env 开头；返回对应 @end env 的行号（支持同名嵌套）。"""
    depth = 0
    for k in range(i, len(lines)):
        t = lines[k].strip()
        if re.match(rf"@{env}\b", t):
            depth += 1
        elif t == f"@end {env}":
            depth -= 1
            if depth == 0:
                return k
    return len(lines) - 1


ALLOWED_FIGURES: set[str] = set()  # 当前页要收的图（scope.json 的 figures + figures_more）
STAGE2_FIGURES: set[str] = set()   # 其中属于进阶的图
STAGE2_FUNCTIONS: set[str] = set()  # 当前页属于进阶的函数（scope.json 的 functions_more）


def sig_text(rest: str) -> tuple[str, str]:
    """@deftypefn {类别} {返回值 =} 名字 (参数…) 的后半 → (名字, 一行签名)。"""
    parts: list[str] = []
    k = 0
    for _ in range(2):  # 类别、返回值都是花括号组
        rest = rest.lstrip()
        if rest.startswith("{"):
            e = match_brace(rest, 0)
            parts.append(rest[1:e])
            rest = rest[e + 1:]
        else:
            m = re.match(r"(\S+)", rest)
            parts.append(m.group(1) if m else "")
            rest = rest[len(m.group(1)) if m else 0:]
    ret = conv(parts[1], True).strip()
    tail = conv(rest, True).strip()
    name = re.match(r"([\w.]+)", tail).group(1) if re.match(r"([\w.]+)", tail) else tail
    return name, (f"{ret} {tail}".strip() if ret else tail)


def parse_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    para: list[str] = []

    def flush() -> None:
        if para:
            text = inline(" ".join(para))
            if text:
                blocks.append({"k": "p", "t": unit(text)})
            para.clear()

    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        t = raw.strip()
        if not t:
            flush()
            i += 1
            continue
        if SKIP_LINE.match(t):
            i += 1
            continue
        hm = HEADING_RE.match(t)
        if hm:
            flush()
            level = {"chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4}.get(hm.group(1), 3)
            blocks.append({"k": "heading", "level": level, "t": unit(inline(hm.group(2)))})
            i += 1
            continue
        em = re.match(r"@(\w+)\b", t)
        env = em.group(1) if em else ""
        if env == "float":
            e = find_end(lines, i, "float")
            body = "\n".join(lines[i + 1:e])
            im = re.search(r"@image\{([\w-]+)", body)
            cm = re.search(r"@caption\{", body)
            flush()
            if im and im.group(1) in ALLOWED_FIGURES:
                cap = None
                if cm:
                    k = match_brace(body, cm.end() - 1)
                    cap = unit(inline(body[cm.end():k]))
                blocks.append({"k": "figure", "id": im.group(1), "caption": cap, **({"stage": 2} if im.group(1) in STAGE2_FIGURES else {})})
            i = e + 1
            continue
        # 整块丢弃
        if env in SKIP_ENVS:
            i = find_end(lines, i, env) + 1
            continue
        if env in KEEP_ENVS:
            i += 1
            continue
        if t.startswith("@end "):
            i += 1
            continue
        # TeX 块：展示公式变成 math 块，行内的并回当前段落
        if env == "tex":
            e = find_end(lines, i, "tex")
            body = "\n".join(lines[i + 1:e]).strip()
            displays = re.findall(r"\$\$(.*?)\$\$", body, re.S)
            if displays and re.fullmatch(r"(\s*\$\$.*?\$\$)+\s*", body, re.S):
                flush()
                for d in displays:
                    blocks.append({"k": "math", "tex": re.sub(r"\s+", " ", plain_tex(d.strip()))})
            else:
                if body.startswith("$") and body.endswith("$") and not body.startswith("$$"):
                    body = "$" + body[1:-1].strip() + "$"
                para.append(re.sub(r"\$([^$]+)\$", lambda m: "$" + plain_tex(m.group(1)) + "$", body))
            i = e + 1
            continue
        if env in VERBATIM_ENVS:
            flush()
            e = find_end(lines, i, env)
            text = verbatim(lines[i + 1:e])
            if text:
                blocks.append({"k": "code", "text": text})
            i = e + 1
            continue
        dm = DEF_RE.match(t)
        if dm and dm.group(1) in ("deftypefn", "deffn", "deftypevr", "defvr"):
            flush()
            kind = dm.group(1)
            e = find_end(lines, i, kind)
            sigs: list[str] = []
            name = ""
            body_start = i
            j = i
            while j < e:
                lm = DEF_RE.match(lines[j].strip())
                if not lm:
                    break
                if kind.startswith("deftype"):
                    nm, sg = sig_text(lm.group(2))
                else:
                    cat = re.match(r"\{[^}]*\}\s*(.*)$", lm.group(2))
                    sg = conv((cat.group(1) if cat else lm.group(2)), True).strip()
                    nm = sg.split()[0] if sg else ""
                name = name or nm
                sigs.append(sg)
                j += 1
            blocks.append({"k": "def", "name": name, "sigs": sigs, **({"stage": 2} if name in STAGE2_FUNCTIONS else {}), "blocks": parse_blocks(lines[j:e])})
            i = e + 1
            continue
        if env == "table" or env == "ftable" or env == "vtable":
            flush()
            e = find_end(lines, i, env)
            style = (t.split() + [""])[1].lstrip("@")
            blocks.append({"k": "dl", "items": parse_items(lines[i + 1:e], style)})
            i = e + 1
            continue
        if env in ("itemize", "enumerate"):
            flush()
            e = find_end(lines, i, env)
            items = [[heads[0]] + blk for heads, blk in split_items(lines[i + 1:e])]
            blocks.append({"k": "list", "ordered": env == "enumerate", "items": [parse_blocks(b) for b in items]})
            i = e + 1
            continue
        if env == "multitable":
            flush()
            e = find_end(lines, i, "multitable")
            blocks.append(parse_multitable(lines[i + 1:e]))
            i = e + 1
            continue
        if env == "quotation":
            flush()
            e = find_end(lines, i, "quotation")
            blocks.append({"k": "box", "env": "note", "title": None, "blocks": parse_blocks(lines[i + 1:e])})
            i = e + 1
            continue
        if env == "center":
            flush()
            para.append(t[len("@center"):])
            flush()
            i += 1
            continue
        para.append(raw)
        i += 1
    flush()
    return blocks


def split_items(lines: list[str]) -> list[tuple[list[str], list[str]]]:
    """按 @item / @itemx 切：返回 [(条目头们, 体行们)]。同层嵌套的 @table/@itemize 里的 @item 不切。"""
    out: list[tuple[list[str], list[str]]] = []
    heads: list[str] = []
    body: list[str] = []
    depth = 0
    started = False

    def close() -> None:
        nonlocal heads, body
        if started:
            out.append((heads, body))
        heads, body = [], []

    for l in lines:
        t = l.strip()
        m = re.match(r"@(table|ftable|vtable|itemize|enumerate|multitable|example|smallexample|display|format|verbatim|quotation|deftypefn|tex|ifnottex|float)\b", t)
        if m:
            depth += 1
        elif t.startswith("@end ") and depth > 0:
            depth -= 1
        im = re.match(r"@(item|itemx)\b\s*(.*)$", t)
        if im and depth == 0:
            if im.group(1) == "item":
                close()
                started = True
                heads = [im.group(2)]
            else:
                heads.append(im.group(2))
            continue
        if started:
            body.append(l)
    close()
    return out


def parse_items(lines: list[str], style: str) -> list[dict]:
    items = []
    for heads, body in split_items(lines):
        terms = []
        for h in heads:
            if style in ("code", "samp", "file", "command", "option", "kbd", "key"):
                terms.append(f"`{conv(h, True).strip()}`")
            elif style == "var":
                terms.append(f"*{conv(h, True).strip()}*")
            else:
                terms.append(inline(h))
        items.append({"term": unit(", ".join(t for t in terms if t.strip("` *"))), "blocks": parse_blocks(body)})
    return items


def parse_multitable(lines: list[str]) -> dict:
    rows: list[list[str]] = []
    for l in lines:
        t = l.strip()
        m = re.match(r"@(headitem|item)\b\s*(.*)$", t)
        if m:
            rows.append([m.group(2)])
        elif rows and t:
            rows[-1][-1] += " " + t
        else:
            continue
        # 单元格用 @tab 分隔
        cells = re.split(r"\s@tab\s|^@tab\s|@tab\s", rows[-1][-1]) if "@tab" in rows[-1][-1] else rows[-1]
        rows[-1] = cells
    return {"k": "table", "spec": "grid", "rows": [[unit(inline(c)) if inline(c) else "" for c in r] for r in rows]}


# ---------------------------------------------------------------------------------------------
# 页：取 txi 里指定的节，展开函数说明

def page_lines(spec: dict) -> tuple[list[str], str]:
    text = (UP / spec["file"]).read_text(encoding="utf-8")
    lines = text.splitlines()
    chapter = ""
    keep: list[str] = []
    want = set(spec.get("sections", []))
    intro = spec.get("intro", True)
    cur: str | None = None  # 当前节名；None = 章首（第一个 @section 之前）
    for l in lines:
        m = re.match(r"@chapter\s+(.*)$", l)
        if m:
            chapter = inline(m.group(1))
            continue
        sm = re.match(r"@section\s+(.*)$", l)
        if sm:
            cur = inline(sm.group(1))
        in_scope = (cur is None and intro) or (cur is not None and (not want or cur in want))
        if in_scope:
            keep.append(l)
    return keep, spec.get("title_en") or chapter


def expand_docstrings(lines: list[str], spec: dict) -> list[str]:
    allow = spec.get("functions")
    if allow is not None:
        allow = list(allow) + list(spec.get("functions_more", []))
    names: list[str] = []
    for l in lines:
        m = re.match(r"\s*@DOCSTRING\((\w+)\)", l)
        if m and (allow is None or m.group(1) in allow):
            names.append(m.group(1))
    docs = fetch_docstrings(sorted(set(names))) if names else {}
    out: list[str] = []
    for l in lines:
        m = re.match(r"\s*@DOCSTRING\((\w+)\)", l)
        if not m:
            out.append(l)
            continue
        name = m.group(1)
        if allow is not None and name not in allow:
            continue
        body = docs[name].splitlines()
        if body and "texinfo" in body[0]:
            body = body[1:]
        out.extend(body)
        out.append("")
    if allow:
        missing = [f for f in allow if f not in names]
        if missing:
            raise SystemExit(f"{spec['id']}: functions 里列了但这些节里没有对应的 @DOCSTRING：{missing}")
    return out


def prune_headings(blocks: list[dict]) -> list[dict]:
    """函数被裁掉后，下面没有内容的标题（紧跟同级或更高一级标题，或到页尾）也去掉。"""
    out: list[dict] = []
    for k, b in enumerate(blocks):
        if b["k"] == "heading":
            nxt = blocks[k + 1] if k + 1 < len(blocks) else None
            if nxt is None or (nxt["k"] == "heading" and nxt.get("level", 9) <= b.get("level", 9)):
                continue
        out.append(b)
    if len(out) != len(blocks):
        return prune_headings(out)
    return out


def section_data(spec: dict) -> dict:
    ALLOWED_FIGURES.clear()
    ALLOWED_FIGURES.update(spec.get("figures", []) + spec.get("figures_more", []))
    STAGE2_FIGURES.clear()
    STAGE2_FIGURES.update(spec.get("figures_more", []))
    STAGE2_FUNCTIONS.clear()
    STAGE2_FUNCTIONS.update(spec.get("functions_more", []))
    lines, title_en = page_lines(spec)
    lines = expand_docstrings(lines, spec)
    blocks = prune_headings(parse_blocks(lines))
    return {"id": spec["id"], "title_en": title_en, "blocks": blocks}


def units(blocks: list[dict]):
    for b in blocks:
        for key in ("t", "title", "term", "caption"):
            if isinstance(b.get(key), dict) and "sha" in b[key]:
                yield b[key]
        if "blocks" in b:
            yield from units(b["blocks"])
        if b.get("k") == "list":
            for it in b["items"]:
                yield from units(it)
        if b.get("k") == "dl":
            for it in b["items"]:
                yield it["term"]
                yield from units(it["blocks"])
        if b.get("k") == "table":
            for row in b.get("rows", []):
                for c in row:
                    if isinstance(c, dict):
                        yield c


def carry_over(old: dict | None, new: dict) -> None:
    if not old:
        return
    old_us, new_us = list(units(old.get("blocks", []))), list(units(new["blocks"]))
    by_sha = {u["sha"]: u["zh"] for u in old_us if u.get("zh")}
    for u in new_us:
        if u["sha"] in by_sha:
            u["zh"] = by_sha[u["sha"]]
    sm = difflib.SequenceMatcher(a=[u["sha"] for u in old_us], b=[u["sha"] for u in new_us], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                o, nw = old_us[i1 + k], new_us[j1 + k]
                if not nw.get("zh") and (o.get("zh") or o.get("stale_zh")):
                    nw["stale_zh"] = o.get("zh") or o["stale_zh"]
    if old.get("title_zh"):
        new["title_zh"] = old["title_zh"]


def zh_progress(data: dict) -> tuple[int, int]:
    us = list(units(data["blocks"]))
    return sum(1 for u in us if u.get("zh")), len(us)


def exercise_count(pid: str) -> int:
    p = EXERCISES / f"{pid}.json"
    return len(json.loads(p.read_text(encoding="utf-8"))) if p.is_file() else 0


def main() -> int:
    check = "--check" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    scope = json.loads((ROOT / "content" / "scope.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    bad = 0
    cur = {"chapters": []}
    for part in scope["parts"]:
        entry = {"id": part["id"], "title_en": part["en"], "title_zh": part["zh"], "items": []}
        for it in part["items"]:
            pid = it["id"]
            path = OUT / f"{pid}.json"
            if only and pid not in only and path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
            else:
                data = section_data(it)
                old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
                carry_over(old, data)
                data["title_zh"] = it["zh"]
                text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
                if check:
                    if not path.is_file() or path.read_text(encoding="utf-8") != text:
                        print(f"快照与上游不一致：{pid}（跑 sync_upstream.py 更新）")
                        bad += 1
                else:
                    path.write_text(text, encoding="utf-8")
            done, total = zh_progress(data)
            entry["items"].append({"id": pid, "level": 2, "title_zh": it["zh"], "title_en": data["title_en"], "page": True,
                                   "units": total, "translated": done, "exercises": exercise_count(pid)})
        cur["chapters"].append(entry)
    if not check:
        (ROOT / "content" / "curriculum.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n = sum(len(c["items"]) for c in cur["chapters"])
        u = sum(i["units"] for c in cur["chapters"] for i in c["items"])
        e = sum(i["exercises"] for c in cur["chapters"] for i in c["items"])
        print(f"{n} 个页，{u} 个可译单元，{e} 道试一试")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
