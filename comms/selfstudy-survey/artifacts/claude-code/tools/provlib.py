"""claude-code 采集脚本共用件：把官方文本里读出的计划、教材、开设结论写成 provinces/<id>.json，
并把课程、教材登记进自己的分片文件（content/courses/claude-code.json、content/textbooks/claude-code.json）。

每个省一个 build_<省id>.py，脚本里只放「抄自官方原文的数据」和来源常量，写入逻辑都在这里，
这样每省数据可复现、可 diff。写完跑 mentor/selfstudy-survey/scripts/check.py --data-only。
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[5]
CONTENT = ROOT / "mentor" / "selfstudy-survey" / "content"
DATE = "2026-10-24"  # 本轮抓取日期，verify.date 一律抄它（DESIGN §2）


def V(source: str, note: str | None = None, level: str = "official") -> dict:
    d = {"level": level, "source": source, "date": DATE}
    if note:
        d["note"] = note
    return d


def _load(p: pathlib.Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _save(p: pathlib.Path, d: dict) -> None:
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Shard:
    """课程库 / 教材库分片：新增条目时与已有同键条目比对，冲突就报错而不是静默覆盖。"""

    def __init__(self, kind: str):
        self.kind = kind
        self.path = CONTENT / kind / "claude-code.json"
        self.doc = _load(self.path)
        self.items: dict = self.doc[kind]
        # 其他成员分片里已有的键（只读，用来发现跨分片冲突）
        self.others: dict = {}
        for f in (CONTENT / kind).glob("*.json"):
            if f != self.path:
                self.others.update(_load(f).get(kind, {}))

    def add(self, key: str, value: dict) -> None:
        for pool in (self.items, self.others):
            if key in pool and pool[key] != value:
                if self.kind == "courses" and pool[key].get("name") == value["name"]:
                    # 同代码同名，仅 kind/别名/备注不同：保留已有（先到先得），别名取并集
                    value = {**pool[key], "aliases": sorted(set(pool[key].get("aliases", [])) | set(value.get("aliases", [])))}
                else:
                    raise SystemExit(f"{self.kind}[{key}] 与已有条目冲突：{pool[key]} vs {value}")
        self.items[key] = value

    def save(self) -> None:
        self.doc[self.kind] = dict(sorted(self.items.items()))
        _save(self.path, self.doc)


def course_row(code, name, credits, category, pair=None, practice=None, textbook=None, note="", elective_group=None):
    return {"code": code, "name": name, "credits": credits, "category": category, "elective_group": elective_group,
            "exam": None, "practice": practice, "textbook": textbook, "pair": pair, "note": note}


def none_offerings(scope: dict, listed: set[str], verify: dict) -> list[dict]:
    """scope 里没有被明确记录的专业，在拿到全省开考专业总表时统一写 none，依据挂总表。"""
    return [
        {"major": m["code"], "track": None, "status": "none", "hosts": [], "plans": [], "verify": verify}
        for m in scope["majors"]
        if m["code"] not in listed
    ]


def write_province(pid: str, patch: dict) -> None:
    p = CONTENT / "provinces" / f"{pid}.json"
    d = _load(p)
    d.update(patch)
    _save(p, d)


def load_scope() -> dict:
    return _load(CONTENT / "scope.json")


def save_evidence(province: str, name: str, text: str, url: str, note: str, sha256: str) -> None:
    """证据快照（文本）写进舱里 artifacts/claude-code/evidence/<省>/，文件头 url/fetched/sha256/note。"""
    d = ROOT / "comms" / "selfstudy-survey" / "artifacts" / "claude-code" / "evidence" / province
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(f"url: {url}\nfetched: {DATE}\nsha256: {sha256}\nnote: {note}\n\n{text}", encoding="utf-8")
