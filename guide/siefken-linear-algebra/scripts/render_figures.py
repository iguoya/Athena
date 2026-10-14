#!/usr/bin/env python3
"""把 content/figures/src/*.tex（TikZ 源码，由 sync_upstream.py 抽出）编译成 content/figures/<sha>.svg。

需要本机装有 TeX（pdflatex + tikz/pgfplots/circuitikz）与 pdf2svg。这是开发期一次性工作，产物入库，
所以使用者不需要装 TeX；上游图变了才重跑。已有 svg 且源码未变的不重编（svg 旁不存指纹：文件名就是源码指纹）。

用法：python3 scripts/render_figures.py [--force] [指纹 ...]
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "figures" / "src"
OUT = ROOT / "content" / "figures"
PREAMBLE = (ROOT / "figures-preamble.tex").read_text(encoding="utf-8")


def scale_root(svg: str, k: float) -> str:
    """只放大根 <svg> 的 width/height（viewBox 不变，内容随之等比放大）。"""
    def fix(m: re.Match) -> str:
        return re.sub(r'\b(width|height)="([\d.]+)(pt|px)?"',
                      lambda a: f'{a.group(1)}="{float(a.group(2)) * k:.2f}{a.group(3) or ""}"', m.group(0))
    return re.sub(r'<svg\b[^>]*>', fix, svg, count=1)


def namespace_ids(svg: str, sha: str) -> str:
    """pdf2svg 每幅图里的 id（glyph0-1、clip1 …）都从头编号；多幅 SVG 内联进同一个页面时会互相覆盖，
    字形串到别的图上（文字变成乱码）。给每个 id 及其引用加上图自己的指纹前缀。"""
    svg = scale_root(svg, 1.7)  # TikZ 图按印刷 pt 出图，屏幕上偏小，放大到可读
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    for i in sorted(ids, key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{sha}-{i}"')
        svg = svg.replace(f'href="#{i}"', f'href="#{sha}-{i}"')
        svg = svg.replace(f'url(#{i})', f'url(#{sha}-{i})')
    return svg


def render(sha: str) -> str | None:
    """成功返回 None，失败返回错误摘要。"""
    body = (SRC / f"{sha}.tex").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / "f.tex"
        tex.write_text(PREAMBLE + body + "\n\\end{document}\n", encoding="utf-8")
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "f.tex"], cwd=d,
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not (Path(d) / "f.pdf").is_file():
            lines = [l for l in r.stdout.splitlines() if l.startswith("!") or "Error" in l]
            return "; ".join(lines[:2]) or "pdflatex 失败"
        r2 = subprocess.run(["pdf2svg", "f.pdf", "f.svg"], cwd=d, capture_output=True, text=True)
        if r2.returncode != 0:
            return "pdf2svg 失败：" + r2.stderr[:100]
        (OUT / f"{sha}.svg").write_text(namespace_ids((Path(d) / "f.svg").read_text(encoding="utf-8"), sha), encoding="utf-8")
    return None


def main() -> int:
    for tool in ("pdflatex", "pdf2svg"):
        if shutil.which(tool) is None:
            print(f"缺 {tool}：Linux 上 sudo apt-get install texlive-latex-extra texlive-pictures texlive-science pdf2svg")
            return 2
    force = "--force" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    shas = only or sorted(p.stem for p in SRC.glob("*.tex"))
    bad = 0
    for sha in shas:
        if (OUT / f"{sha}.svg").is_file() and not force:
            continue
        err = render(sha)
        if err:
            print(f"✗ {sha}: {err}")
            bad += 1
        else:
            print(f"✓ {sha}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
