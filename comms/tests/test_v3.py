#!/usr/bin/env python3
"""comms.py v3 自测：分箱、已读互不覆盖、--mine、认领冲突、--as、旧已读文件。不引测试框架。"""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATHENA = ROOT.parent
spec = importlib.util.spec_from_file_location("athena_comms_v3", ROOT / "comms.py")
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
    for tid, title in (("T-001", "甲"), ("T-002", "乙")):
        (home / "tasks" / f"{tid}-{title}.md").write_text(
            "---\n"
            f"id: {tid}\n"
            f"title: {title}\n"
            "owner: cursor\n"
            "status: todo\n"
            "priority: P1\n"
            "depends: \n"
            "created: 2026-10-16 00:00\n"
            "updated: 2026-10-16 00:00\n"
            "---\n\n## 进展记录\n",
            encoding="utf-8",
        )


def run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["comms.py", *argv]
    try:
        with redirect_stdout(buf):
            try:
                result = mod.main()
            except SystemExit as e:
                if isinstance(e.code, str):
                    return 1, buf.getvalue() + e.code
                return (0 if e.code is None else e.code), buf.getvalue()
    finally:
        sys.argv = old
    return (0 if result is None else result), buf.getvalue()


def send(home: Path, subject: str, task: str | None = None) -> str:
    time.sleep(1.05)
    argv = ["send", "--from", "zcode", "--to", "cursor", "--subject", subject, "--body", subject, "--project", "_v3test"]
    if task:
        argv.extend(["--task", task])
    code, out = run(argv)
    if code != 0:
        raise SystemExit(f"发送失败 {subject}: {out}")
    hits = [p for p in (home / "msgs").glob("*.md") if subject in p.read_text(encoding="utf-8")]
    if len(hits) != 1:
        raise SystemExit(f"{subject} 对应的文件不是 1 个：{len(hits)}")
    return hits[0].name


def main() -> int:
    home = ATHENA / "comms" / "_v3test"
    shutil.rmtree(home, ignore_errors=True)
    try:
        mod.COMMS_ROOT = ATHENA / "comms"
        cabin_at(home)
        proj = ["--project", "_v3test"]

        old = send(home, "旧广播")
        legacy = home / "read" / "cursor.txt"
        legacy.write_text(old + "\n", encoding="utf-8")
        legacy_bytes = legacy.read_bytes()

        code, out = run(["inbox", "cursor", *proj])
        if code != 0 or "旧广播" in out:
            raise SystemExit(f"旧已读文件没有并入，收件箱仍看到旧广播：{out}")

        one = send(home, "任务一", "T-001")
        two = send(home, "任务二", "T-002")
        pub = send(home, "公共一")

        code, out = run(["inbox", "cursor", *proj])
        if not all(s in out for s in ("任务一", "任务二", "公共一")) or "旧广播" in out:
            raise SystemExit(f"不带新参数的收件箱不对：{out}")

        code, out = run(["ack", "cursor", "--all", "--task", "T-001", *proj])
        if code != 0 or "已标记 1 条为已读" not in out:
            raise SystemExit(f"按任务 ack 失败：{out}")
        if (home / "read" / "cursor.T-001.txt").read_text(encoding="utf-8").strip() != one:
            raise SystemExit("T-001 的已读没有只进自己的箱")
        if (home / "read" / "cursor.T-002.txt").exists():
            raise SystemExit("ack T-001 时写进了 T-002 的箱")
        if legacy.read_bytes() != legacy_bytes:
            raise SystemExit("旧的 cursor.txt 被改动了")

        code, out = run(["inbox", "cursor", *proj])
        if "任务一" in out or "任务二" not in out or "公共一" not in out:
            raise SystemExit(f"ack 一个箱后，别的箱不该消失：{out}")
        code, out = run(["inbox", "cursor", "--task", "T-001", *proj])
        if "任务一" not in out or "含历史" not in out or "任务二" in out:
            raise SystemExit(f"--task 应含本箱历史且不含别的箱：{out}")

        code, out = run(["ack", "cursor", "--all", *proj])
        if code != 0:
            raise SystemExit(out)
        if two not in (home / "read" / "cursor.T-002.txt").read_text(encoding="utf-8"):
            raise SystemExit("不带 --task 的 ack 没有把任务二写进它自己的箱")
        if pub not in (home / "read" / "cursor.all.txt").read_text(encoding="utf-8"):
            raise SystemExit("公共消息没有进 .all 箱")
        code, out = run(["inbox", "cursor", *proj])
        if "未读 0 条" not in out:
            raise SystemExit(f"全部 ack 之后默认收件箱应为空：{out}")

        code, out = run(["status", "T-001", "doing", "--by", "cursor", "--as", "tab2", *proj])
        if code != 0:
            raise SystemExit(out)
        task = (home / "tasks" / "T-001-甲.md").read_text(encoding="utf-8")
        if "cursor(tab2)：todo → doing" not in task:
            raise SystemExit(f"--as 没有写进流转行：{task}")
        code, out = run(["status", "T-001", "doing", "--by", "zcode", *proj])
        if code == 0 or "该任务正在被认领（by cursor）" not in out:
            raise SystemExit(f"认领冲突没有拦住：{code} {out}")
        if "zcode：doing → doing" in (home / "tasks" / "T-001-甲.md").read_text(encoding="utf-8"):
            raise SystemExit("冲突的认领仍然写进了任务文件")

        send(home, "认领内", "T-001")
        send(home, "别的任务", "T-002")
        send(home, "公共二")
        send(home, "紧急停", "T-002")

        code, out = run(["inbox", "cursor", "--mine", *proj])
        if "认领内" not in out or "公共二" not in out or "别的任务" in out or "紧急停" in out:
            raise SystemExit(f"--mine 应只有公共箱和认领中的 T-001：{out}")
        code, out = run(["notify", "cursor", "--mine", *proj])
        if "认领内" not in out or "公共二" not in out or "紧急停" not in out or "别的任务" in out:
            raise SystemExit(f"notify --mine 应放行认领任务、公共箱和紧急，其余静默：{out}")

        code, out = run(["check", *proj])
        if code != 0:
            raise SystemExit(out)
        print("test_v3: 分箱、已读隔离、--mine、认领冲突、--as、旧已读并入 通过")
        return 0
    finally:
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
