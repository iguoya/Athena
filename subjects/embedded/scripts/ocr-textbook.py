#!/usr/bin/env python3
"""教材 OCR 数据化:扫描版 PDF → 按页文本,供「教材原文」融入软件。

两本官方教材均为扫描版(无文本层),用 rapidocr 逐页识别。输出按页存放:
    <outdir>/p<N>.txt   (N 为 PDF 页码,补零三位)

识别为印刷体中文,准确率约 95%+,个别形近字有误(如「事件→率件」);
作为教材原文的机器转录,编写内容时以图为准校正关键数字与术语。

用法:
    python3 scripts/ocr-textbook.py <pdf路径> <输出目录> [起始页 结束页]
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pymupdf
from rapidocr_onnxruntime import RapidOCR


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    _force_utf8_output()
    pdf_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    end = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf_path))
    ocr = RapidOCR()

    total = min(end, doc.page_count)
    done = 0
    for i in range(start - 1, total):
        out_file = out_dir / f"p{i + 1:03d}.txt"
        if out_file.is_file() and out_file.stat().st_size > 0:
            continue  # 断点续跑:已有非空结果跳过
        pix = doc[i].get_pixmap(dpi=200)
        img = str(Path(tempfile.gettempdir()) / f"ocr-page-{os.getpid()}.png")
        pix.save(img)
        result, _ = ocr(img)
        text = "\n".join(line[1] for line in result) if result else ""
        out_file.write_text(text, encoding="utf-8")
        done += 1
        if done % 10 == 0:
            print(f"进度: {i + 1}/{total}", flush=True)
    print(f"完成: 本次识别 {done} 页,输出目录 {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
