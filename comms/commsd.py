#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Athena 协作投递守护（commsd，ADR 0181）。

职责窄四件：监听消息落盘、维护自身心跳、写系统通知请求、按窄口径 spawn 唤醒。
不存消息、不改任何舱内文件——文件权威与写路径仍是 CLI + 各舱目录（ADR 0165/0166）。
宿主是 comms-console（拉起与保活）；没有宿主时也可手动 `python comms/commsd.py`。

- 新消息 to=operator，或标题含「转向使用者」→ 在 sessions/notify-queue/ 写请求文件，
  由宿主（comms-console）弹系统通知并投进 operator 收件箱；宿主消费后删除。
- 标题含「紧急」且收件方（具体代理，广播 all 不 spawn）所有会话心跳超时
  HEARTBEAT_TTL → 调 spawn.py 唤醒一个无头会话；每条消息至多 spawn 一次。
- 自身心跳在 sessions/.daemon.json；已有新鲜实例在跑则直接退出（单实例）。

用法：python comms/commsd.py [--interval 秒] [--once]
  --once 只扫一轮就退出（调试与自测用）。
"""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comms as cm  # noqa: E402 —— 复用解析与路径常量，协议逻辑只留一份

SESSIONS = cm.SESSIONS
DAEMON_FILE = cm.DAEMON_FILE
NOTIFY_QUEUE = cm.NOTIFY_QUEUE
SPAWNED_DIR = cm.SPAWNED_DIR
DAEMON_TTL = 60  # 秒；超过视为上一个实例已死
SPAWN_MAX_AGE = 30  # 分钟；消息创建超过这么久就不再 spawn（避免考古式唤醒陈旧紧急消息）


def _operator_wants(meta: dict[str, str]) -> bool:
    return meta.get("to") == "operator" or "转向使用者" in (meta.get("subject") or "")


def snapshot_msgs() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for p in cm.COMMS_ROOT.glob("*/msgs/*.md"):
        out[f"{p.parent.parent.name}/{p.name}"] = p
    return out


def active_sessions(agent: str) -> list[dict]:
    out = []
    if not SESSIONS.is_dir():
        return out
    for f in SESSIONS.glob(f"{agent}.*.json"):
        if f.name.startswith(".") or "delivered" in f.name:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if d.get("role") == "operator" or d.get("mute"):
            continue
        if cm.session_active(d):
            out.append(d)
    return out


def queue_notify(key: str, project: str, path: Path, meta: dict[str, str]) -> None:
    NOTIFY_QUEUE.mkdir(parents=True, exist_ok=True)
    target = NOTIFY_QUEUE / f"{key.replace('/', '__')}.json"
    if target.exists():
        return  # 幂等：同一条消息只排队一次，消费由宿主删文件
    payload = {"project": project, "file": path.name, "from": meta.get("from", ""),
               "subject": meta.get("subject", ""), "created": meta.get("created", ""),
               "queued": datetime.now().isoformat(timespec="seconds")}
    cm.atomic_write(target, json.dumps(payload, ensure_ascii=False, indent=1))


def maybe_spawn(project: str, key: str, meta: dict[str, str]) -> str | None:
    """窄口径（Q6）：标题带「紧急」+ 收件方是具体代理 + 它全部会话心跳超时 + 未 spawn 过。"""
    to = meta.get("to", "")
    if "紧急" not in (meta.get("subject") or "") or to in ("all", "operator", ""):
        return None
    try:
        created = datetime.strptime(meta.get("created", ""), "%Y-%m-%d %H:%M")
        if (datetime.now() - created).total_seconds() > SPAWN_MAX_AGE * 60:
            return None
    except ValueError:
        return None
    if active_sessions(to):
        return None
    SPAWNED_DIR.mkdir(parents=True, exist_ok=True)
    flag = SPAWNED_DIR / f"{key.replace('/', '__')}.flag"
    if flag.exists():
        return None
    cm.atomic_write(flag, datetime.now().isoformat(timespec="seconds"))
    cmd = [sys.executable, str(Path(__file__).resolve().parent / "spawn.py"), to, "--project", project,
           "--note", f"紧急消息投递：{meta.get('subject', '')}"]
    if meta.get("task"):
        cmd += ["--task", meta["task"]]
    try:
        done = subprocess.run(cmd, cwd=str(cm.ATHENA), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=120)
        return (done.stdout or "").strip()[-400:] or f"exit={done.returncode}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"spawn 失败：{exc}"


def sweep(baseline: dict[str, Path]) -> tuple[dict[str, Path], list[str]]:
    """扫一轮：返回新基线与动作日志。启动时的存量不当新消息（baseline 由调用方维护）。"""
    log: list[str] = []
    current = snapshot_msgs()
    fresh = [k for k in current if k not in baseline]
    for key in sorted(fresh):
        path = current[key]
        project = key.split("/", 1)[0]
        meta, _body = cm.parse(path)
        if _operator_wants(meta):
            queue_notify(key, project, path, meta)
            log.append(f"notify-queue += {key}")
        spawned = maybe_spawn(project, key, meta)
        if spawned is not None:
            log.append(f"spawn {meta.get('to')}: {spawned}")
    return current, log


def write_heartbeat() -> None:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    cm.atomic_write(DAEMON_FILE, json.dumps(
        {"pid": __import__("os").getpid(), "heartbeat": datetime.now().isoformat(timespec="seconds")},
        ensure_ascii=False))


def daemon_alive() -> bool:
    if not DAEMON_FILE.exists():
        return False
    try:
        d = json.loads(DAEMON_FILE.read_text(encoding="utf-8"))
        hb = datetime.fromisoformat(d["heartbeat"])
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return False
    if d.get("pid") == __import__("os").getpid():
        return False
    return (datetime.now() - hb).total_seconds() <= DAEMON_TTL


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--interval", type=int, default=2)
    ap.add_argument("--once", action="store_true", help="只扫一轮就退出（调试）")
    a = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not a.once and daemon_alive():
        print("commsd 已有活跃实例，退出")
        return 0

    def _bye(_sig, _frm):
        DAEMON_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, _bye)
    signal.signal(signal.SIGTERM, _bye)
    write_heartbeat()
    baseline = snapshot_msgs()
    print(f"commsd 已启动（pid 略），监听 {cm.COMMS_ROOT.name}/*/msgs，interval={a.interval}s")
    if a.once:
        _baseline, log = sweep(baseline)
        for line in log:
            print(line)
        DAEMON_FILE.unlink(missing_ok=True)
        return 0
    while True:
        time.sleep(a.interval)
        write_heartbeat()
        try:
            baseline, log = sweep(baseline)
        except Exception as exc:  # noqa: BLE001 —— 单轮失败不退出，下一轮重试
            print(f"轮次异常（继续）：{exc}")
            continue
        for line in log:
            print(line)


if __name__ == "__main__":
    raise SystemExit(main())
