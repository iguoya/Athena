#!/usr/bin/env python3
"""从上游 LaTeX 源生成段落快照（应用 ADR 0001，做法同 gtkmm 的 sync_upstream.py）。

输入：upstream/linear-algebra/baseText/{content,exercises}/*.tex 与 courseSetup.tex（书的顺序、
      每节对应哪份习题文件）。范围由 content/scope.json 裁剪。
输出：content/sections/<上游文件名>.json —— 有序块流，每个可译单元带指纹 sha 与 zh；
      content/curriculum.json —— 章/节目录与各节译文进度（由 scope.json 与快照推出，不手写）。

原文不手写：en 是上游逐字提取、仅做 LaTeX→轻量标记转换的结果（公式原样保留为 $...$ 与展示块）；
zh 是唯一的手写内容。上游一变：指纹相同的单元保留译文，原文变了的标 stale（旧译文存
stale_zh 供参考），新增的 zh 为空。只译 stale 与空的。

用法：python3 scripts/sync_upstream.py [--check] [节 id ...]
  --check  只比对快照与上游是否一致，不写文件（check.py 用）
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UP = ROOT / "upstream" / "linear-algebra" / "baseText"
OUT = ROOT / "content" / "sections"

# 容器环境：内容是块流；title 取第一个花括号参数
BOX_ENVS = {"definition", "theorem", "proposition", "lemma", "corollary", "example", "algorithm",
            "procedure", "discussion", "problem"}
# 无标题的块环境
PLAIN_ENVS = {"solution", "proof", "proofof", "outcome", "sol"}
LIST_ENVS = {"enumerate", "itemize", "enumialphparenastyle"}
MATH_ENVS = {"equation*", "equation", "eqnarray*", "align*", "align"}
# 整体原样处理成「图」的环境（tikz 画不出来，界面显示占位并指向原书）
FIGURE_ENVS = {"tikzpicture", "circuitikz", "figure"}
TRANSPARENT_ENVS = {"center", "samepage", "scope"}
TABLE_ENVS = {"tabular"}
ALL_ENVS = (BOX_ENVS | PLAIN_ENVS | LIST_ENVS | MATH_ENVS | FIGURE_ENVS | TRANSPARENT_ENVS
            | TABLE_ENVS | {"ex"})
BEGIN_RE = re.compile(r"\\begin\{(" + "|".join(re.escape(e) for e in sorted(ALL_ENVS, key=len, reverse=True)) + r")\}")

NOISE = re.compile(
    r"\\(noindent|medskip|bigskip|smallskip|clearpage|newpage|centering|par|hfill|raggedright|"
    r"noindentafter|nospellcheck)\b\s*|\\(vspace|hspace|vskip|hskip)\*?\{[^}]*\}|\\label\{[^}]*\}|"
    r"\\nonumber\b|\\ignorespaces\b|\\relax\b|\\allowbreak\b|\\-"
)


# 交叉引用解析状态：LABELS 是全书「盒子环境的 slug → (环境, 标题)」，EQMAP 是当前节里被 \eqref
# 引用的公式标签 → 序号（界面里公式编号是本节内连续的，不照搬原书的章内编号）
LABELS: dict[str, tuple[str, str]] = {}
EQMAP: dict[str, int] = {}


def scan_labels() -> None:
    pat = re.compile(r"\\begin\{(definition|theorem|proposition|lemma|corollary|example|algorithm|procedure|"
                     r"discussion|problem)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{([^{}]*)\}")
    for f in sorted((UP / "content").glob("*.tex")):
        for m in pat.finditer(strip_comments(f.read_text(encoding="utf-8", errors="ignore"))):
            LABELS[m.group(3)] = (m.group(1), re.sub(r"\s+", " ", m.group(2)).strip())


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


def clean_math(s: str) -> str:
    """自定义矩阵环境 → 标准写法，去掉排版专用命令。KaTeX 端另有宏表（src/macros.ts）。"""
    s = re.sub(r"\\begin\{(mymatrix|mysmallmatrix)\}\{([^}]*)\}", r"\\left[\\begin{array}{\2}", s)
    s = re.sub(r"\\end\{(mymatrix|mysmallmatrix)\}", r"\\end{array}\\right]", s)
    s = re.sub(r"\\begin\{absmatrix\}\{([^}]*)\}", r"\\left|\\begin{array}{\1}", s)
    s = re.sub(r"\\end\{absmatrix\}", r"\\end{array}\\right|", s)
    tags = [EQMAP[x] for x in re.findall(r"\\label\{([^}]*)\}", s) if x in EQMAP]
    s = re.sub(r"\\label\{[^}]*\}|\\nonumber\b", "", s)
    if tags:
        s = s.rstrip() + f" \\tag{{{tags[0]}}}"
    s = drop_cmd(s, "index")
    s = re.sub(r"\\(hfill|centering)\b", "", s)
    for _ in range(3):  # 嵌套的 \strikeh{…}{\strikev{…}{x}} 由内向外逐层替换
        s = re.sub(r"\\strike[hv]\s*\{[^{}]*\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}", r"\\cancel{\1}", s)
    s = re.sub(r"\\circled\s*\{((?:[^{}]|\{[^{}]*\})*)\}", r"\\boxed{\1}", s)

    def _array(m):  # KaTeX 的 array 不认 @{...} 列修饰与可选的垂直对齐参数
        spec = re.sub(r"@\{[^{}]*\}", "", m.group(2))
        return "\\begin{array}{" + spec + "}"

    s = re.sub(r"\\begin\{array\}(\[[tbc]\])?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", _array, s)
    s = s.replace("\\/", "").replace("\\mbox{", "\\text{")
    # \minor{A}{ij} / \cofactor{A}{ij}：第一个参数只为排版服务，KaTeX 宏表达不了「丢掉第一个参数」
    for name, sym in (("minor", "M"), ("cofactor", "C")):
        s = re.sub(r"\\" + name + r"\{[^{}]*\}\{([^{}]*)\}", sym + r"_{\1}", s)
    return s.strip()


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


def text_to_md(t: str) -> str:
    t = drop_cmd(t, "index")
    t = drop_cmd(t, "eindex")
    t = NOISE.sub(" ", t)
    t = unwrap_cmd(t, "textbf", "**", "**")
    t = unwrap_cmd(t, "emph", "*", "*")
    t = unwrap_cmd(t, "textit", "*", "*")
    t = unwrap_cmd(t, "textsl", "*", "*")
    t = unwrap_cmd(t, "textrm", "", "")
    t = unwrap_cmd(t, "mbox", "", "")
    t = unwrap_cmd(t, "text", "", "")
    t = unwrap_cmd(t, "url", "", "")
    t = unwrap_cmd(t, "texttt", "`", "`")
    t = unwrap_cmd(t, "footnote", " 〔注：", "〕")
    t = unwrap_group_font(t, "em", "*", "*")
    t = unwrap_group_font(t, "it", "*", "*")
    t = unwrap_group_font(t, "bf", "**", "**")
    # 交叉引用：书页码在界面里没有意义，只保留「见某处」的位置感
    t = re.sub(r"\\eqref\{([^}]*)\}", lambda m: f"({EQMAP[m.group(1)]})" if m.group(1) in EQMAP else "〔引用〕", t)

    def _ref(m):
        slug = m.group(2).split(":", 1)[-1]
        hit = LABELS.get(slug)
        return f"“{hit[1]}”" if hit else "〔引用〕"

    t = re.sub(r"\\(ref|autoref|cref|Cref)\{([^}]*)\}", _ref, t)
    t = re.sub(r"\\hyperref\[[^\]]*\]\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\RREF\b\s*\\?", "Reduced Echelon Form ", t)
    t = re.sub(r"\\Rref\b\s*\\?", "Reduced echelon form ", t)
    t = re.sub(r"\\rref\b\s*\\?", "reduced echelon form ", t)
    t = re.sub(r"\\EF\b\s*\\?", "Echelon Form ", t)
    t = re.sub(r"\\Ef\b\s*\\?", "Echelon form ", t)
    t = re.sub(r"\\ef\b\s*\\?", "echelon form ", t)
    t = t.replace("``", "“").replace("''", "”").replace("---", "—").replace("--", "–")
    t = t.replace("\\&", "&").replace("\\%", "%").replace("\\#", "#").replace("\\$", "＄")
    t = t.replace("\\ldots", "…").replace("\\dots", "…").replace("\\\\", " ")
    t = re.sub(r"\\q?quad\b", " ", t)
    t = re.sub(r"\\[,;:! ]", " ", t)
    t = t.replace("~", " ")
    t = re.sub(r"[{}]", "", t)
    return t


def inline(t: str) -> str:
    """行内文字 → 轻量标记：**粗体** *斜体* $公式$。空白折叠成单个空格。"""
    t = drop_cmd(drop_cmd(t, "index"), "eindex")
    t = re.sub(r"\\textbf(?=[A-Za-z])([A-Za-z]+)", r"\\textbf{\1}", t)  # 上游笔误 \textbfword
    out = []
    for kind, s in split_math(t):
        if kind == "m":
            out.append("$" + clean_math(s) + "$")
        else:
            out.append(text_to_md(s))
    r = "".join(out)
    r = re.sub(r"[ \t\r\n]+", " ", r).strip()
    r = re.sub(r"\s+([,.;:!?])", r"\1", r)
    return r


def sha(en: str) -> str:
    return hashlib.sha1(en.encode("utf-8")).hexdigest()[:12]


def unit(en: str) -> dict:
    return {"en": en, "sha": sha(en), "zh": ""}


# ── 块解析 ────────────────────────────────────────────


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


def paragraphs(text: str) -> list[dict]:
    """没有块环境的文字 → 展示公式块 + 段落块。"""
    blocks: list[dict] = []
    # 先抽出 \[ \] 与 $$ $$
    pat = re.compile(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$", re.S)
    pos = 0
    chunks: list[tuple[str, str]] = []
    for m in pat.finditer(text):
        chunks.append(("t", text[pos : m.start()]))
        chunks.append(("m", m.group(1) if m.group(1) is not None else m.group(2)))
        pos = m.end()
    chunks.append(("t", text[pos:]))
    for kind, s in chunks:
        if kind == "m":
            blocks.append({"k": "math", "tex": clean_math(s)})
            continue
        for para in re.split(r"\n\s*\n", s):
            h = re.match(r"\s*\\(subsection|subsubsection|paragraph|section)\*?\s*\{", para)
            if h:
                a, _ = read_args(para, h.end() - 1, 1)
                blocks.append({"k": "heading", "t": unit(inline(a[0]))})
                continue
            en = inline(para)
            if en:
                blocks.append({"k": "p", "t": unit(en)})
    return blocks


def split_items(body: str) -> list[str]:
    """按顶层 \\item 切列表项（嵌套的列表环境里的 \\item 不切）。"""
    items: list[str] = []
    depth = 0
    cur = []
    i = 0
    while i < len(body):
        if body.startswith("\\begin{", i) and re.match(r"\\begin\{(enumerate|itemize|enumialphparenastyle)\}", body[i:]):
            depth += 1
        elif body.startswith("\\end{", i) and re.match(r"\\end\{(enumerate|itemize|enumialphparenastyle)\}", body[i:]):
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


FIG_DIR = ROOT / "content" / "figures"
TIKZ_RE = re.compile(r"\\begin\{(tikzpicture|circuitikz)\}")


def tikz_sources(body: str) -> list[str]:
    """body 里全部 tikzpicture / circuitikz 的完整源码（含 \\begin…\\end，已去注释）。"""
    out = []
    pos = 0
    while True:
        m = TIKZ_RE.search(body, pos)
        if not m:
            return out
        end_start, end_after = find_end(body, m.group(1), m.end())
        out.append(body[m.start():end_after])
        pos = end_after


def figure_block(env: str, body: str) -> dict:
    """图块：每幅 TikZ 以源码指纹命名，源码存 content/figures/src/<sha>.tex，svg 由 render_figures.py 生成。"""
    figs = []
    for src in tikz_sources(body):
        norm = re.sub(r"\s+", " ", src).strip()
        f = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]
        figs.append(f)
        PENDING_FIGS[f] = src
    cap = re.search(r"\\caption\{", body)
    note = ""
    if cap:
        a, _ = read_args(body, cap.end() - 1, 1)
        note = inline(a[0])
    return {"k": "figure", "env": env, "figs": figs, "caption": unit(note) if note else None}


PENDING_FIGS: dict[str, str] = {}


def parse_blocks(t: str) -> list[dict]:
    blocks: list[dict] = []
    pos = 0
    while True:
        m = BEGIN_RE.search(t, pos)
        if not m:
            blocks += paragraphs(t[pos:])
            return blocks
        blocks += paragraphs(t[pos : m.start()])
        env = m.group(1)
        end_start, end_after = find_end(t, env, m.end())
        body = t[m.end() : end_start]
        pos = end_after
        if env in BOX_ENVS:
            args, j = read_args(body, 0, 2)
            blocks.append({"k": "box", "env": env, "title": unit(inline(args[0])) if args and args[0].strip() else None,
                           "blocks": parse_blocks(body[j:])})
        elif env in ("solution", "proof", "proofof", "sol"):
            title = None
            if env == "proofof":
                args, j = read_args(body, 0, 1)
                title = unit(inline(args[0])) if args else None
                body = body[j:]
            blocks.append({"k": env if env != "sol" else "solution", "title": title, "blocks": parse_blocks(body)})
        elif env == "outcome":
            blocks.append({"k": "outcome", "blocks": parse_blocks(body)})
        elif env in LIST_ENVS:
            blocks.append({"k": "list", "ordered": env != "itemize",
                           "items": [parse_blocks(it) for it in split_items(body)]})
        elif env in MATH_ENVS and "\\begin{tikzpicture}" in body:
            blocks.append(figure_block("tikzpicture", body))
        elif env in MATH_ENVS:
            tex = clean_math(body)
            if env.startswith("eqnarray"):
                tex = "\\begin{array}{rcl}" + tex.replace("&=&", "&=&") + "\\end{array}"
            elif env.startswith("align"):
                tex = "\\begin{aligned}" + tex + "\\end{aligned}"
            blocks.append({"k": "math", "tex": tex})
        elif env in FIGURE_ENVS:
            blocks.append(figure_block(env, f"\\begin{{{env}}}{body}\\end{{{env}}}" if env != "figure" else body))
        elif env in TABLE_ENVS:
            args, j = read_args(body, 0, 1)
            blocks.append(parse_table(args[0] if args else "", body[j:]))
        elif env in TRANSPARENT_ENVS:
            blocks += parse_blocks(body)
        else:  # ex 只会出现在习题文件里，由 parse_exercises 处理
            blocks += parse_blocks(body)


def parse_table(spec: str, body: str) -> dict:
    """tabular → 行列；含英文单词的单元格是可译单元，纯数字/公式单元格原样保留。"""
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
    t = strip_comments(t)
    out: list[dict] = []
    pos = 0
    n = 0
    while True:
        m = re.compile(r"\\begin\{ex\}").search(t, pos)
        if not m:
            return out
        end_start, end_after = find_end(t, "ex", m.end())
        body = t[m.end() : end_start]
        pos = end_after
        n += 1
        sm = re.search(r"\\begin\{sol\}", body)
        if sm:
            se, _ = find_end(body, "sol", sm.end())
            stem = parse_blocks(body[: sm.start()])
            sol = parse_blocks(body[sm.end() : se])
        else:
            stem, sol = parse_blocks(body), []
        out.append({"id": f"ex{n}", "stem": stem, "sol": sol})


# ── 课表与书序 ────────────────────────────────────────


def book_order() -> dict[str, list[str]]:
    """courseSetup.tex：每个 content 文件之后跟着哪些 exercises 文件。"""
    pair: dict[str, list[str]] = {}
    cur = None
    for line in (UP / "courseSetup.tex").read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"\s*\\input\s+content/([\w-]+)\.tex", line)
        if m:
            cur = m.group(1)
            pair.setdefault(cur, [])
            continue
        m = re.match(r"\s*\\input\s+exercises/([\w-]+)\.tex", line)
        if m and cur:
            pair[cur].append(m.group(1))
    return pair


def section_title(t: str) -> str:
    m = re.search(r"\\(?:chapter|section|subsection)\*?\s*(?=\{)", t)
    if not m:
        return ""
    a, _ = read_args(t, m.end(), 1)
    s = a[0]
    # \texorpdfstring{$\R^n$}{Rn} → 取 TeX 版
    s = re.sub(r"\\texorpdfstring\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{[^}]*\}", r"\1", s)
    return inline(s)


def units(blocks: list[dict]):
    """遍历块流里全部可译单元（文档顺序）。"""
    for b in blocks:
        for key in ("t", "title", "caption"):
            if isinstance(b.get(key), dict) and "sha" in b[key]:
                yield b[key]
        for key in ("blocks",):
            if key in b:
                yield from units(b[key])
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


def build_section(sec_id: str, pair: dict[str, list[str]]) -> dict:
    src = (UP / "content" / f"{sec_id}.tex").read_text(encoding="utf-8", errors="ignore")
    raw = strip_comments(src)
    EQMAP.clear()
    used = set(re.findall(r"\\eqref\{([^}]*)\}", raw))
    for ex_name in pair.get(sec_id, []):
        p = UP / "exercises" / f"{ex_name}.tex"
        if p.is_file():
            used |= set(re.findall(r"\\eqref\{([^}]*)\}", p.read_text(encoding="utf-8", errors="ignore")))
    for lab in re.findall(r"\\label\{([^}]*)\}", raw):
        if lab in used and lab not in EQMAP:
            EQMAP[lab] = len(EQMAP) + 1
    data = {
        "id": sec_id,
        "title_en": section_title(raw),
        "blocks": parse_blocks(raw),
        "exercises": [],
    }
    for ex_name in pair.get(sec_id, []):
        p = UP / "exercises" / f"{ex_name}.tex"
        if p.is_file():
            for k, ex in enumerate(parse_exercises(p.read_text(encoding="utf-8", errors="ignore")), 1):
                ex["file"], ex["no_in_file"] = ex_name, k
                data["exercises"].append(ex)
    # 习题 id 在整节内连续编号；出处逐题记录（题面逐字取自原书，relation=verbatim）
    for i, ex in enumerate(data["exercises"], 1):
        ex["id"] = f"ex{i}"
        fname, no = ex.pop("file"), ex.pop("no_in_file")
        ex["source_refs"] = [{
            "relation": "verbatim",
            "site": "Selinger《Linear Algebra: A First Course》（CC BY 4.0 开源教材）",
            "locator": f"{data['title_en']} · 习题 {no}（上游 exercises/{fname}.tex）",
            "url": f"https://github.com/selinger/linear-algebra/blob/master/baseText/exercises/{fname}.tex",
        }]
    # 开头的节标题块就是页面标题本身，不重复
    if data["blocks"] and data["blocks"][0]["k"] == "heading":
        data["blocks"] = data["blocks"][1:]
    return data


def zh_progress(data: dict) -> tuple[int, int]:
    us = list(units(data["blocks"])) + [u for ex in data["exercises"] for u in units(ex["stem"] + ex["sol"])]
    done = sum(1 for u in us if u.get("zh"))
    return done, len(us)


def main() -> int:
    check = "--check" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    scope = json.loads((ROOT / "content" / "scope.json").read_text(encoding="utf-8"))
    pair = book_order()
    scan_labels()
    OUT.mkdir(parents=True, exist_ok=True)
    bad = 0
    curriculum = {"chapters": []}
    for ch in scope["chapters"]:
        ch_src = (UP / "content" / f"{ch['id']}.tex").read_text(encoding="utf-8", errors="ignore")
        entry = {"id": ch["id"], "title_en": section_title(strip_comments(ch_src)), "title_zh": ch["zh"], "items": []}
        for it in ch["items"]:
            item = {"id": it["id"], "level": it["level"], "title_zh": it["zh"], "page": it["page"]}
            path = OUT / f"{it['id']}.json"
            if it["page"]:
                if only and it["id"] not in only and path.is_file():
                    data = json.loads(path.read_text(encoding="utf-8"))
                else:
                    data = build_section(it["id"], pair)
                    old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
                    carry_over(old, data)
                    data["title_zh"] = it["zh"]
                    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
                    if check:
                        if not path.is_file() or path.read_text(encoding="utf-8") != text:
                            print(f"快照与上游不一致：{it['id']}（跑 sync_upstream.py 更新）")
                            bad += 1
                    else:
                        path.write_text(text, encoding="utf-8")
                done, total = zh_progress(data)
                item["title_en"] = data["title_en"]
                item["units"] = total
                item["translated"] = done
                item["exercises"] = len(data["exercises"])
            else:
                src = (UP / "content" / f"{it['id']}.tex").read_text(encoding="utf-8", errors="ignore")
                item["title_en"] = section_title(strip_comments(src))
            entry["items"].append(item)
        curriculum["chapters"].append(entry)
    if not check:
        (FIG_DIR / "src").mkdir(parents=True, exist_ok=True)
        for f, src in PENDING_FIGS.items():
            (FIG_DIR / "src" / f"{f}.tex").write_text(src.strip() + "\n", encoding="utf-8")
        (ROOT / "content" / "curriculum.json").write_text(
            json.dumps(curriculum, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n = sum(1 for c in curriculum["chapters"] for i in c["items"] if i["page"])
        u = sum(i.get("units", 0) for c in curriculum["chapters"] for i in c["items"])
        e = sum(i.get("exercises", 0) for c in curriculum["chapters"] for i in c["items"])
        print(f"{n} 个节页，{u} 个可译单元，{e} 道习题")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
