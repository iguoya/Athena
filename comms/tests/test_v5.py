#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""commsd 自测：通知队列幂等、spawn 窄口径、扫描基线、单实例心跳。不引测试框架。
spawn 的真实调用用 stub 替换——测试里绝不真的开无头会话。"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATHENA = ROOT.parent
sys.path.insert(0, str(ROOT))

import comms as cm  # noqa: E402

spec = importlib.util.spec_from_file_location("athena_commsd", ROOT / "commsd.py")
cd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(cd)

TMP_PROJECT = "_dtest"
SPAWN_CALLS: list[list[str]] = []


def cabin() -> None:
    home = cm.COMMS_ROOT / TMP_PROJECT
    for sub in ("tasks", "msgs", "read", "chat"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    (home / "config.json").write_text(json.dumps(
        {"leader": "zcode", "agents": ["zcode", "cursor"], "bands": {"zcode": 9}}, ensure_ascii=False), encoding="utf-8")


def msg(frm: str, to: str, subject: str, body: str = "正文") -> Path:
    proj = cm.COMMS_ROOT / TMP_PROJECT
    name = f"{cm.stamp()}__{frm}__{to}__{cm.slug(subject)}.md"
    p = proj / "msgs" / name
    p.write_text(cm.dump({"from": frm, "to": to, "subject": subject, "created": cm.now()},
                         "\n" + body + "\n"), encoding="utf-8")
    return p


def session(agent: str, sid: str, minutes_ago: int = 0) -> None:
    d = {"agent": agent, "sid": sid, "role": "worker", "projects": [], "mute": False,
         "heartbeat": (datetime.now() - timedelta(minutes=minutes_ago)).isoformat(timespec="seconds")}
    cm.atomic_write(cd.SESSIONS / f"{agent}.{sid}.json", json.dumps(d, ensure_ascii=False))


def main() -> int:
    shutil.rmtree(cm.COMMS_ROOT / TMP_PROJECT, ignore_errors=True)
    cd.SESSIONS = cm.SESSIONS = cm.COMMS_ROOT / "_dtest_sessions"
    cd.DAEMON_FILE = cm.DAEMON_FILE = cd.SESSIONS / ".daemon.json"
    cd.NOTIFY_QUEUE = cm.NOTIFY_QUEUE = cd.SESSIONS / "notify-queue"
    cd.SPAWNED_DIR = cm.SPAWNED_DIR = cd.SESSIONS / ".spawned"
    shutil.rmtree(cd.SESSIONS, ignore_errors=True)
    cd.SESSIONS.mkdir(parents=True, exist_ok=True)
    cabin()

    real_run = cd.subprocess.run
    cd.subprocess.run = lambda cmd, **kw: (SPAWN_CALLS.append(cmd), _fake_run())[-1]

    # ── 通知队列：operator 收件与「转向使用者」标题，幂等 ──
    baseline = cd.snapshot_msgs()
    p1 = msg("cursor", "operator", "请裁决：方向二选一")
    p2 = msg("cursor", "zcode", "T-002 卡住，转向使用者定底本")
    msg("cursor", "zcode", "普通进展：不需要人")           # 不排队
    baseline, log = cd.sweep(baseline)
    queued = sorted(f.name for f in cd.NOTIFY_QUEUE.glob("*.json"))
    assert len(queued) == 2, f"应排 2 条通知，实际 {queued}"
    baseline2, log2 = cd.sweep(baseline)
    assert not log2, "第二轮不应有新动作"
    assert len(list(cd.NOTIFY_QUEUE.glob("*.json"))) == 2, "重复扫描不得重复排队"

    # ── spawn 窄口径 ──
    def age(p: Path, minutes: int) -> None:
        m, b = cm.parse(p)
        m["created"] = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")
        cm.atomic_write(p, cm.dump(m, b))

    p_stale1 = msg("cursor", "zcode", "紧急：底本失效，速回")
    age(p_stale1, minutes=60)                              # 老紧急消息永不 spawn
    session("zcode", "alive1", minutes_ago=0)              # zcode 有活跃会话 → 不 spawn
    baseline, _ = cd.sweep(baseline)
    assert not SPAWN_CALLS, "收件方有活跃会话时不得 spawn"
    # 全部会话超时 → 只 spawn 新紧急消息；老的与已 spawn 过的都挡住
    session("zcode", "alive1", minutes_ago=30)             # 把 alive1 也改成过期：全会话超时
    msg("cursor", "zcode", "紧急：验收窗口要关了")           # 新消息 → spawn 一次
    baseline, _ = cd.sweep(baseline)
    assert len(SPAWN_CALLS) == 1, f"应只 spawn 新紧急消息一次，实际 {SPAWN_CALLS}"
    assert "--project" in SPAWN_CALLS[0] and TMP_PROJECT in SPAWN_CALLS[0], SPAWN_CALLS
    baseline3, _ = cd.sweep({})                            # 清空基线=当作全新消息 → 时效与幂等标记兜底
    assert len(SPAWN_CALLS) == 1, "老消息与已 spawn 过的消息都不得再 spawn"
    # 广播与 operator 不 spawn
    msg("cursor", "all", "紧急：请大家注意节假 deadline")
    msg("cursor", "operator", "紧急：给使用者的")
    cd.sweep(baseline3)
    assert len(SPAWN_CALLS) == 1, "广播与 operator 的紧急消息不 spawn"

    # ── 单实例心跳 ──
    cd.write_heartbeat()
    d = json.loads(cd.DAEMON_FILE.read_text(encoding="utf-8"))
    d["pid"] = 999999                                      # 测试进程自己写的 pid 会被 pid 守卫判假，改成外部 pid
    cm.atomic_write(cd.DAEMON_FILE, json.dumps(d, ensure_ascii=False))
    assert cd.daemon_alive(), "新鲜心跳应判定存活"
    d["heartbeat"] = (datetime.now() - timedelta(seconds=120)).isoformat(timespec="seconds")
    cm.atomic_write(cd.DAEMON_FILE, json.dumps(d, ensure_ascii=False))
    assert not cd.daemon_alive(), "过期心跳应判定死亡"

    cd.subprocess.run = real_run
    print("test_v5: 通知队列幂等、spawn 窄口径（活跃会话/广播/operator 排除、至多一次）、单实例心跳 通过")
    return 0


def _fake_run():
    class R:
        returncode = 0
        stdout = "（stub）已打印提示词"
    return R()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        shutil.rmtree(cm.COMMS_ROOT / TMP_PROJECT, ignore_errors=True)
        shutil.rmtree(cm.COMMS_ROOT / "_dtest_sessions", ignore_errors=True)
