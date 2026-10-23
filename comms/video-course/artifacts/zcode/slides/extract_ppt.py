# -*- coding: utf-8 -*-
"""T-001 课件逐页文本快照抽取（PowerPoint COM，Windows + 装有 PowerPoint 的机器）。

用法：
  python -X utf8 extract_ppt.py <解包目录> <rar路径> <输出目录> [序言|第１章|附录 ...]

不选中任何章时依次处理全部三份（序言 / 第１章 / 附录）。
输出 JSON 结构见任务书 T-001；页内文本逐字（\r/\v 统一为 \n，保留原有空格），
MathType 等公式 OLE 对象拿不到文字，按 figures 计数并在该页加 note=公式重排。
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pythoncom
import win32com.client

PROG_RE = re.compile(r"\bpla\s?(\d{3}[a-z]?)\b", re.I)

# MsoShapeType
TABLE, PICTURE, EMBED_OLE, GROUP = 19, 13, 7, 6


def clean(t: str) -> str:
    return t.replace("\r", "\n").replace("\v", "\n").replace("\x0b", "\n")


CODE_LINE = re.compile(
    r"(^%|^>>|[A-Za-z0-9]\s*=[^=]|[;,\[]\s*$|\brref\b|\bref1\b|\bref2\b|\bplot\b|"
    r"\bdisp\b|\bformat\b|\bclear\b|\binv\b|\beye\b|\bzeros\b|\bones\b|\binput\b)",
    re.I,
)


def code_block(text: str) -> str:
    """行级筛出疑似 MATLAB 代码行；含中文的行只保留 % 注释与 >> 提示。"""
    keep = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if re.search(r"[\u4e00-\u9fff]", s):
            if s.startswith("%") or ">>" in s:
                keep.append(line.rstrip())
            continue
        if CODE_LINE.search(s):
            keep.append(line.rstrip())
    return "\n".join(keep)


def walk(shapes, texts, figs, ole_count):
    for i in range(1, shapes.Count + 1):
        sh = shapes.Item(i)
        try:
            stype = sh.Type
        except Exception:
            continue
        if stype == GROUP:
            walk(sh.GroupItems, texts, figs, ole_count)
            continue
        has_text = False
        try:
            if sh.HasTextFrame and sh.TextFrame.HasText:
                texts.append(clean(sh.TextFrame.TextRange.Text))
                has_text = True
        except Exception:
            pass
        if not has_text and stype == TABLE:
            try:
                tbl = sh.Table
                for r in range(1, tbl.Rows.Count + 1):
                    cells = [
                        clean(tbl.Cell(r, c).Shape.TextFrame.TextRange.Text)
                        for c in range(1, tbl.Columns.Count + 1)
                    ]
                    texts.append(" | ".join(cells))
            except Exception:
                pass
        if stype == PICTURE:
            figs.append(str(sh.Name))
        if stype == EMBED_OLE:
            ole_count[0] += 1
            figs.append("OLE对象(公式或其他,文本不可提取)")


def extract(app, src: Path) -> list:
    pres = app.Presentations.Open(str(src), WithWindow=False, ReadOnly=True)
    pages = []
    try:
        for i in range(1, pres.Slides.Count + 1):
            slide = pres.Slides.Item(i)
            title, texts, figs, ole = "", [], [], [0]
            try:
                if slide.Shapes.HasTitle:
                    title = clean(slide.Shapes.Title.TextFrame.TextRange.Text)
            except Exception:
                pass
            walk(slide.Shapes, texts, figs, ole)
            body = [t for t in texts if t.strip() and t.strip() != title.strip()]
            codes = [
                block for block in (code_block(t) for t in body) if block.strip()
            ]
            page = {
                "page": i,
                "title": title,
                "text": "\n".join(body),
                "figures": figs,
                "code": codes,
                "program_refs": sorted(
                    {f"pla{m.group(1)}" for t in texts for m in PROG_RE.finditer(t)}
                ),
            }
            if ole[0]:
                page["note"] = "公式重排"
            pages.append(page)
    finally:
        pres.Close()
    return pages


def main():
    unpack_dir, rar_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    wanted = sys.argv[4:] or ["序言", "第１章", "附录"]
    rar_sha = hashlib.sha256(rar_path.read_bytes()).hexdigest()
    unpack = unpack_dir / "实用大众线性代数课件"
    files = {
        "序言": unpack / "实用大众线性代数课件序言.ppt",
        "第１章": unpack / "实用大众线性代数课件第１章.ppt",
        "第２章": unpack / "实用大众线性代数课件第２章.ppt",
        "第３章": unpack / "实用大众线性代数课件第３章.ppt",
        "第４章": unpack / "实用大众线性代数课件第４章.ppt",
        "第５章": unpack / "实用大众线性代数课件第５章.ppt",
        "第６章": unpack / "实用大众线性代数课件第６章.ppt",
        "附录": unpack / "实用大众线性代数课件附录.ppt",
    }
    names = {
        "序言": "preface",
        "第１章": "ch1",
        "第２章": "ch2",
        "第３章": "ch3",
        "第４章": "ch4",
        "第５章": "ch5",
        "第６章": "ch6",
        "附录": "appendix-a",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("PowerPoint.Application")
    for key in wanted:
        src = files[key]
        pages = extract(app, src)
        doc = {"source": src.name, "sha256_of_rar": rar_sha, "pages": pages}
        out = out_dir / f"{names[key]}.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        n_notes = sum(1 for p in pages if "note" in p)
        print(f"{key}: {len(pages)} 页 -> {out}（含公式重排标注 {n_notes} 页）")
        for p in pages:
            flag = "!" if not p["text"].strip() else " "
            print(
                f"  {flag}p{p['page']:>2} fig={len(p['figures'])} "
                f"code={len(p['code'])} refs={p['program_refs']} | {p['title'][:36]}"
            )


if __name__ == "__main__":
    main()
