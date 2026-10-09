#!/usr/bin/env python3
"""软考真题导入管线:qicoder 电子书(GitBook)→ 应用卷子格式。

来源:https://ebook.qicoder.com 的嵌入式系统设计师历年真题电子书,页面自带
「试题答案」「试题解析」,是判分内容里出处最硬的形态(ADR 0043 的 verbatim)。
已入库的 11 卷(2010–2020)全部经这条管线导入;PDF 核对副本来源待登记到
sources.json 后再启用,不凭印象填仓库地址。

页面结构(GitBook 静态 HTML,中文为 HTML 实体):
    <h3>第 N 题</h3> → 题干 <p> → 选项 <blockquote><ul><li>(A) …</li>…</ul></blockquote>
    → <strong>答案与解析</strong> → <ul><li>试题难度：… / 知识点：… / 试题答案：[['A']] / 试题解析：…</li></ul>

复合题(一题多空,试题答案为 [['A'],['C']] 形态)第一版跳过:应用考核单元
是四选一单选,多空题等考核形态扩展后再处理。

用法:
    python3 scripts/import-past-exam.py --list
    python3 scripts/import-past-exam.py --from-url "嵌入式/2021年嵌入式系统设计师考试上午真题.html" \
        --paper-id past-exam-esd-202105 --year 2021 --session 上半年 --subject 嵌入式系统设计师·综合知识
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAST_EXAMS = PROJECT_ROOT / "content" / "past-exams"
BASE = "https://ebook.qicoder.com"

LETTERS = {"A": 0, "B": 1, "C": 2, "D": 3}


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def encode_url(url: str) -> str:
    """路径段里的中文/空格做百分号编码,协议与斜杠保留。"""
    parts = url.split("/")
    return "/".join(p if (i < 3 or not re.search(r"[^\x00-\x7F]", p)) else urllib.parse.quote(p)
                    for i, p in enumerate(parts))


def fetch(url: str) -> str:
    req = urllib.request.Request(encode_url(url), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(fragment: str) -> str:
    """去标签 + 解实体,压平空白。"""
    t = re.sub(r"<br\s*/?>", " ", fragment)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def list_papers() -> None:
    index = fetch(f"{BASE}/软件设计师")
    links = re.findall(r'href="(/?[^"]*?notes/[^"]+\.html)"[^>]*>([^<]+)<', index)
    if not links:
        links = [(m, m) for m in re.findall(r'"([^"]*notes/[^"]+\.html)"', index)]
    print(f"可导入的卷子({len(links)} 个页面):")
    for href, title in links:
        print(f"  {html.unescape(title)}\n    -> {href}")


def parse_paper(html_text: str) -> tuple[list[dict], list[int]]:
    text = html.unescape(html_text)
    # 按 <h3> 切块;每块应是「第 N 题」
    chunks = re.split(r"<h3[^>]*>", text)
    questions: list[dict] = []
    skipped: list[int] = []
    for chunk in chunks[1:]:
        # h3 开标签与标题文字之间隔着锚点链接的一串图标 HTML,窗口放大到 500
        head = re.match(r"\s*第\s*(\d+)\s*题", strip_tags(chunk[:500]))
        if not head:
            continue
        no = int(head.group(1))
        if "试题答案" not in chunk:
            skipped.append(no)
            continue
        # 试题答案:[[\'A\']] → 判定单空/多空
        ans_m = re.search(r"试题答案[:：]\s*(\[\[.*?\]\])", chunk)
        if not ans_m:
            skipped.append(no)
            continue
        letters = re.findall(r"'([A-D])'", ans_m.group(1))
        if len(letters) != 1:
            skipped.append(no)  # 多空复合题:考核形态扩展后再处理
            continue

        # 题干:第一个 <p>(到 <blockquote> 或 <strong> 之前)
        stem_m = re.search(r"<p>(.*?)</p>", chunk, re.S)
        stem = strip_tags(stem_m.group(1)) if stem_m else ""
        # 选项:<li>(A) …</li>
        options = []
        for m in re.finditer(r"<li>\s*\(([A-D])\)\s*(.*?)</li>", chunk, re.S):
            options.append(strip_tags(m.group(2)))
        # 知识点与解析
        know_m = re.search(r"知识点[:：]\s*(.*?)</li>", chunk, re.S)
        know = strip_tags(know_m.group(1)) if know_m else ""
        expl_m = re.search(r"试题解析[:：]\s*(.*?)</li>", chunk, re.S)
        explanation = strip_tags(expl_m.group(1)) if expl_m else ""

        if len(options) != 4 or not stem:
            skipped.append(no)
            continue
        questions.append({
            "id": f"q{no}",
            "no": no,
            "stem": stem,
            "options": options,
            "answer": LETTERS[letters[0]],
            "explanation": explanation,
            "knowledge": know,
        })
    return questions, skipped


def import_paper(arguments) -> None:
    url = arguments.from_url
    if not url.startswith("http"):
        if url.startswith("notes/"):
            url = f"{BASE}/软件设计师/{url.lstrip('/')}"
        else:
            url = f"{BASE}/{url.lstrip('/')}"
    print(f"拉取 {url}", flush=True)
    html_text = fetch(url)

    questions, skipped = parse_paper(html_text)
    if not questions:
        raise SystemExit("没有解析出任何题目:页面结构可能变了,先人工看一眼 HTML")
    print(f"解析出 {len(questions)} 题,跳过多空/缺答案题 {len(skipped)} 道:{skipped}", flush=True)

    paper = {
        "id": arguments.paper_id,
        "title": arguments.title or f"{arguments.year} 年{arguments.session} {arguments.subject}",
        "year": arguments.year,
        "session": arguments.session,
        "subject": arguments.subject,
        "source_note": "软考真题电子书(qicoder)整理,题目与答案 verbatim",
        "source_ref": {"relation": "verbatim", "sourceId": "past-exam-web-qicoder",
                        "locator": arguments.from_url},
        "questions": [
            {
                "id": f"{arguments.paper_id}.{q['id']}",
                "no": q["no"],
                "stem": q["stem"],
                "options": q["options"],
                "answer": q["answer"],
                "explanation": q["explanation"],
                "knowledge": q["knowledge"],
                "source": {"relation": "verbatim", "sourceId": "past-exam-web-qicoder",
                            "locator": f"{arguments.paper_id} 第 {q['no']} 题"},
            }
            for q in questions
        ],
    }

    papers_dir = PAST_EXAMS / "papers"
    papers_dir.mkdir(exist_ok=True)
    out = papers_dir / f"{arguments.paper_id}.json"
    out.write_text(json.dumps(paper, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {out.relative_to(PROJECT_ROOT)}({len(paper['questions'])} 题)", flush=True)

    # 登记 papers.json(按年份倒序去重)
    reg_path = PAST_EXAMS / "papers.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    meta = {k: paper[k] for k in ("id", "title", "year", "session", "subject", "source_note")}
    reg["papers"] = [m for m in reg.get("papers", []) if m["id"] != meta["id"]]
    reg["papers"].append(meta)
    reg["papers"].sort(key=lambda m: (m["year"], m["session"]), reverse=True)
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已登记 {reg_path.relative_to(PROJECT_ROOT)}", flush=True)


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="导入嵌入式系统设计师历年真题(qicoder 电子书)")
    parser.add_argument("--list", action="store_true", help="列出可导入的卷子")
    parser.add_argument("--from-url", help="卷子页面路径(notes/xxx.html)或完整 URL")
    parser.add_argument("--paper-id", help="卷子 id,如 past-exam-2021a")
    parser.add_argument("--year", type=int)
    parser.add_argument("--session", default="上半年")
    parser.add_argument("--subject", default="综合知识")
    parser.add_argument("--title", help="卷子标题,默认按年份生成")
    arguments = parser.parse_args()

    if arguments.list:
        list_papers()
        return 0
    if arguments.from_url and arguments.paper_id and arguments.year:
        import_paper(arguments)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
