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
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMS = ROOT / "docs" / "comms"
TASKS = COMMS / "tasks"
MSGS = COMMS / "msgs"
READ = COMMS / "read"

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
    if a.task:
        find_task(a.task)
        meta["task"] = a.task
    (MSGS / name).write_text(dump(meta, "\n" + body.strip() + "\n"), encoding="utf-8")
    print("已发送：", name)


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
    s.add_argument("--task"); s.set_defaults(fn=cmd_send)
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
    a = ap.parse_args()
    r = a.fn(a)
    return r if isinstance(r, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
