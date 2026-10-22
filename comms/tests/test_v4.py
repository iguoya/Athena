#!/usr/bin/env python3
"""comms.py v4 自测：会话注册、deliver 订阅投递、operator、triage、delivered 并入已读。
不引测试框架；沿用 v2/v3 的临时舱模式。"""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATHENA = ROOT.parent
spec = importlib.util.spec_from_file_location("athena_comms_v4", ROOT / "comms.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

TMP = ATHENA / "comms" / "_v4test"
SID_A = "sess-aaaaaaaa"
SID_B = "sess-bbbbbbbb"


def cabin(name: str, agents: list[str]) -> None:
    home = TMP.parent / name if False else mod.COMMS_ROOT / name
    for sub in ("tasks", "msgs", "read", "chat"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    (home / "config.json").write_text(json.dumps(
        {"leader": "zcode", "agents": agents, "bands": {"zcode": 9, "cursor": 1}}, ensure_ascii=False), encoding="utf-8")


def msg(project: str, frm: str, to: str, subject: str, body: str = "正文", task: str | None = None) -> str:
    proj = mod.COMMS_ROOT / project
    name = f"{mod.stamp()}__{frm}__{to}__{mod.slug(subject)}.md"
    meta = {"from": frm, "to": to, "subject": subject, "created": mod.now()}
    if task:
        meta["task"] = task
    (proj / "msgs" / name).write_text(mod.dump(meta, "\n" + body + "\n"), encoding="utf-8")
    return name


def say(project: str, frm: str, to: str, text: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with (mod.COMMS_ROOT / project / "chat" / f"{frm}.log").open("a", encoding="utf-8") as fh:
        fh.write(f"{ts}|{to}|{text}\n")


def run(argv: list[str]) -> str:
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["comms.py", *argv]
    try:
        with redirect_stdout(buf):
            result = mod.main()
    finally:
        sys.argv = old
    assert result in (0, None), f"exit={result} for {argv}"
    return buf.getvalue()


def checks() -> None:
    # ── 注册与心跳 ──
    out = run(["session", "touch", "--agent", "zcode", "--sid", SID_A, "--projects", "v4a"])
    assert "role=worker" in out and "v4a" in out, out
    data = mod.session_read("zcode", SID_A)
    assert data and data["projects"] == ["v4a"], data
    assert mod.session_active(data), "刚注册的会话应活跃"
    out = run(["session", "list"])
    assert f"zcode.{SID_A[:8]}" in out, out
    # 心跳过期（绕过 session_save——它会无条件把心跳刷回现在）
    data["heartbeat"] = (datetime.now() - timedelta(minutes=20)).isoformat(timespec="seconds")
    mod.atomic_write(mod.session_path("zcode", SID_A), json.dumps(data, ensure_ascii=False))
    out = run(["session", "list"])
    assert SID_A[:8] not in out, "超时会话不应出现在默认列表"
    out = run(["session", "list", "--all"])
    assert SID_A[:8] in out, out

    # ── deliver：订阅过滤 + operator 静音 + 紧急优先 ──
    msg("v4a", "cursor", "zcode", "普通：给全舱")          # 公共箱（to=zcode）
    msg("v4b", "cursor", "zcode", "订阅外：不应投递")
    out = run(["deliver", "--agent", "zcode", "--sid", SID_A])
    assert "给全舱" in out and "v4a" in out, out
    assert "订阅外" not in out, "订阅外的舱不应注入"
    # 已投递不重复
    out = run(["deliver", "--agent", "zcode", "--sid", SID_A])
    assert "给全舱" not in out, "已投递的消息不应再次注入"
    # 手动 inbox 也不显示已投递的
    out = run(["--project", "v4a", "inbox", "zcode"])
    assert "给全舱" not in out, "手动 inbox 应并入会话已投递记录"
    # 紧急消息越过订阅
    msg("v4b", "cursor", "zcode", "紧急：越箱而来")
    out = run(["deliver", "--agent", "zcode", "--sid", SID_A])
    assert "越箱而来" in out, "紧急消息应无视订阅注入"

    # ── operator：收发与静音 ──
    msg("v4a", "cursor", "operator", "给使用者的裁决请求")
    out = run(["--project", "v4a", "inbox", "operator"])
    assert "给使用者的裁决请求" in out, out
    out = run(["--project", "v4a", "ack", "operator", "--all"])
    assert "已标记" in out, out
    run(["session", "touch", "--agent", "zcode", "--sid", SID_B, "--role", "operator"])
    msg("v4a", "cursor", "zcode", "operator 会话不该看到这个")
    out = run(["deliver", "--agent", "zcode", "--sid", SID_B])
    assert out.strip() == "", f"operator 会话应零注入，得到：{out}"

    # ── chat 会话游标 ──
    run(["session", "touch", "--agent", "zcode", "--sid", SID_A, "--projects", "v4a"])
    say("v4a", "cursor", "zcode", "快问快答")
    out = run(["deliver", "--agent", "zcode", "--sid", SID_A])
    assert "快问快答" in out, out
    out = run(["deliver", "--agent", "zcode", "--sid", SID_A])
    assert "快问快答" not in out, "chat 会话游标应推进"

    # ── triage：跨舱聚合 + shared delivered ──
    run(["session", "drop", "--agent", "zcode", "--sid", SID_A])
    msg("v4a", "cursor", "zcode", "triage 才能看到")
    out = run(["triage", "zcode"])
    assert "triage 才能看到" in out and "v4a" in out, out
    out = run(["triage", "zcode"])
    assert "0 条未处理消息" in out, "triage 看过的应写 shared delivered"

    print("test_v4: 会话注册/心跳、deliver 订阅与静音、紧急越箱、operator、chat 会话游标、triage 通过")


def main() -> int:
    shutil.rmtree(TMP.parent / "_v4test", ignore_errors=True)
    shutil.rmtree(mod.SESSIONS, ignore_errors=True) if str(mod.SESSIONS).endswith("_v4sessions") else None
    if TMP.exists():
        shutil.rmtree(TMP)
    cabin("v4a", ["zcode", "cursor"])
    cabin("v4b", ["zcode", "cursor"])
    mod.SESSIONS = mod.COMMS_ROOT / "_v4sessions"
    mod.SESSIONS.mkdir(parents=True, exist_ok=True)
    try:
        checks()
    finally:
        shutil.rmtree(mod.COMMS_ROOT / "v4a", ignore_errors=True)
        shutil.rmtree(mod.COMMS_ROOT / "v4b", ignore_errors=True)
        shutil.rmtree(mod.SESSIONS, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
