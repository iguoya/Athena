#!/usr/bin/env python3
"""从上游 LaTeX 源生成段落快照（应用 ADR 0001；做法与 guide/gtkmm 的 sync_upstream.py 同源，本应用独立维护）。

输入：upstream/IBLLinearAlgebra/book/ 下的 modules/moduleN.tex（讲解）、moduleN-exercises.tex（练习题与解答）、
      common/definitions.tex（被引用的定义）、linearalgebra-book.tex（模块顺序、标题、学习目标）。
输出：content/sections/<页 id>.json —— 有序块流，每个可译单元带指纹 sha 与 zh；content/curriculum.json —— 目录与进度。

原文不手写：en 是上游逐字提取、仅做 LaTeX→轻量标记转换的结果；zh 是唯一的手写内容。
范围由 content/scope.json 决定（页 id = 模块文件名，如 module9、appendix2）。

用法：python3 scripts/sync_upstream.py [--check] [页 id ...]
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UP = ROOT / "upstream" / "IBLLinearAlgebra" / "book"
OUT = ROOT / "content" / "sections"
FIG_DIR = ROOT / "content" / "figures"

BOX_ENVS = {"example", "theorem", "emphbox", "definition"}
PLAIN_ENVS = {"proof", "solution"}
LIST_ENVS = {"enumerate", "enumerate*", "itemize"}
MATH_ENVS = {"align*", "align", "equation", "equation*", "alignat*", "gather*", "split", "aligned"}
TRANSPARENT_ENVS = {"center", "quote", "samepage", "minipage", "wrapfigure", "scope", "figure", "pgfinterruptboundingbox"}
TABLE_ENVS = {"tabular"}
FIGURE_ENVS = {"tikzpicture"}
ALL_ENVS = BOX_ENVS | PLAIN_ENVS | LIST_ENVS | MATH_ENVS | TRANSPARENT_ENVS | TABLE_ENVS | FIGURE_ENVS
BEGIN_RE = re.compile(r"\\begin\{(" + "|".join(re.escape(e) for e in sorted(ALL_ENVS, key=len, reverse=True)) + r")\}")

NOISE = re.compile(
    r"\\(noindent|medskip|bigskip|smallskip|clearpage|newpage|centering|par|hfill|raggedright|quad|qquad)\b\s*|"
    r"\\(vspace|hspace|vskip|hskip)\*?\{[^}]*\}|\\label\{[^}]*\}|\\nonumber\b|\\ignorespaces\b|\\relax\b|\\-"
)


def strip_comments(t: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", t)


def match_brace(t: str, i: int) -> int:
    """t[i] == '{'，返回配对的 '}' 下标；找不到返回 -1。"""
    depth = 0
    j = i
    while j < len(t):
        c = t[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def read_args(t: str, i: int, n: int) -> tuple[list[str], int]:
    """从 t[i:] 起读 n 个 {...} 参数（允许前导空白），返回 (参数, 结束位置)。"""
    args = []
    j = i
    for _ in range(n):
        m = re.compile(r"\s*").match(t, j)
        j = m.end()
        if j >= len(t) or t[j] != "{":
            break
        k = match_brace(t, j)
        if k < 0:
            break
        args.append(t[j + 1 : k])
        j = k + 1
    return args, j


def drop_cmd(t: str, name: str) -> str:
    """删掉 \\name{...}（含内容），如 \\index。"""
    out = []
    i = 0
    pat = re.compile(r"\\" + name + r"\*?(?:\[[^\]]*\])?\s*(?=\{)")
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        out.append(t[i : m.start()])
        k = match_brace(t, m.end())
        i = (k + 1) if k >= 0 else m.end()
    return "".join(out)


def unwrap_cmd(t: str, name: str, left: str, right: str) -> str:
    """\\name{X} → left X right（递归处理嵌套）。"""
    out = []
    i = 0
    pat = re.compile(r"\\" + name + r"\s*(?=\{)")
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        out.append(t[i : m.start()])
        k = match_brace(t, m.end())
        if k < 0:
            out.append(t[m.start() : m.end()])
            i = m.end()
            continue
        inner = unwrap_cmd(t[m.end() + 1 : k], name, left, right)
        out.append(left + inner + right)
        i = k + 1
    return "".join(out)


def unwrap_group_font(t: str, font: str, left: str, right: str) -> str:
    """{\\em X} / {\\bf X} → left X right。"""
    out = []
    i = 0
    pat = re.compile(r"\{\s*\\" + font + r"\b\s*")
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        out.append(t[i : m.start()])
        k = match_brace(t, m.start())
        if k < 0:
            out.append(t[m.start() : m.end()])
            i = m.end()
            continue
        out.append(left + unwrap_group_font(t[m.end() : k], font, left, right) + right)
        i = k + 1
    return "".join(out)


def split_math(t: str) -> list[tuple[str, str]]:
    """把一段文字切成 [("t", 文本), ("m", $公式$)]：行内公式整体保护起来。"""
    parts: list[tuple[str, str]] = []
    i = 0
    buf = []
    while i < len(t):
        c = t[i]
        if c == "\\" and i + 1 < len(t):
            if t[i + 1] == "(":
                k = t.find("\\)", i)
                if k > 0:
                    if buf:
                        parts.append(("t", "".join(buf)))
                        buf = []
                    parts.append(("m", t[i + 2 : k]))
                    i = k + 2
                    continue
            buf.append(t[i : i + 2])
            i += 2
            continue
        if c == "$":
            # 收尾的 $ 必须在花括号深度 0：\text{ ... $x$ ... } 里嵌套的 $ 属于内层
            k = i + 1
            depth = 0
            while k < len(t):
                if t[k] == "\\":
                    k += 2
                    continue
                if t[k] == "{":
                    depth += 1
                elif t[k] == "}":
                    depth -= 1
                elif t[k] == "$" and depth <= 0:
                    break
                k += 1
            if k < len(t):
                if buf:
                    parts.append(("t", "".join(buf)))
                    buf = []
                parts.append(("m", t[i + 1 : k]))
                i = k + 1
                continue
        buf.append(c)
        i += 1
    if buf:
        parts.append(("t", "".join(buf)))
    return parts


def sha(en: str) -> str:
    return hashlib.sha1(en.encode("utf-8")).hexdigest()[:12]


def unit(en: str) -> dict:
    return {"en": en, "sha": sha(en), "zh": ""}


def find_end(t: str, env: str, start: int) -> tuple[int, int]:
    """返回 (\\end{env} 起点, 之后位置)；按同名嵌套计数。"""
    tag_b = "\\begin{" + env + "}"
    tag_e = "\\end{" + env + "}"
    depth = 1
    i = start
    while True:
        b = t.find(tag_b, i)
        e = t.find(tag_e, i)
        if e < 0:
            raise ValueError(f"找不到 {tag_e}")
        if 0 <= b < e:
            depth += 1
            i = b + len(tag_b)
        else:
            depth -= 1
            if depth == 0:
                return e, e + len(tag_e)
            i = e + len(tag_e)


def split_items(body: str) -> list[str]:
    """按顶层 \\item 切列表项（嵌套的列表环境里的 \\item 不切）。"""
    items: list[str] = []
    depth = 0
    cur = []
    i = 0
    while i < len(body):
        if body.startswith("\\begin{", i) and re.match(r"\\begin\{(enumerate\*?|itemize)\}", body[i:]):
            depth += 1
        elif body.startswith("\\end{", i) and re.match(r"\\end\{(enumerate\*?|itemize)\}", body[i:]):
            depth -= 1
        if depth == 0 and body.startswith("\\item", i) and not body[i + 5 : i + 6].isalpha():
            if cur or items:
                items.append("".join(cur))
            cur = []
            i += 5
            # \item[label]
            m = re.match(r"\s*\[[^\]]*\]", body[i:])
            if m:
                i += m.end()
            continue
        cur.append(body[i])
        i += 1
    if cur:
        items.append("".join(cur))
    return [x for x in items if x.strip()]


DEFS: dict[str, dict] = {}   # common/definitions.tex 里 SaveDefinition 的 key → {title, body}
PENDING_FIGS: dict[str, str] = {}


def load_definitions() -> None:
    t = strip_comments((UP / "common" / "definitions.tex").read_text(encoding="utf-8", errors="ignore"))
    pos = 0
    while True:
        m = re.compile(r"\\begin\{SaveDefinition\}").search(t, pos)
        if not m:
            return
        end_start, end_after = find_end(t, "SaveDefinition", m.end())
        body = t[m.end():end_start]
        pos = end_after
        opt = re.match(r"\s*\[", body)
        if not opt:
            continue
        k = body.index("[")
        depth, j = 0, k
        while j < len(body):
            if body[j] == "[" and depth == 0:
                depth = 1
            elif body[j] == "{":
                depth += 100
            elif body[j] == "}":
                depth -= 100
            elif body[j] == "]" and depth == 1:
                break
            j += 1
        optstr, rest = body[k + 1:j], body[j + 1:]
        key = re.search(r"key\s*=\s*([\w-]+)", optstr)
        title = re.search(r"title\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", optstr)
        if key:
            DEFS[key.group(1)] = {"title": title.group(1) if title else "", "body": rest}


def clean_math(s: str) -> str:
    """去掉排版专用命令；\\systeme 转成对齐的方程组；其余宏交给前端 KaTeX 的 macros 表（src/macros.ts）。"""
    s = re.sub(r"\\label\{[^}]*\}|\\nonumber\b", "", s)
    s = drop_cmd(s, "index")
    s = re.sub(r"\\index\[[^\]]*\]", "", s)
    s = re.sub(r"\\(hfill|centering)\b", "", s)
    s = s.replace("\\/", "").replace("\\mbox{", "\\text{")
    s = re.sub(r"\\displaybreak(\[\d\])?", "", s)
    for a, b in (("\\Ldots", "\\ldots"), ("\\Cdots", "\\cdots"), ("\\Vdots", "\\vdots"), ("\\Ddots", "\\ddots")):
        s = s.replace(a, b)  # nicematrix 的大写省略号
    s = s.replace("\\Set*{", "\\Set{")  # \Set*{…}：星号版（大定界符），KaTeX 宏会把 * 当成参数
    # \color{LimeGreen!80!black} 这类 xcolor 混色，KaTeX 不认：去掉颜色，保留内容
    s = re.sub(r"\\color\{[^{}]*!\s*[^{}]*\}", "", s)
    # nicematrix：bNiceMatrix / bNiceArray（带 [选项]）→ 普通方括号矩阵
    s = re.sub(r"\\begin\{bNiceArray\}\{\s*([^{}]*?)\s*\}(\[(?:[^\[\]{}]|\{[^{}]*\}|\{(?:[^{}]|\{[^{}]*\})*\})*\])?",
               lambda m: "\\left[\\begin{array}{" + re.sub(r"\s+", "", m.group(1)) + "}", s)
    s = s.replace("\\end{bNiceArray}", "\\end{array}\\right]")
    s = re.sub(r"\\begin\{bNiceMatrix\}(\[(?:[^\[\]{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\])?", lambda m: "\\begin{bmatrix}", s)
    s = s.replace("\\end{bNiceMatrix}", "\\end{bmatrix}")

    def _array(m):  # KaTeX 的 array 不认 @{...} 列修饰
        return "\\begin{array}{" + re.sub(r"@\{[^{}]*\}", "", m.group(1)) + "}"

    s = re.sub(r"\\begin\{array\}\{((?:[^{}]|\{[^{}]*\})*)\}", _array, s)
    # \sysdelim\{. \systeme{…}：左边带大括号的方程组；\sysdelim.. 表示不带
    def _systeme(m: re.Match) -> str:
        eqs = [e.strip() for e in m.group(3).split(",") if e.strip()]
        rows = []
        for e in eqs:
            if "=" in e:  # 在第一个 = 前对齐
                x, y = e.split("=", 1)
                rows.append(f"{x} &= {y}")
            else:
                rows.append(e)
        body = "\\begin{aligned}" + " \\\\ ".join(rows) + "\\end{aligned}"
        return "\\left\\{" + body + "\\right." if m.group(1) and "{" in m.group(1) else body

    s = re.sub(r"(\\sysdelim\s*(?:\\\{\s*\.|\.\.)\s*)?\\systeme(\[[^\]]*\])?\s*\{((?:[^{}]|\{[^{}]*\})*)\}", _systeme, s)
    # aligned 里不能有多个 \tag：把 \tag{x} 改成行尾的 (x) 标注
    s = re.sub(r"\\tag\{([^{}]*)\}", r"\\quad\\text{(\1)}", s)
    return s.strip()


def text_to_md(t: str) -> str:
    t = re.sub(r"\\index\[[^\]]*\]", "", t)
    t = drop_cmd(t, "index")
    t = NOISE.sub(" ", t)
    t = unwrap_cmd(t, "textbf", "**", "**")
    t = unwrap_cmd(t, "emph", "*", "*")
    t = unwrap_cmd(t, "textit", "*", "*")
    t = unwrap_cmd(t, "textrm", "", "")
    t = unwrap_cmd(t, "mbox", "", "")
    t = unwrap_cmd(t, "text", "", "")
    t = unwrap_cmd(t, "url", "", "")
    t = unwrap_cmd(t, "texttt", "`", "`")
    t = unwrap_cmd(t, "footnote", " 〔注：", "〕")
    t = unwrap_group_font(t, "em", "*", "*")
    t = unwrap_group_font(t, "bf", "**", "**")
    t = re.sub(r"\\(eqref|ref|autoref|cref|Cref|pageref)\{[^}]*\}", "〔引用〕", t)
    t = re.sub(r"\\hyperref\[[^\]]*\]\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", t)
    t = t.replace("``", "“").replace("''", "”").replace("---", "—").replace("--", "–")
    t = t.replace("\\&", "&").replace("\\%", "%").replace("\\#", "#").replace("\\$", "＄")
    t = t.replace("\\ldots", "…").replace("\\dots", "…").replace("\\\\", " ")
    t = re.sub(r"\\[,;:! ]", " ", t)
    t = t.replace("~", " ")
    t = re.sub(r"[{}]", "", t)
    return t


def inline(t: str) -> str:
    """行内文字 → 轻量标记：**粗体** *斜体* $公式$。

    先把 $…$ 换成占位符，再在整段文字上展开 \\emph / \\textbf / \\footnote 等（花括号里可能含公式，
    不能等切分之后再展开，否则括号配不上、命令残留在文字里）；公式本身不被这些展开碰到。"""
    math: list[str] = []
    masked = []
    for kind, seg in split_math(t):
        if kind == "m":
            math.append(seg)
            masked.append(f"\u27e6{len(math) - 1}\u27e7")
        else:
            masked.append(seg)
    m = "".join(masked)
    m = drop_cmd(drop_cmd(m, "index"), "eindex")
    m = re.sub(r"\\(textbf|emph|textit)(?=[A-Za-z])([A-Za-z]+)", r"\\\1{\2}", m)  # 上游笔误 \\emphword
    for name, l, r in (("emph", "*", "*"), ("textbf", "**", "**"), ("textit", "*", "*"), ("footnote", " 〔注：", "〕"), ("texttt", "`", "`")):
        m = unwrap_cmd(m, name, l, r)
    out = []
    pos = 0
    for mm in re.finditer(r"\u27e6(\d+)\u27e7", m):
        out.append(text_to_md(m[pos:mm.start()]))
        out.append("$" + clean_math(math[int(mm.group(1))]) + "$")
        pos = mm.end()
    out.append(text_to_md(m[pos:]))
    r = "".join(out)
    r = re.sub(r"[ \t\r\n]+", " ", r).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", r)


# ── 图 ────────────────────────────────────────────────

def tikz_sources(body: str) -> list[str]:
    out, pos = [], 0
    pat = re.compile(r"\\begin\{tikzpicture\}")
    while True:
        m = pat.search(body, pos)
        if not m:
            return out
        end_start, end_after = find_end(body, "tikzpicture", m.end())
        out.append(re.sub(r"\n\s*\n+", "\n", body[m.start():end_after]))  # 空行会让 pgfplots 报「Paragraph ended」
        pos = end_after


def figure_block(body: str) -> dict:
    figs = []
    for src in tikz_sources(body):
        f = hashlib.sha1(re.sub(r"\s+", " ", src).strip().encode("utf-8")).hexdigest()[:12]
        figs.append(f)
        PENDING_FIGS[f] = src
    return {"k": "figure", "env": "tikzpicture", "figs": figs, "caption": None}


# ── 块解析 ────────────────────────────────────────────

def opt_arg(body: str) -> tuple[str | None, str]:
    """环境开头的 [可选参数]（允许内部花括号）。"""
    m = re.match(r"\s*\[", body)
    if not m:
        return None, body
    depth, j = 0, m.end() - 1
    while j < len(body):
        c = body[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "]" and depth == 0:
            return body[m.end():j], body[j + 1:]
        j += 1
    return None, body


def normalize_source(t: str) -> str:
    """上游有些环境是用 \\beginXXX / \\endXXX 宏拼的（\\begindefinition[标题]、\\begindmath* 等），
    还有未加花括号的 \\subsubsection*标题。统一成标准写法再解析。"""
    t = re.sub(r"\\begindefinition\b", r"\\begin{definition}", t)
    t = t.replace("\\enddefinition", "\\end{definition}")
    t = re.sub(r"\\begindmath\*?", r"\\begin{equation*}", t)
    t = re.sub(r"\\enddmath\*?", r"\\end{equation*}", t)
    t = t.replace("\\beginquote", "\\begin{quote}").replace("\\endquote", "\\end{quote}")
    t = re.sub(r"\\subsubsection\*?\s*(?:\{([^{}]*)\}|([^\n{][^\n]*))", lambda m: "\\Heading{" + (m.group(1) or m.group(2)).strip() + "}", t)
    t = re.sub(r"\\includegraphics(\[[^\]]*\])?\s*\S+", "", t)  # 位图（本应用不收）
    t = re.sub(r"\\(HeadingTrue|bfseries|itshape|allowbreak)\b", "", t)
    t = re.sub(r"\\color(mypink|myred|mygreen|myorange|myblue)", "", t)  # 上游把 \\color{x} 写成了 \\colorx
    return t


def paragraphs(text: str) -> list[dict]:
    blocks: list[dict] = []
    # 先展开 \SavedDefinitionRender{key} 为定义盒子占位，再抽出 \[ \] 与 $$ $$
    pat = re.compile(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$|\\SavedDefinitionRender\{([\w-]+)\}", re.S)
    pos = 0
    chunks: list[tuple[str, str]] = []
    for m in pat.finditer(text):
        chunks.append(("t", text[pos:m.start()]))
        if m.group(3):
            chunks.append(("d", m.group(3)))
        else:
            chunks.append(("m", m.group(1) if m.group(1) is not None else m.group(2)))
        pos = m.end()
    chunks.append(("t", text[pos:]))
    for kind, s in chunks:
        if kind == "m":
            blocks.append({"k": "math", "tex": clean_math(s)})
            continue
        if kind == "d":
            d = DEFS.get(s)
            if not d:
                raise ValueError(f"未知的定义 key：{s}")
            blocks.append({"k": "box", "env": "definition", "title": unit(inline(d["title"])) if d["title"] else None,
                           "blocks": parse_blocks(d["body"])})
            continue
        for para in re.split(r"\n\s*\n", s):
            h = re.match(r"\s*\\Heading\s*(\[[^\]]*\])?\s*\{", para)
            if h:
                a, j = read_args(para, h.end() - 1, 1)
                blocks.append({"k": "heading", "t": unit(inline(a[0]))})
                rest = para[j:]
                if rest.strip():
                    en = inline(rest)
                    if en:
                        blocks.append({"k": "p", "t": unit(en)})
                continue
            en = inline(para)
            if en:
                blocks.append({"k": "p", "t": unit(en)})
    return blocks


def parse_blocks(t: str) -> list[dict]:
    blocks: list[dict] = []
    pos = 0
    while True:
        m = BEGIN_RE.search(t, pos)
        if not m:
            blocks += paragraphs(t[pos:])
            return blocks
        blocks += paragraphs(t[pos:m.start()])
        env = m.group(1)
        end_start, end_after = find_end(t, env, m.end())
        body = t[m.end():end_start]
        pos = end_after
        if env in BOX_ENVS:
            title, body = opt_arg(body)
            blocks.append({"k": "box", "env": env, "title": unit(inline(title)) if title and title.strip() else None,
                           "blocks": parse_blocks(body)})
        elif env in PLAIN_ENVS:
            _, body = opt_arg(body)
            blocks.append({"k": env, "title": None, "blocks": parse_blocks(body)})
        elif env in LIST_ENVS:
            _, body = opt_arg(body)
            blocks.append({"k": "list", "ordered": env != "itemize",
                           "items": [parse_blocks(it) for it in split_items(body)]})
        elif env in MATH_ENVS and "\\begin{tikzpicture}" in body:
            blocks.append(figure_block(body))
        elif env in MATH_ENVS:
            tex = clean_math(body)
            if env.startswith("align") or env == "split":
                tex = "\\begin{aligned}" + tex + "\\end{aligned}"
            elif env.startswith("gather"):
                tex = "\\begin{gathered}" + tex + "\\end{gathered}"
            blocks.append({"k": "math", "tex": tex})
        elif env in FIGURE_ENVS:
            blocks.append(figure_block(f"\\begin{{{env}}}{body}\\end{{{env}}}"))
        elif env in TABLE_ENVS:
            args, j = read_args(body, 0, 1)
            blocks.append(parse_table(args[0] if args else "", body[j:]))
        elif env in TRANSPARENT_ENVS:
            if env in ("minipage", "wrapfigure"):  # 跳过 {宽度} 之类的参数
                _, body = opt_arg(body)
                _, j = read_args(body, 0, 2 if env == "wrapfigure" else 1)
                body = body[j:]
            blocks += parse_blocks(body)
        else:
            blocks += parse_blocks(body)


def parse_table(spec: str, body: str) -> dict:
    body = re.sub(r"\\hline|\\cline\{[^}]*\}", "", body)
    rows = []
    for r in re.split(r"\\\\", body):
        if not r.strip():
            continue
        cells = []
        for c in r.split("&"):
            en = inline(c)
            plain = re.sub(r"\$[^$]*\$", "", en)
            cells.append(unit(en) if re.search(r"[A-Za-z]{3,}", plain) else en)
        rows.append(cells)
    return {"k": "table", "spec": re.sub(r"[^lcr|]", "", spec), "rows": rows}


def parse_exercises(t: str) -> list[dict]:
    """moduleN-exercises.tex：exercises > problist > \\prob …（可带 solution 环境）。"""
    t = normalize_source(strip_comments(t))
    m = re.search(r"\\begin\{problist\}", t)
    if not m:
        return []
    end_start, _ = find_end(t, "problist", m.end())
    body = t[m.end():end_start]
    parts = re.split(r"\\prob\b", body)[1:]
    out = []
    for n, p in enumerate(parts, 1):
        sm = re.search(r"\\begin\{solution\}", p)
        if sm:
            se, _ = find_end(p, "solution", sm.end())
            stem = parse_blocks(p[:sm.start()])
            sol = parse_blocks(p[sm.end():se] + "")
            # solution 之后若还有题干文字（少见）并入题干
            tail = p[se + len("\\end{solution}"):]
            if tail.strip():
                stem += parse_blocks(tail)
        else:
            stem, sol = parse_blocks(p), []
        out.append({"id": f"ex{n}", "stem": stem, "sol": sol})
    return out


# ── 课表与书序 ────────────────────────────────────────

def module_info() -> dict[str, dict]:
    """linearalgebra-book.tex：每个模块的标题与「学完应能做到」列表（按 \\input 的模块文件归属）。"""
    t = strip_comments((UP / "linearalgebra-book.tex").read_text(encoding="utf-8", errors="ignore"))
    info: dict[str, dict] = {}
    for m in re.finditer(r"\\begin\{module\}", t):
        end_start, _ = find_end(t, "module", m.end())
        body = t[m.end():end_start]
        inp = re.search(r"\\input\{modules/(module\d+)\.tex\}", body)
        title = re.search(r"\\Title\s*\{((?:[^{}]|\{[^{}]*\})*)\}", body)
        if not inp or not title:
            continue
        lst = re.search(r"\\begin\{itemize\}(.*?)\\end\{itemize\}", body[: inp.start()], re.S)
        info[inp.group(1)] = {"title": inline(title.group(1)), "learn": split_items(lst.group(1)) if lst else []}
    return info


def section_data(pid: str, info: dict[str, dict]) -> dict:
    src = normalize_source(strip_comments((UP / "modules" / f"{pid}.tex").read_text(encoding="utf-8", errors="ignore")))
    blocks: list[dict] = []
    meta = info.get(pid, {})
    if meta.get("learn"):
        items = [parse_blocks(x) for x in meta["learn"]]
        blocks.append({"k": "outcome", "title": None, "blocks": [{"k": "list", "ordered": False, "items": items}]})
    blocks += parse_blocks(src)
    title_en = meta.get("title") or ""
    if not title_en:
        h = re.search(r"\\Heading\s*\{((?:[^{}]|\{[^{}]*\})*)\}", src)
        title_en = inline(h.group(1)) if h else pid
    data = {"id": pid, "title_en": title_en, "blocks": blocks, "exercises": []}
    ex_path = UP / "modules" / f"{pid}-exercises.tex"
    if ex_path.is_file():
        data["exercises"] = parse_exercises(ex_path.read_text(encoding="utf-8", errors="ignore"))
    for ex in data["exercises"]:
        ex["source_refs"] = [{
            "relation": "verbatim",
            "site": "Siefken《MAT223 Workbook: Linear Algebra》（CC BY-SA 4.0 开源教材）",
            "locator": f"{title_en} · 练习题 {ex['id'][2:]}（上游 book/modules/{pid}-exercises.tex）",
            "url": f"https://github.com/siefkenj/IBLLinearAlgebra/blob/master/book/modules/{pid}-exercises.tex",
        }]
    return data


def units(blocks: list[dict]):
    for b in blocks:
        for key in ("t", "title", "caption"):
            if isinstance(b.get(key), dict) and "sha" in b[key]:
                yield b[key]
        if "blocks" in b:
            yield from units(b["blocks"])
        if b.get("k") == "list":
            for it in b["items"]:
                yield from units(it)
        if b.get("k") == "table":
            for row in b.get("rows", []):
                for c in row:
                    if isinstance(c, dict):
                        yield c


def carry_over(old: dict | None, new: dict) -> None:
    """把旧快照的译文带到新快照：先按指纹；指纹变了（上游改了原文，或解析器改进）的按位置对齐，
    旧译文放进 stale_zh（zh 留空），由人确认后写回——不会把对不上的译文悄悄当成最新的。"""
    if not old:
        return

    def flat(d: dict) -> list[dict]:
        return list(units(d.get("blocks", []))) + [u for ex in d.get("exercises", []) for u in units(ex["stem"] + ex["sol"])]

    old_us, new_us = flat(old), flat(new)
    by_sha = {u["sha"]: u["zh"] for u in old_us if u.get("zh")}
    for u in new_us:
        if u["sha"] in by_sha:
            u["zh"] = by_sha[u["sha"]]
    import difflib

    sm = difflib.SequenceMatcher(a=[u["sha"] for u in old_us], b=[u["sha"] for u in new_us], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                o, n = old_us[i1 + k], new_us[j1 + k]
                if not n.get("zh") and (o.get("zh") or o.get("stale_zh")):
                    n["stale_zh"] = o.get("zh") or o["stale_zh"]
    if old.get("title_zh"):
        new["title_zh"] = old["title_zh"]


def zh_progress(data: dict) -> tuple[int, int]:
    us = list(units(data["blocks"])) + [u for ex in data["exercises"] for u in units(ex["stem"] + ex["sol"])]
    return sum(1 for u in us if u.get("zh")), len(us)


def main() -> int:
    check = "--check" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    scope = json.loads((ROOT / "content" / "scope.json").read_text(encoding="utf-8"))
    load_definitions()
    info = module_info()
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
                data = section_data(pid, info)
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
                                   "units": total, "translated": done, "exercises": len(data["exercises"])})
        cur["chapters"].append(entry)
    if not check:
        (FIG_DIR / "src").mkdir(parents=True, exist_ok=True)
        for f, src in PENDING_FIGS.items():
            (FIG_DIR / "src" / f"{f}.tex").write_text(src.strip() + "\n", encoding="utf-8")
        (ROOT / "content" / "curriculum.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n = sum(len(c["items"]) for c in cur["chapters"])
        u = sum(i["units"] for c in cur["chapters"] for i in c["items"])
        e = sum(i["exercises"] for c in cur["chapters"] for i in c["items"])
        print(f"{n} 个页，{u} 个可译单元，{e} 道练习题，{len(PENDING_FIGS)} 幅图")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
