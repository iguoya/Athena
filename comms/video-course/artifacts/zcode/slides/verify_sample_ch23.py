# -*- coding: utf-8 -*-
"""T-006 抽查：用 COM 独立重读第 2–3 章 5 页与 ch2/ch3.json 逐字比对（验收证据）。

与 verify_sample.py（T-001）同款逻辑，仅换 CHECKS。用法：
  python -X utf8 verify_sample_ch23.py <解包目录>
"""
import json
import sys
from pathlib import Path

import pythoncom
import win32com.client

CHECKS = [
    ("ch2", 34, "实用大众线性代数课件第２章.ppt"),  # 代码页（例2.11）
    ("ch2", 44, "实用大众线性代数课件第２章.ppt"),  # 例2.18 航线图（图文混排）
    ("ch2", 50, "实用大众线性代数课件第２章.ppt"),  # 章末要求页（长文本）
    ("ch3", 17, "实用大众线性代数课件第３章.ppt"),  # 3.3 性质（公式重排页）
    ("ch3", 24, "实用大众线性代数课件第３章.ppt"),  # 克莱姆法则（数学式 code 块页）
]


def clean(t: str) -> str:
    return t.replace("\r", "\n").replace("\v", "\n").replace("\x0b", "\n")


def read_slide(app, path, idx):
    pres = app.Presentations.Open(str(path), WithWindow=False, ReadOnly=True)
    slide = pres.Slides.Item(idx)
    title, texts = "", []
    try:
        if slide.Shapes.HasTitle:
            title = clean(slide.Shapes.Title.TextFrame.TextRange.Text)
    except Exception:
        pass
    for i in range(1, slide.Shapes.Count + 1):
        sh = slide.Shapes.Item(i)
        got = False
        try:
            if sh.HasTextFrame and sh.TextFrame.HasText:
                t = clean(sh.TextFrame.TextRange.Text)
                if t.strip() and t.strip() != title.strip():
                    texts.append(t)
                    got = True
        except Exception:
            pass
        if not got and sh.Type == 19:  # msoTable，与 extract_ppt.py 的处理一致
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
    pres.Close()
    return title, "\n".join(texts)


def main():
    base = Path(sys.argv[1]) / "实用大众线性代数课件"
    slides_dir = Path(__file__).parent
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch("PowerPoint.Application")
    allok = True
    for name, idx, f in CHECKS:
        d = json.loads((slides_dir / f"{name}.json").read_text(encoding="utf-8"))
        page = next(p for p in d["pages"] if p["page"] == idx)
        title, text = read_slide(app, base / f, idx)
        ok = page["title"] == title and page["text"] == text
        allok &= ok
        print(f"{name} p{idx}: title一致={page['title'] == title} "
              f"text逐字一致={page['text'] == text} ({len(text)}字符)")
    print("抽查 5/5 全部一致" if allok else "存在差异！")
    raise SystemExit(0 if allok else 1)


if __name__ == "__main__":
    main()
