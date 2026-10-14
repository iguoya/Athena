#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""九州三方协作通讯工具（Claude Code / Cursor / ZCode）。

设计原则：任何一方永远不修改别人写的文件，所以不会互相覆盖。
  - 任务：docs/comms/tasks/T-xxx-*.md，每个任务一个文件，只有负责人和 Claude Code 能改状态。
  - 消息：docs/comms/msgs/*.md，只新增、不修改；已读状态记在 docs/comms/read/<name>.txt（各写各的）。
  - 看板：docs/comms/BOARD.md 由本工具生成，不要手改。

常用命令（NAME 为 claude-code / cursor / zcode 之一）：
  python scripts/comms.py inbox NAME                      # 每轮开工先跑：未读消息 + 我的待办
  python scripts/comms.py send --from NAME --to NAME2 --subject 主题 --body 正文 [--task T-001]
  python scripts/comms.py ack NAME [--all | 文件名...]    # 标记已读
  python scripts/comms.py status T-001 doing --by NAME --note 说明
  python scripts/comms.py board                           # 重新生成 BOARD.md
  python scripts/comms.py task new --owner cursor --title 标题 --priority P0 --body-file x.md   # 仅 Claude Code
  python scripts/comms.py check                           # 校验任务与消息结构
  python scripts/comms.py presence [NAME]                 # 判断对方是否在线（online / quiet / unreachable）
  python scripts/comms.py reply FILE --from NAME --body 正文   # 回复一条消息（自动串成一个线程）
  python scripts/comms.py thread FILE|ID                  # 按时间顺序看一个线程
  python scripts/comms.py say --from NAME --to NAME2|all 一句话   # 即时消息（短、不进任务系统）
  python scripts/comms.py chat NAME [--tail N]            # 看发给我的即时消息（未读，并标记已读）
  python scripts/comms.py notify NAME                     # 给 hook 用：有未读时只打印 1~3 行摘要，没有则静默
  python scripts/comms.py watch NAME [--timeout 3300]      # 阻塞等待新消息，来了就打印并退出（后台运行即可被唤醒）
  python scripts/comms.py ping NAME|all                   # 发一条「联络」消息，之后用 presence 看有没有回应
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMS = ROOT / "docs" / "comms"
TASKS = COMMS / "tasks"
MSGS = COMMS / "msgs"
READ = COMMS / "read"
CHAT = COMMS / "chat"

AGENTS = ("claude-code", "cursor", "zcode")
STATUSES = ("todo", "doing", "review", "blocked", "done")
PRIORITIES = ("P0", "P1", "P2")
OPEN = ("todo", "doing", "blocked", "review")


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def slug(text: str) -> str:
    s = re.sub(r"[\\/:*?\"<>|\s]+", "-", text.strip())
    return s[:24].strip("-") or "msg"


def parse(path: Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return {}, raw
    meta: dict[str, str] = {}
    for line in raw[4:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split("#")[0].strip() if k.strip() == "status" else v.strip()
    return meta, raw[end + 5 :]


def dump(meta: dict[str, str], body: str) -> str:
    head = "\n".join(f"{k}: {v}" for k, v in meta.items())
    return f"---\n{head}\n---\n{body}"


def tasks() -> list[tuple[Path, dict[str, str], str]]:
    out = []
    for p in sorted(TASKS.glob("T-*.md")):
        m, b = parse(p)
        out.append((p, m, b))
    return out


def find_task(tid: str):
    for p, m, b in tasks():
        if m.get("id") == tid:
            return p, m, b
    raise SystemExit(f"找不到任务 {tid}")


def read_set(name: str) -> set[str]:
    f = READ / f"{name}.txt"
    if not f.exists():
        return set()
    return {l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()}


def messages_for(name: str, unread_only: bool = True):
    seen = read_set(name)
    out = []
    for p in sorted(MSGS.glob("*.md")):
        m, b = parse(p)
        if m.get("to") not in (name, "all"):
            continue
        if m.get("from") == name:
            continue
        if unread_only and p.name in seen:
            continue
        out.append((p, m, b))
    return out


def check_agent(name: str) -> None:
    if name not in AGENTS:
        raise SystemExit(f"名字须为 {AGENTS} 之一，收到 {name!r}")


# ------------------------------------------------------------------ 命令
def cmd_inbox(a):
    check_agent(a.name)
    msgs = messages_for(a.name, unread_only=not a.all)
    print(f"=== {a.name} 的收件箱（{'全部' if a.all else '未读'} {len(msgs)} 条）===")
    for p, m, b in msgs:
        print(f"\n--- {p.name}\n来自 {m.get('from')} · {m.get('created')} · 主题：{m.get('subject')}"
              + (f" · 任务 {m['task']}" if m.get("task") else ""))
        print(b.strip())
    mine = [(p, m, b) for p, m, b in tasks() if m.get("owner") == a.name and m.get("status") in OPEN]
    order = {"P0": 0, "P1": 1, "P2": 2}
    st = {"doing": 0, "blocked": 1, "todo": 2, "review": 3}
    mine.sort(key=lambda t: (order.get(t[1].get("priority"), 9), st.get(t[1].get("status"), 9), t[1].get("id")))
    print(f"\n=== 我的待办（{len(mine)} 项，按优先级）===")
    done_ids = {m.get("id") for _, m, _ in tasks() if m.get("status") == "done"}
    for p, m, b in mine:
        deps = [d for d in m.get("depends", "").replace("[", "").replace("]", "").split(",") if d.strip()]
        waiting = [d.strip() for d in deps if d.strip() not in done_ids]
        flag = f"（等待 {','.join(waiting)}）" if waiting else ""
        print(f"[{m.get('priority')}] {m.get('id')} · {m.get('status'):7} · {m.get('title')}{flag}\n      文件：{p.relative_to(ROOT).as_posix()}")
    if msgs:
        print("\n读完后请运行：python scripts/comms.py ack", a.name, "--all")


def cmd_send(a):
    check_agent(getattr(a, "from"))
    if a.to != "all":
        check_agent(a.to)
    body = a.body
    if a.body_file:
        body = Path(a.body_file).read_text(encoding="utf-8")
    if body == "-":
        body = sys.stdin.read()
    if not body:
        raise SystemExit("缺少 --body 或 --body-file")
    MSGS.mkdir(parents=True, exist_ok=True)
    name = f"{stamp()}__{getattr(a, 'from')}__{a.to}__{slug(a.subject)}.md"
    meta = {"from": getattr(a, "from"), "to": a.to, "subject": a.subject, "created": now()}
    if getattr(a, "thread", None):
        meta["thread"] = a.thread
    if a.task:
        find_task(a.task)
        meta["task"] = a.task
    (MSGS / name).write_text(dump(meta, "\n" + body.strip() + "\n"), encoding="utf-8")
    print("已发送：", name)


def msg_id(p: Path) -> str:
    """消息 id = 文件名里的时间戳；线程 id = 线程根消息的 id。"""
    return p.name[:15]


def find_msg(key: str) -> Path:
    hits = [p for p in sorted(MSGS.glob("*.md")) if key in p.name]
    if not hits:
        raise SystemExit(f"找不到消息：{key}")
    return hits[-1] if len(hits) > 1 and key.count("__") == 0 and not key[:1].isdigit() else hits[0]


def cmd_reply(a):
    """回复一条消息：收件人自动取原发件人，标题加「Re: 」，线程 id 沿用或以原消息为根。"""
    orig = find_msg(a.file)
    om, _ = parse(orig)
    me = getattr(a, "from")
    check_agent(me)
    to = om.get("from") if om.get("from") != me else om.get("to")
    subj = om.get("subject", "")
    ns = argparse.Namespace(**{"from": me, "to": to, "subject": subj if subj.startswith("Re: ") else "Re: " + subj,
                               "body": a.body, "body_file": a.body_file, "task": om.get("task"),
                               "thread": om.get("thread") or msg_id(orig)})
    cmd_send(ns)


def cmd_thread(a):
    key = a.key
    root = None
    for p in sorted(MSGS.glob("*.md")):
        if key in p.name:
            m, _ = parse(p)
            root = m.get("thread") or msg_id(p)
            break
    if root is None:
        raise SystemExit(f"找不到线程：{key}")
    chain = []
    for p in sorted(MSGS.glob("*.md")):
        m, b = parse(p)
        if (m.get("thread") or msg_id(p)) == root:
            chain.append((p, m, b))
    print(f"=== 线程 {root}（{len(chain)} 条）===")
    for p, m, b in chain:
        print()
        print(f"--- {m.get('created')} {m.get('from')} → {m.get('to')} · {m.get('subject')}")
        print(b.strip())


def cmd_notify(a):
    """给 hook 用的轻量提示：没有未读就什么都不打印（不打扰），有则最多 3 行摘要。"""
    check_agent(a.name)
    msgs = messages_for(a.name)
    chats = chat_unread(a.name)
    if not msgs and not chats:
        return 0
    if chats:
        print(f"[九州即时消息] {len(chats)} 条未读（运行 python mentor/jiuzhou/scripts/comms.py chat {a.name} 查看并标记已读）：")
        for ts, frm, _to, text in chats[-3:]:
            print(f"  - [{ts[11:16]}] {frm}: {text[:80]}")
    if msgs:
        print(f"[九州通讯] {a.name} 有 {len(msgs)} 条未读消息，运行 python mentor/jiuzhou/scripts/comms.py inbox {a.name} 查看：")
        for p, m, _ in msgs[-3:]:
            print(f"  - {m.get('from')} · {m.get('subject')}")
    return 0


def cmd_watch(a):
    """阻塞等待 NAME 的新未读消息；来了就打印并退出 0，超时退出 3。在后台运行，来消息时进程结束即可被唤醒。"""
    check_agent(a.name)
    known = {p.name for p, _, _ in messages_for(a.name)}
    known_chat = {t[:3] for t in chat_unread(a.name)}
    deadline = time.time() + a.timeout
    while time.time() < deadline:
        fresh_chat = [t for t in chat_unread(a.name) if t[:3] not in known_chat]
        if fresh_chat:
            for ts, frm, _to, text in fresh_chat:
                print(f"[{ts[5:16]}] {frm} → {a.name}: {text}")
            return 0
        fresh = [(p, m, b) for p, m, b in messages_for(a.name) if p.name not in known]
        if fresh:
            for p, m, b in fresh:
                print(f"--- {p.name}")
                print(f"来自 {m.get('from')} · {m.get('created')} · 主题：{m.get('subject')}")
                print(b.strip())
            return 0
        time.sleep(a.interval)
    print(f"{a.name}：{a.timeout} 秒内没有新消息")
    return 3


# ------------------------------------------------------------------ 即时消息（chat）
# 与任务/消息机制并存：任务与正式消息照旧；chat 是「一句话」级别的即时通讯。
# 每个人只写自己的 chat/<名字>.log（只追加），读的时候合并按时间排序——和消息机制一样，永远不改别人的文件。
# 每行：时间|收件人|正文（正文里的换行压成「 / 」）。已读位置记在 read/<名字>.chat（一个时间戳）。
def _chat_path(name: str) -> Path:
    return CHAT / f"{name}.log"


def chat_lines():
    out = []
    for n in AGENTS:
        f = _chat_path(n)
        if not f.exists():
            continue
        for raw in f.read_text(encoding="utf-8").splitlines():
            parts = raw.split("|", 2)
            if len(parts) == 3:
                out.append((parts[0], n, parts[1], parts[2]))
    return sorted(out)


def chat_pointer(name: str) -> str:
    f = READ / f"{name}.chat"
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""


def chat_unread(name: str):
    ptr = chat_pointer(name)
    return [t for t in chat_lines() if t[1] != name and t[2] in (name, "all") and t[0] > ptr]


def mark_chat_read(name: str) -> None:
    lines = chat_lines()
    if lines:
        READ.mkdir(parents=True, exist_ok=True)
        (READ / f"{name}.chat").write_text(lines[-1][0], encoding="utf-8")


def cmd_say(a):
    me = getattr(a, "from")
    check_agent(me)
    if a.to != "all":
        check_agent(a.to)
    text = " / ".join(x.strip() for x in a.text.splitlines() if x.strip())
    if not text:
        raise SystemExit("内容为空")
    CHAT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _chat_path(me).open("a", encoding="utf-8", newline="") as f:
        f.write(f"{ts}|{a.to}|{text}" + chr(10))
    print(f"[{ts}] {me} → {a.to}: {text}")


def cmd_chat(a):
    check_agent(a.name)
    if a.tail:
        lines = [t for t in chat_lines() if t[1] == a.name or t[2] in (a.name, "all")][-a.tail:]
        print(f"=== 最近 {len(lines)} 条即时消息（与 {a.name} 有关）===")
    else:
        lines = chat_unread(a.name)
        print(f"=== {a.name} 的即时消息（未读 {len(lines)} 条）===")
    for ts, frm, to, text in lines:
        print(f"[{ts[5:16]}] {frm} → {to}: {text}")
    if not a.tail:
        mark_chat_read(a.name)


def cmd_ack(a):
    check_agent(a.name)
    READ.mkdir(parents=True, exist_ok=True)
    unread = [p.name for p, _, _ in messages_for(a.name)]
    names = unread if a.all else a.files
    f = READ / f"{a.name}.txt"
    seen = read_set(a.name)
    add = [n for n in names if n not in seen]
    if add:
        with f.open("a", encoding="utf-8", newline="\n") as fh:
            for n in add:
                fh.write(n + "\n")
    print(f"已标记 {len(add)} 条为已读")


def cmd_status(a):
    check_agent(a.by)
    if a.status not in STATUSES:
        raise SystemExit(f"状态须为 {STATUSES}")
    p, m, b = find_task(a.task)
    if a.by not in (m.get("owner"), "claude-code"):
        raise SystemExit(f"只有负责人（{m.get('owner')}）或 claude-code 能改 {a.task}")
    if a.status == "done" and a.by != "claude-code":
        raise SystemExit("done 只能由 claude-code 验收后标记；你请改成 review 并附验证证据")
    if a.by != m.get("owner"):
        # 指挥者代改别人的任务要谨慎：只能验收（review→done）或明确打回返工，不能悄悄回退负责人刚交的状态
        if a.status == "done" and m.get("status") != "review":
            raise SystemExit(f"{a.task} 当前是 {m.get('status')}，只有 review 状态才能验收为 done")
        if a.status in ("doing", "todo") and m.get("status") in ("review", "done"):
            if not (a.note or "").startswith("返工"):
                raise SystemExit("把别人已交的 review/done 打回，--note 必须以“返工：”开头并写明原因")
    if a.status in ("review", "blocked") and not a.note:
        raise SystemExit(f"改成 {a.status} 必须写 --note（review 附验证命令输出摘要；blocked 写卡在哪、要谁帮忙）")
    old = m.get("status")
    m["status"] = a.status
    m["updated"] = now()
    line = f"- [{now()}] {a.by}：{old} → {a.status}" + (f" · {a.note}" if a.note else "")
    b = b.rstrip() + "\n" + line + "\n"
    p.write_text(dump(m, b), encoding="utf-8")
    print(f"{a.task}: {old} → {a.status}")
    cmd_board(None)


def next_task_id(prefix_hundreds: int) -> str:
    ids = [int(m["id"][2:]) for _, m, _ in tasks() if m.get("id", "").startswith("T-")]
    base = [i for i in ids if i // 100 == prefix_hundreds]
    return f"T-{(max(base) + 1) if base else prefix_hundreds * 100 + 1:03d}"


def cmd_task_new(a):
    check_agent(a.owner)
    if a.priority not in PRIORITIES:
        raise SystemExit(f"priority 须为 {PRIORITIES}")
    hundreds = {"cursor": 0, "zcode": 1, "claude-code": 9}[a.owner]
    tid = next_task_id(hundreds)
    body = Path(a.body_file).read_text(encoding="utf-8") if a.body_file else "\n## 目标\n\n## 做法\n\n## 验收\n"
    meta = {"id": tid, "title": a.title, "owner": a.owner, "status": "todo", "priority": a.priority,
            "depends": a.depends or "", "created": now(), "updated": now()}
    TASKS.mkdir(parents=True, exist_ok=True)
    path = TASKS / f"{tid}-{slug(a.title)}.md"
    path.write_text(dump(meta, body.rstrip() + "\n\n## 进展记录\n"), encoding="utf-8")
    print("已创建：", path.relative_to(ROOT).as_posix())
    cmd_board(None)


def cmd_board(_a):
    ts = tasks()
    lines = ["# 九州协作看板", "",
             f"> 由 `scripts/comms.py board` 生成于 {now()}，**不要手改**。任务详情见各任务文件，通讯规则见 [README.md](README.md)。", ""]
    unread = {n: len(messages_for(n)) for n in AGENTS}
    lines += ["## 未读消息", "", "| 角色 | 未读 |", "|---|---|"] + [f"| {n} | {unread[n]} |" for n in AGENTS] + [""]
    pres = [presence_of(n) for n in AGENTS if n != "claude-code"]
    lines += ["## 在线状态", "", "| 对方 | 状态 | 最近痕迹 | 距今 |", "|---|---|---|---|"] + [
        f"| {r['name']} | {r['state']} | {r['kind']} | {_fmt_age(r['age'])} |" for r in pres] + [""]
    cnt = {s: sum(1 for _, m, _ in ts if m.get("status") == s) for s in STATUSES}
    lines += ["## 概览", "", " · ".join(f"{s} {cnt[s]}" for s in STATUSES), ""]
    for agent in AGENTS:
        mine = [(p, m) for p, m, _ in ts if m.get("owner") == agent]
        if not mine:
            continue
        lines += [f"## {agent}", "", "| 任务 | 优先级 | 状态 | 标题 | 依赖 | 更新 |", "|---|---|---|---|---|---|"]
        order = {"P0": 0, "P1": 1, "P2": 2}
        st = {"doing": 0, "blocked": 1, "review": 2, "todo": 3, "done": 4}
        mine.sort(key=lambda t: (st.get(t[1].get("status"), 9), order.get(t[1].get("priority"), 9), t[1].get("id")))
        for p, m in mine:
            link = f"[{m.get('id')}](tasks/{p.name})"
            lines.append(f"| {link} | {m.get('priority')} | {m.get('status')} | {m.get('title')} | {m.get('depends','')} | {m.get('updated','')} |")
        lines.append("")
    (COMMS / "BOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if _a is not None:
        print("已生成", (COMMS / "BOARD.md").relative_to(ROOT).as_posix())


# ------------------------------------------------------------------ 在线判定
# 「在线」不能靠自报，只能靠可观察的痕迹：发过消息、读过消息（ack）、更新过任务进展、提交过自己名下的路径。
# 取这些痕迹里最新的一个作为 last_seen。再配合「联络（ping）」：claude-code 发一条标题以「联络」开头的消息，
# 对方若在 PING_GRACE 内没有任何新痕迹，就算没有回应。
ONLINE_WITHIN = timedelta(minutes=30)     # 这段时间内有痕迹 = online
QUIET_UNTIL = timedelta(hours=4)          # 超过这个时间一直没痕迹 = unreachable（即使没人 ping 过）
PING_GRACE = timedelta(minutes=15)        # ping 之后这么久还没痕迹 = 联系不上

# 各方名下的路径：有提交说明它在干活（消息之外的第二类证据）
OWNED = {
    "cursor": ["mentor/jiuzhou/src", "mentor/jiuzhou/src-tauri", "packages/maps", "mentor/jiuzhou/scripts/check.py"],
    "zcode": ["mentor/jiuzhou/content", "mentor/jiuzhou/scripts/check_layers.py", "mentor/jiuzhou/scripts/add_content.py"],
}
MSG_TS = re.compile(r"^(\d{8}-\d{6})__([^_]+(?:-[^_]+)*)__([^_]+(?:-[^_]+)*)__")
NOTE_TS = re.compile(r"^- \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] ([\w-]+)[：:]", re.M)


def _git_last_commit(paths: list[str]):
    try:
        repo = ROOT.parent.parent
        out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", *paths], cwd=repo,
                             capture_output=True, text=True, timeout=20).stdout.strip()
        return datetime.fromtimestamp(int(out)) if out else None
    except Exception:  # noqa: BLE001 —— git 不可用时只是少一类证据
        return None


def signs(name: str) -> list[tuple[datetime, str]]:
    """name 留下的所有痕迹（时间, 类型）。"""
    out: list[tuple[datetime, str]] = []
    for p in MSGS.glob("*.md"):
        m = MSG_TS.match(p.name)
        if m and m.group(2) == name:
            out.append((datetime.strptime(m.group(1), "%Y%m%d-%H%M%S"), "发消息"))
    for ts, frm, _to, _t in chat_lines():
        if frm == name:
            out.append((datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"), "即时消息"))
    rf = READ / f"{name}.txt"
    if rf.exists():
        out.append((datetime.fromtimestamp(rf.stat().st_mtime), "读消息"))
    for p in TASKS.glob("*.md"):
        for ts, who in NOTE_TS.findall(p.read_text(encoding="utf-8")):
            if who == name:
                out.append((datetime.strptime(ts, "%Y-%m-%d %H:%M"), "更新任务"))
    if name in OWNED:
        c = _git_last_commit(OWNED[name])
        if c:
            out.append((c, "提交代码/内容"))
    return out


def last_ping(name: str):
    """claude-code 发给 name（或 all）的最近一次「联络」消息的时间。"""
    best = None
    for p in MSGS.glob("*.md"):
        m = MSG_TS.match(p.name)
        if not m or m.group(2) != "claude-code" or m.group(3) not in (name, "all"):
            continue
        meta, _ = parse(p)
        if meta.get("subject", "").startswith("联络"):
            t = datetime.strptime(m.group(1), "%Y%m%d-%H%M%S")
            best = t if best is None or t > best else best
    return best


def presence_of(name: str) -> dict:
    now_ = datetime.now()
    ss = sorted(signs(name))
    seen, kind = (ss[-1] if ss else (None, "无"))
    age = now_ - seen if seen else None
    ping = last_ping(name)
    unanswered = bool(ping and now_ - ping > PING_GRACE and (seen is None or seen < ping))
    if age is not None and age <= ONLINE_WITHIN:
        state = "online"
    elif unanswered or age is None or age > QUIET_UNTIL:
        state = "unreachable"
    else:
        state = "quiet"
    return {"name": name, "state": state, "seen": seen, "kind": kind, "age": age, "ping": ping, "unanswered": unanswered}


ADVICE = {
    "online": "可以验收、指派任务、发消息。",
    "quiet": "有一阵没动静但没有证据说明断线：保留任务队列，只做被动检查（读收件箱），不催办。",
    "unreachable": "联系不上：停止监督——不验收、不指派新任务、不催办、不为它改状态；只在它重新出现（presence 变回 online）后再恢复。",
}


def _fmt_age(a) -> str:
    if a is None:
        return "从未"
    mins = int(a.total_seconds() // 60)
    return f"{mins} 分钟前" if mins < 120 else f"{mins // 60} 小时前"


def cmd_presence(a):
    names = [a.name] if a.name else [n for n in AGENTS if n != "claude-code"]
    for n in names:
        check_agent(n)
    rows = [presence_of(n) for n in names]
    if a.name:
        print(rows[0]["state"])
        return 0
    print("| 对方 | 状态 | 最近痕迹 | 距今 | 最近联络 | 建议 |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        if not r["ping"]:
            ping = "无"
        else:
            replied = r["seen"] is not None and r["seen"] >= r["ping"]
            tag = "已回应" if replied else ("未回应" if r["unanswered"] else "等待回应")
            ping = f"{r['ping'].strftime('%H:%M')}（{tag}）"
        print(f"| {r['name']} | {r['state']} | {r['kind']} | {_fmt_age(r['age'])} | {ping} | {ADVICE[r['state']]} |")
    return 0


def cmd_ping(a):
    targets = [n for n in AGENTS if n != "claude-code"] if a.name == "all" else [a.name]
    if a.name != "all":
        check_agent(a.name)
    body = ("claude-code 在线确认。读到这条请回一行：在线 / 手上做什么 / 有没有卡住。"
            " 不回应也没关系，只是我会据此判断你是否在线；联系不上时我不会再验收或催办你的任务，等你回来再恢复。")
    ns = argparse.Namespace(**{"from": "claude-code", "to": a.name, "subject": "联络：请回一行在线状态",
                               "body": body, "body_file": None, "task": None})
    cmd_send(ns)
    return 0


def cmd_check(_a):
    problems = []
    ids = set()
    for p, m, _ in tasks():
        tid = m.get("id")
        if not tid or tid in ids:
            problems.append(f"{p.name}: id 缺失或重复")
        ids.add(tid)
        if m.get("owner") not in AGENTS:
            problems.append(f"{p.name}: owner 非法 {m.get('owner')!r}")
        if m.get("status") not in STATUSES:
            problems.append(f"{p.name}: status 非法 {m.get('status')!r}")
        if m.get("priority") not in PRIORITIES:
            problems.append(f"{p.name}: priority 非法")
    for p, m, _ in tasks():
        for d in [x.strip() for x in m.get("depends", "").replace("[", "").replace("]", "").split(",") if x.strip()]:
            if d not in ids:
                problems.append(f"{p.name}: depends 不存在 {d}")
    for p in sorted(MSGS.glob("*.md")):
        m, _ = parse(p)
        if m.get("from") not in AGENTS or m.get("to") not in (*AGENTS, "all"):
            problems.append(f"{p.name}: from/to 非法")
        if m.get("task") and m["task"] not in ids:
            problems.append(f"{p.name}: task 不存在 {m['task']}")
    if problems:
        print("通讯结构问题：")
        for x in problems:
            print("  -", x)
        return 1
    print(f"通讯结构校验通过：任务 {len(ids)} 个，消息 {len(list(MSGS.glob('*.md')))} 条")
    return 0


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("inbox"); s.add_argument("name"); s.add_argument("--all", action="store_true"); s.set_defaults(fn=cmd_inbox)
    s = sub.add_parser("send")
    s.add_argument("--from", dest="from", required=True); s.add_argument("--to", required=True)
    s.add_argument("--subject", required=True); s.add_argument("--body"); s.add_argument("--body-file")
    s.add_argument("--task"); s.add_argument("--thread"); s.set_defaults(fn=cmd_send)
    s = sub.add_parser("ack"); s.add_argument("name"); s.add_argument("--all", action="store_true")
    s.add_argument("files", nargs="*"); s.set_defaults(fn=cmd_ack)
    s = sub.add_parser("status"); s.add_argument("task"); s.add_argument("status")
    s.add_argument("--by", required=True); s.add_argument("--note"); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("board"); s.set_defaults(fn=cmd_board)
    t = sub.add_parser("task"); tsub = t.add_subparsers(dest="sub", required=True)
    n = tsub.add_parser("new"); n.add_argument("--owner", required=True); n.add_argument("--title", required=True)
    n.add_argument("--priority", default="P1"); n.add_argument("--depends"); n.add_argument("--body-file")
    n.set_defaults(fn=cmd_task_new)
    s = sub.add_parser("check"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("reply"); s.add_argument("file"); s.add_argument("--from", dest="from", required=True)
    s.add_argument("--body"); s.add_argument("--body-file"); s.set_defaults(fn=cmd_reply)
    s = sub.add_parser("thread"); s.add_argument("key"); s.set_defaults(fn=cmd_thread)
    s = sub.add_parser("say"); s.add_argument("--from", dest="from", required=True); s.add_argument("--to", required=True)
    s.add_argument("text"); s.set_defaults(fn=cmd_say)
    s = sub.add_parser("chat"); s.add_argument("name"); s.add_argument("--tail", type=int, default=0); s.set_defaults(fn=cmd_chat)
    s = sub.add_parser("notify"); s.add_argument("name"); s.set_defaults(fn=cmd_notify)
    s = sub.add_parser("watch"); s.add_argument("name"); s.add_argument("--timeout", type=int, default=3300)
    s.add_argument("--interval", type=int, default=3); s.set_defaults(fn=cmd_watch)
    s = sub.add_parser("presence"); s.add_argument("name", nargs="?"); s.set_defaults(fn=cmd_presence)
    s = sub.add_parser("ping"); s.add_argument("name"); s.set_defaults(fn=cmd_ping)
    a = ap.parse_args()
    r = a.fn(a)
    return r if isinstance(r, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
