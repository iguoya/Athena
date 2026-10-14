#!/usr/bin/env python3
"""从上游（SymPy 官方教程，reStructuredText）生成段落快照与课表。

  python3 scripts/sync_upstream.py            重新生成 content/sections/*.json 与 content/curriculum.json
  python3 scripts/sync_upstream.py --check    只核对快照与上游是否一致（check.py 调用）
  python3 scripts/sync_upstream.py <页 id>…   只重新生成这几页

上游克隆在 upstream/sympy（gitignore，稀疏检出 doc/src/tutorials/intro-tutorial），基准提交记在 upstream.json。

每个可译单元是 {en, sha, zh}：en 是上游原文（rst 行内标记规整成 markdown 风格，公式用 $…$、代码用 `…`），
sha 是 en 的指纹，zh 是手写译文。重新同步时按指纹把已有译文带过来；原文变了的，旧译文放进 stale_zh，不悄悄当最新的。

代码块（`>>>` 交互式会话、`::` 字面块）逐字保留，不翻译、不产生可译单元。
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UP = ROOT / "upstream" / "sympy" / "doc" / "src" / "tutorials" / "intro-tutorial"
OUT = ROOT / "content" / "sections"
EXERCISES = ROOT / "content" / "exercises"


def sha(en: str) -> str:
    return hashlib.sha1(en.encode("utf-8")).hexdigest()[:12]


def unit(en: str) -> dict:
    return {"en": en, "sha": sha(en), "zh": ""}


# ---------------------------------------------------------------------------------------------
# 行内标记：rst → markdown 风格（公式 $…$、代码 `…`、**粗**、*斜*）

LABEL_TITLES: dict[str, str] = {}  # `.. _label:` → 它后面那个标题，给 :ref:`label` 用

ROLE_RE = re.compile(r":(?:py:)?(func|class|meth|mod|attr|data|exc|obj|ref|math|term|doc):`([^`]+)`")
FOOTNOTE_REF_RE = re.compile(r"\[#([\w-]+)\]_")
FOOTNOTE_DEF_RE = re.compile(r"^\.\. \[#([\w-]+)\]\s*(.*)$")
FOOTNOTES: dict[str, int] = {}  # 当前页的脚注标签 → 编号（按定义顺序）
LINK_RE = re.compile(r"`([^`<]+?)\s*<([^>]+)>`_{1,2}")
NAMED_LINK_RE = re.compile(r"`([^`<]+?)`_{1,2}")


def _role(m: re.Match) -> str:
    role, body = m.group(1), m.group(2)
    if role == "math":
        return f"$ {body.strip()} $".replace("$ ", "$").replace(" $", "$")
    m2 = re.match(r"^(.*?)\s*<([^>]+)>$", body, re.S)
    title, target = (m2.group(1).strip(), m2.group(2).strip()) if m2 else (None, body.strip())
    if role == "ref":
        return title or LABEL_TITLES.get(target, target.replace("-", " ").replace("_", " "))
    if title:
        return title  # 带显示文字的角色（`文字 <目标>`）是超链接文字，不是代码
    name = target.lstrip("~")
    if target.startswith("~") or "." in name:
        name = name.split(".")[-1] if target.startswith("~") else name
    return f"`{name}`"


def inline(text: str) -> str:
    """把一段 rst 行内标记规整成 markdown 风格。顺序要紧：先把 ``字面量`` 收起来，剩下的单反引号才是默认角色（数学）。"""
    text = re.sub(r"\s+", " ", text.strip())
    text = FOOTNOTE_REF_RE.sub(lambda m: f"[{FOOTNOTES.get(m.group(1), '?')}]", text)
    lits: list[str] = []

    def keep(m: re.Match) -> str:
        lits.append(m.group(1))
        return f"\x00{len(lits) - 1}\x00"

    text = re.sub(r"``(.+?)``", keep, text)
    text = ROLE_RE.sub(lambda m: keep_code(_role(m), lits), text)
    text = LINK_RE.sub(lambda m: f"{m.group(1).strip()}（{m.group(2).strip()}）", text)
    text = NAMED_LINK_RE.sub(lambda m: m.group(1), text)
    # 剩下的单反引号：默认角色 = 数学（SymPy 文档的 default_role）。公式内容是原样的（\\ 是换行，不是 rst 转义），先藏起来
    text = re.sub(r"(?<![`\\])`([^`]+)`(?!`)", lambda m: keep_code(f"${m.group(1).strip()}$", lits), text)
    text = re.sub(r"(?<!\\)\\ ", "", text)  # rst 里的「反斜杠加空格」只是分隔标记用的转义，不是内容
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"`{lits[int(m.group(1))]}`" if not lits[int(m.group(1))].startswith("\x01") else lits[int(m.group(1))][1:], text)
    return text


def keep_code(s: str, lits: list[str]) -> str:
    """角色输出里已经是 `代码` 或 $公式$ 的，也要藏起来，免得被后面的单反引号规则再处理。"""
    if s.startswith("`") and s.endswith("`"):
        lits.append(s[1:-1])
        return f"\x00{len(lits) - 1}\x00"
    if s.startswith("$"):
        lits.append("\x01" + s)
        return f"\x00{len(lits) - 1}\x00"
    return s


# ---------------------------------------------------------------------------------------------
# 块结构

HEAD_CHARS = "=-~^\"'`#*+"
DIRECTIVE_RE = re.compile(r"^\.\. (\w[\w-]*)::\s*(.*)$")
BULLET_RE = re.compile(r"^(\s*)([-*])\s+(.*)$")
ENUM_RE = re.compile(r"^(\s*)(\d+|#)\.\s+(.*)$")
BOX_ENVS = {"note": "note", "warning": "warning", "tip": "tip", "important": "important", "hint": "hint", "seealso": "seealso"}


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def is_underline(line: str, text: str) -> bool:
    s = line.strip()
    return bool(s) and len(set(s)) == 1 and s[0] in HEAD_CHARS and len(s) >= max(len(text.strip()), 3) - 1 and not text.strip().startswith(("..", ">>>"))


def dedent(lines: list[str], n: int) -> list[str]:
    return [l[n:] if len(l) >= n and not l[:n].strip() else l.lstrip(" ") if not l.strip() else l[n:] for l in lines]


def body_after(lines: list[str], i: int, parent_indent: int) -> tuple[list[str], int]:
    """取一个缩进体：从 i 起，空行与缩进 > parent_indent 的行；返回（行，下一个下标）。末尾空行不要。"""
    body: list[str] = []
    j = i
    while j < len(lines):
        l = lines[j]
        if l.strip() and indent_of(l) <= parent_indent:
            break
        body.append(l)
        j += 1
    while body and not body[-1].strip():
        body.pop()
    return body, j


def common_indent(lines: list[str]) -> int:
    ind = [indent_of(l) for l in lines if l.strip()]
    return min(ind) if ind else 0


def parse_table(rows: list[str]) -> dict:
    """网格表：只处理上游用到的最简形式（每个单元一行）。"""
    cells: list[list[str]] = []
    for l in rows:
        s = l.strip()
        if not s.startswith("|"):
            continue
        cells.append([c.strip() for c in s.strip("|").split("|")])
    if not cells:
        return {"k": "table", "spec": "", "rows": []}
    return {"k": "table", "spec": "grid", "rows": [[unit(inline(c)) if c else "" for c in r] for r in cells]}


def parse_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        ind = indent_of(line)
        s = line.strip()

        # 脚注定义 `.. [#label] 文字`：变成一个「[n] 文字」段落
        fm = FOOTNOTE_DEF_RE.match(s)
        if fm:
            body, i = body_after(lines, i + 1, ind)
            text = " ".join([fm.group(2)] + [l.strip() for l in body if l.strip()])
            blocks.append({"k": "p", "t": unit(f"[{FOOTNOTES.get(fm.group(1), '?')}] " + inline(text))})
            continue

        # 注释与标签：`.. _label:`、`.. 随便什么`（带缩进的续行一起丢）
        m = DIRECTIVE_RE.match(s)
        if s.startswith("..") and not m:
            body, i = body_after(lines, i + 1, ind)
            continue

        if m:
            name, arg = m.group(1).lower(), m.group(2).strip()
            body, i = body_after(lines, i + 1, ind)
            # 选项行（:maxdepth: 2 之类）
            opts = 0
            while opts < len(body) and (not body[opts].strip() or body[opts].strip().startswith(":")):
                opts += 1
            content = dedent(body[opts:], common_indent(body[opts:]) if body[opts:] else 0)
            if name in BOX_ENVS:
                inner = parse_blocks(([arg] if arg else []) + content) if arg else parse_blocks(content)
                blocks.append({"k": "box", "env": BOX_ENVS[name], "title": None, "blocks": inner})
            elif name in ("sidebar", "topic"):
                blocks.append({"k": "box", "env": "note", "title": unit(inline(arg)) if arg else None, "blocks": parse_blocks(content)})
            elif name == "math":
                tex = "\n".join(([arg] if arg else []) + [l.strip() for l in content]).strip()
                blocks.append({"k": "math", "tex": re.sub(r"\n{2,}", "\n", tex)})
            elif name == "rubric":
                blocks.append({"k": "heading", "t": unit(inline(arg))})
            # toctree、graphviz 等：丢弃（graphviz 只在被裁掉的页里用）
            continue

        # 交互式会话
        if s.startswith(">>>"):
            j = i
            code = []
            while j < n and lines[j].strip():
                code.append(lines[j])
                j += 1
            blocks.append({"k": "code", "text": "\n".join(dedent(code, ind)).rstrip()})
            i = j
            continue

        # 网格表
        if s.startswith("+-") or s.startswith("+="):
            j = i
            while j < n and lines[j].strip() and lines[j].strip()[0] in "+|":
                j += 1
            blocks.append(parse_table(lines[i:j]))
            i = j
            continue

        # 标题：「标题行 + 下划线」或「上划线 + 标题行 + 下划线」
        if i + 1 < n and is_underline(lines[i + 1], s) and not BULLET_RE.match(line) and not s.startswith("+"):
            blocks.append({"k": "heading", "t": unit(inline(s))})
            i += 2
            continue
        if len(set(s)) == 1 and s[0] in HEAD_CHARS and len(s) >= 3 and i + 2 < n and is_underline(lines[i + 2], lines[i + 1]):
            blocks.append({"k": "heading", "t": unit(inline(lines[i + 1].strip()))})
            i += 3
            continue

        # 列表
        lm = BULLET_RE.match(line) or ENUM_RE.match(line)
        if lm and not (len(set(s)) == 1 and s[0] in "-*" and len(s) > 2):
            ordered = bool(ENUM_RE.match(line))
            marker_indent = len(lm.group(1))
            items: list[list[dict]] = []
            while i < n:
                cur = lines[i]
                cm = (ENUM_RE if ordered else BULLET_RE).match(cur)
                if not cm or len(cm.group(1)) != marker_indent:
                    break
                content_indent = len(cur) - len(cm.group(3))
                item = [cur[content_indent:]]
                i += 1
                while i < n and (not lines[i].strip() or indent_of(lines[i]) > marker_indent):
                    item.append(lines[i][content_indent:] if lines[i].strip() else "")
                    i += 1
                while item and not item[-1].strip():
                    item.pop()
                items.append(parse_blocks(item))
                while i < n and not lines[i].strip():  # 列表项之间的空行
                    if i + 1 < n and (ENUM_RE if ordered else BULLET_RE).match(lines[i + 1]) and len((ENUM_RE if ordered else BULLET_RE).match(lines[i + 1]).group(1)) == marker_indent:
                        i += 1
                    else:
                        break
            blocks.append({"k": "list", "ordered": ordered, "items": items})
            continue

        # 普通段落（缩进的引用块也当段落）；以 :: 结尾的后面跟字面块
        j = i
        para = []
        while j < n and lines[j].strip():
            if j > i and (lines[j].strip().startswith(">>>") or DIRECTIVE_RE.match(lines[j].strip())):
                break
            para.append(lines[j].strip())
            j += 1
        text = " ".join(para)
        literal = text.endswith("::")
        if literal:
            text = text[:-2] if text.endswith(" ::") or text == "::" else text[:-1]
            text = text.rstrip()
        i = j
        if text:
            blocks.append({"k": "p", "t": unit(inline(text))})
        if literal:
            while i < n and not lines[i].strip():
                i += 1
            body, i = body_after(lines, i, ind)
            if body:
                blocks.append({"k": "code", "text": "\n".join(dedent(body, common_indent(body))).rstrip()})
    return blocks


# ---------------------------------------------------------------------------------------------

def collect_labels(files: list[Path]) -> None:
    for p in files:
        ls = p.read_text(encoding="utf-8").splitlines()
        for k, l in enumerate(ls):
            m = re.match(r"^\.\. _([\w:-]+):\s*$", l)
            if not m:
                continue
            j = k + 1
            while j < len(ls) and not ls[j].strip():
                j += 1
            if j < len(ls) and re.fullmatch(r"[=\-~^]{3,}", ls[j].strip()) and j + 1 < len(ls):
                LABEL_TITLES[m.group(1)] = ls[j + 1].strip()
            elif j + 1 < len(ls):
                LABEL_TITLES[m.group(1)] = ls[j].strip()


def section_data(pid: str) -> dict:
    src = (UP / f"{pid}.rst").read_text(encoding="utf-8")
    FOOTNOTES.clear()
    for k, label in enumerate(re.findall(r"^\.\. \[#([\w-]+)\]", src, re.M), 1):
        FOOTNOTES[label] = k
    blocks = parse_blocks(src.splitlines())
    # 页标题：第一块标题；它不放进正文，界面另显
    assert blocks and blocks[0]["k"] == "heading", f"{pid}: 没找到页标题"
    title_en = blocks[0]["t"]["en"]
    return {"id": pid, "title_en": title_en, "blocks": blocks[1:]}


def units(blocks: list[dict]):
    for b in blocks:
        for key in ("t", "title"):
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
    """把旧快照的译文带到新快照：先按指纹；指纹变了的按位置对齐，旧译文放进 stale_zh（zh 留空），由人确认后写回。"""
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
    collect_labels(sorted(UP.glob("*.rst")))
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
                data = section_data(pid)
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
