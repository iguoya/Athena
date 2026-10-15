#!/usr/bin/env python3
"""comms.py v2 自测：原子写、status 乐观锁、既有命令冒烟。不引测试框架。"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATHENA = ROOT.parent
spec = importlib.util.spec_from_file_location("athena_comms_v2", ROOT / "comms.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def cabin_at(home: Path) -> None:
    for name in ("tasks", "msgs", "read", "chat"):
        (home / name).mkdir(parents=True)
    (home / "config.json").write_text(
        json.dumps(
            {
                "leader": "zcode",
                "agents": ["zcode", "cursor"],
                "bands": {"zcode": 9, "cursor": 1},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (home / "tasks" / "T-001-demo.md").write_text(
        "---\n"
        "id: T-001\n"
        "title: demo\n"
        "owner: cursor\n"
        "status: todo\n"
        "priority: P1\n"
        "depends: \n"
        "created: 2026-10-16 00:00\n"
        "updated: 2026-10-16 00:00\n"
        "---\n\n## 进展记录\n",
        encoding="utf-8",
    )


def run(argv: list[str]) -> int:
    old = sys.argv
    sys.argv = ["comms.py", *argv]
    try:
        result = mod.main()
    finally:
        sys.argv = old
    return 0 if result is None else result


def task_file(home: Path, tid: str) -> Path:
    hits = list((home / "tasks").glob(f"{tid}-*.md"))
    if len(hits) != 1:
        raise SystemExit(f"{tid} 任务文件数量是 {len(hits)}")
    return hits[0]


def main() -> int:
    home = ATHENA / "comms" / "_v2test"
    shutil.rmtree(home, ignore_errors=True)
    try:
        mod.COMMS_ROOT = ATHENA / "comms"
        cabin_at(home)

        run(["send", "--from", "cursor", "--to", "zcode", "--subject", "你好", "--body", "正文完整", "--project", "_v2test"])
        msgs = list((home / "msgs").glob("*.md"))
        if len(msgs) != 1:
            raise SystemExit(f"发出的消息不是 1 条：{len(msgs)}")
        text = msgs[0].read_text(encoding="utf-8")
        if not text.startswith("---\n") or "正文完整" not in text or not text.endswith("\n"):
            raise SystemExit("原子写的消息不完整")
        if list(home.rglob("*.tmp")):
            raise SystemExit("临时文件没有替换掉")

        run(["ack", "zcode", "--all", "--project", "_v2test"])
        read = (home / "read" / "zcode.txt").read_text(encoding="utf-8")
        if msgs[0].name not in read.splitlines() or not read.endswith("\n"):
            raise SystemExit(f"已读记录不完整：{read!r}")

        run(["say", "--from", "cursor", "--to", "zcode", "一句完整", "--project", "_v2test"])
        log = (home / "chat" / "cursor.log").read_text(encoding="utf-8")
        if log.count("\n") != 1 or "一句完整" not in log:
            raise SystemExit(f"即时消息不是一整行：{log!r}")

        run(["status", "T-001", "doing", "--by", "cursor", "--project", "_v2test"])
        meta, _ = mod.parse(task_file(home, "T-001"))
        if meta.get("status") != "doing":
            raise SystemExit(f"status 没写成 doing：{meta.get('status')}")
        board = (home / "BOARD.md").read_text(encoding="utf-8")
        if not board.startswith("# ") or "doing" not in board:
            raise SystemExit("看板没有生成完整")

        run(["inbox", "cursor", "--project", "_v2test"])
        if run(["check", "--project", "_v2test"]) != 0:
            raise SystemExit("冒烟 check 没过")

        run(["task", "new", "--owner", "cursor", "--title", "锁测试", "--priority", "P1", "--project", "_v2test"])
        locked = task_file(home, "T-101")
        orig = mod.parse
        flipped = {"done": False}

        def wrapped(path: Path):
            meta, body = orig(path)
            if not flipped["done"] and path.name.startswith("T-101") and meta.get("status") == "todo":
                flipped["done"] = True
                path.write_text(
                    path.read_text(encoding="utf-8").replace("status: todo", "status: review", 1),
                    encoding="utf-8",
                )
            return meta, body

        mod.parse = wrapped
        try:
            try:
                run(["status", "T-101", "doing", "--by", "cursor", "--project", "_v2test"])
            except SystemExit as e:
                if "请重跑一次 status" not in str(e):
                    raise SystemExit(f"乐观锁的报错不对：{e}") from e
            else:
                raise SystemExit("乐观锁没有拦住并发的 status")
        finally:
            mod.parse = orig
        if orig(locked)[0].get("status") != "review":
            raise SystemExit("冲突时仍写入了任务文件")
    finally:
        shutil.rmtree(home, ignore_errors=True)

    print("test_v2: 原子写、乐观锁、inbox/send/ack/status/board/check 冒烟通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
