#!/usr/bin/env python3
"""给 comms 里的代理单开一个新会话去做一个任务（ADR 0165 的补充：开会话）。

comms.py 只管「说话」，对方只在自己下一轮开工时才看到；这里补上「叫人」：
为某个代理起一个全新的无头会话（不碰它正在跑的旧会话），首句就是
「先 inbox、认领 T-xxx、做完转 review」。新旧会话靠 comms 的认领机制分流，
所以不会抢同一个任务；文件层面的撞车仍由任务书里的 owned 路径约束。

    python comms/spawn.py zcode  --project driver --task T-104
    python comms/spawn.py cursor --project driver --task T-014 --dry-run
    python comms/spawn.py zcode  --project driver --task T-104 --note "先看 ADR 0130"

各代理的开法（只用它自己的命令行入口，不碰它的桌面窗口）：
- zcode：``node <ZCode>/resources/glm/zcode.cjs -p <提示词>``，完全无头、后台运行。
- cursor：优先用独立的 Cursor CLI（``cursor-agent`` 或 ``agent``，装了才有）；没装则
  降级成「打开 Cursor 新对话并预填提示词」，需要使用者按一下回车。
- claude-code：``claude -p <提示词>``。

无头会话的输出写到 ``comms/<舱>/runs/<时间>-<代理>-<任务>.log``。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMS = ROOT / "comms"


def die(msg: str) -> "None":
    raise SystemExit(f"spawn: {msg}")


def load_cabin(project: str) -> dict:
    cfg = COMMS / project / "config.json"
    if not cfg.is_file():
        known = "、".join(sorted(p.parent.name for p in COMMS.glob("*/config.json")))
        die(f"舱不存在：comms/{project}/config.json；已有舱：{known}")
    return json.loads(cfg.read_text(encoding="utf-8"))


def read_task(project: str, tid: str) -> tuple[Path, dict[str, str]]:
    found = sorted((COMMS / project / "tasks").glob(f"{tid}-*.md"))
    if not found:
        die(f"舱 {project} 里没有任务 {tid}")
    meta: dict[str, str] = {}
    lines = found[0].read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() == "---":
        for ln in lines[1:]:
            if ln.strip() == "---":
                break
            k, _, v = ln.partition(":")
            meta[k.strip()] = v.strip()
    return found[0], meta


def build_prompt(agent: str, project: str, tid: str | None, note: str) -> str:
    inbox = f"python comms/comms.py inbox {agent} --project {project}"
    parts = [
        f"你是 {agent}，在 Athena 仓库（当前目录是仓库根）的协作舱「{project}」里被单开一个新会话。",
        "先读根 AGENTS.md 与 comms/README.md，遵守其中的多代理并行规则。",
        f"第一步运行：{inbox}",
    ]
    if tid:
        parts += [
            f"然后读任务书 comms/{project}/tasks/{tid}-*.md，按它的目标与验收口径执行。",
            f"开工先认领：python comms/comms.py status {tid} doing --by {agent} --project {project}。"
            "若该任务已被别的会话认领（doing 且不是你刚认领的），停下并发消息说明，不要重复做。",
            f"做完跑任务书要求的检查，再 python comms/comms.py status {tid} review --by {agent} "
            f'--note "验证命令输出摘要 + 证据路径" --project {project}；卡住用 blocked 并写明卡在哪。'
            "done 只有 leader 能标。",
        ]
    parts += [
        "只改自己名下的路径；git add 写明确路径，不整目录添加；工作区里不是你改的未提交改动，"
        "不修改、不回退、不顺带提交；撞到别人的改动先停下，发消息说明。",
        "你是无头会话，没人实时回答：需要裁决就发消息给 leader 并把任务转 blocked，别空等。",
    ]
    if note:
        parts.append(f"补充说明：{note}")
    return "\n".join(parts)


def find_node() -> str:
    node = shutil.which("node")
    if not node:
        die("找不到 node（ZCode 的命令行入口是 Node 脚本）")
    return node


ZCODE_MODEL = ("account:bigmodel-individual-coding-plan", "GLM-5.3")


def zcode_cli() -> tuple[list[str], dict[str, str]]:
    """返回 (命令前缀, 额外环境变量)。

    zcode.cjs 是为 SEA 单文件包写的：它按入口脚本的相对位置找内置 provider 配置，装在
    resources/glm/ 下时落空；无头模式也没有「默认模型」。所以在 ~/.zcode/spawn-cli/
    放一个垫片：入口路径指向垫片目录（里面有 provider/ 副本），并用私有的 personal
    provider 配置给出默认模型——不改 ZCode 桌面端自己的配置。
    """
    install = None
    for p in (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "ZCode/resources",
        Path.home() / "AppData/Local/Programs/ZCode/resources",
        Path("/Applications/ZCode.app/Contents/Resources"),
    ):
        if (p / "glm/zcode.cjs").is_file():
            install = p
            break
    if install is None:
        die("找不到 ZCode 的 resources/glm/zcode.cjs；确认 ZCode 已安装")
    shim = Path.home() / ".zcode/spawn-cli"
    (shim / "provider").mkdir(parents=True, exist_ok=True)
    builtin = install / "config/provider/zcode-builtin.json"
    shutil.copyfile(builtin, shim / "provider/zcode-builtin.json")
    (shim / "zcode.cjs").touch()  # 入口路径要真实存在（realpath），内容不用
    (shim / "run.cjs").write_text(
        "process.argv[1] = require('path').join(__dirname, 'zcode.cjs');\n"
        "require(process.env.ZCODE_REAL_CJS);\n",
        encoding="utf-8",
    )
    provider, model = ZCODE_MODEL
    (shim / "provider_config.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "config": {
                    "providerConfigRules": {"providerRules": []},
                    "modelConfigRules": {"providerModelRules": [], "manualProviderModelRules": []},
                    "defaultModelSelection": {
                        "providerId": provider,
                        "modelId": model,
                        "options": {"reasoningLevel": "high"},
                    },
                },
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    env = {
        "ZCODE_REAL_CJS": str(install / "glm/zcode.cjs"),
        "ZCODE_BUILTIN_PROVIDER_CONFIG_FILE": str(builtin),
        "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE": str(shim / "provider_config.json"),
    }
    return [find_node(), str(shim / "run.cjs")], env


def cursor_agent_cli() -> list[str] | None:
    r"""独立的 Cursor CLI（cursor-agent）；没装返回 None。

    Windows 的 cursor-agent.cmd 会经 cmd.exe 转手，多行/中文提示词在那里会被截断，
    所以直接跑版本目录里的 node.exe + index.js（装在 %LOCALAPPDATA%\cursor-agent，
    安装脚本会改用户 PATH，但已开着的终端看不到，这里不依赖 PATH）。
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "cursor-agent/versions"
        vers = sorted((d for d in base.glob("20*") if (d / "index.js").is_file()), key=lambda d: d.name)
        return [str(vers[-1] / "node.exe"), str(vers[-1] / "index.js")] if vers else None
    exe = shutil.which("cursor-agent") or shutil.which("agent")
    return [exe] if exe else None


def build_command(agent: str, prompt: str) -> tuple[list[str], dict[str, str]] | None:
    """返回 (无头命令, 额外环境变量)；None 表示该代理没有可用的无头入口（走降级）。"""
    if agent == "zcode":
        head, env = zcode_cli()
        return [*head, "-p", prompt, "--cwd", str(ROOT)], env
    if agent == "claude-code":
        exe = shutil.which("claude")
        if not exe:
            die("找不到 claude 命令")
        return [exe, "-p", prompt], {}
    if agent == "cursor":
        head = cursor_agent_cli()
        if head:
            # --force：无头时没人点确认；--trust：免掉「信任此工作区」提问。范围由提示词与 owned 路径约束
            return [*head, "-p", "--force", "--trust", "--workspace", str(ROOT), prompt], {}
        return None
    die(f"不认识的代理 {agent!r}：spawn.py 只会开 zcode / cursor / claude-code")


def child_env(agent: str, extra: dict[str, str]) -> dict[str, str]:
    """新会话继承调用者的环境，但不能把调用者（常是 Claude Code）的宿主标记带过去。

    Cursor 看到 CLAUDE* 就会按 Claude Code 的约定加载 ``.claude/settings.json`` 里的钩子，
    再看到 ``SHELL=bash`` 就拿 bash 去 eval 钩子的 PowerShell 包装，结果每条 Shell 命令
    都起不来（2026-10-19 pocket-cube-solver 舱 T-001 实测）。非 claude-code 的代理一律去掉。
    """
    env = dict(os.environ)
    if agent != "claude-code":
        for key in list(env):
            if key.startswith(("CLAUDE", "ANTHROPIC_")) or key in ("SHELL", "MSYSTEM"):
                del env[key]
        # Cursor 兼容 Claude 钩子时用它拼 ``$CLAUDE_PROJECT_DIR/.claude/hooks/...``；
        # 不显式给，实测会落成 ``C:\``，钩子找不到脚本、挡住全部 Shell
        env["CLAUDE_PROJECT_DIR"] = str(ROOT)
    env.update(extra)
    return env


def launch_detached(cmd: list[str], env: dict[str, str], log: Path, agent: str) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    out = open(log, "wb")
    kw: dict = {"cwd": str(ROOT), "env": child_env(agent, env), "stdin": subprocess.DEVNULL, "stdout": out, "stderr": subprocess.STDOUT}
    if sys.platform == "win32":
        # 脱离当前终端，关掉调用它的会话也不会带走它
        kw["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    else:
        kw["start_new_session"] = True
    return subprocess.Popen(cmd, **kw).pid


def cursor_fallback(prompt: str, dry: bool, open_it: bool) -> None:
    """没有独立 CLI：用 Cursor 的提示词深链开新对话并预填，使用者回车发送。"""
    link = "cursor://anysphere.cursor-deeplink/prompt?text=" + urllib.parse.quote(prompt)
    print("Cursor 没有可无头运行的 CLI（cursor-agent 未安装），降级为预填新对话。")
    if sys.platform == "win32":
        print("（已装却看不到？Windows 商店版 python 别名看不到 AppData\\Local 下新建的目录，改用 `py comms/spawn.py ...`。）")
    if len(link) > 8000:
        print(f"提示词过长（深链 {len(link)} 字符），请手动把下面这段贴进 Cursor 新对话：\n\n{prompt}")
        return
    if dry or not open_it:
        # 默认不替使用者弹开 Cursor 窗口（会打断他正在做的事）；明确要才开
        print("未打开 Cursor。要让它弹出预填的新对话，加 --open-cursor。")
        return
    if sys.platform == "win32":
        os.startfile(link)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", link], check=False)
    else:
        subprocess.run(["xdg-open", link], check=False)
    print("已让 Cursor 打开新对话并预填提示词——到 Cursor 里按回车发送。")


def main() -> int:
    ap = argparse.ArgumentParser(description="为 comms 代理单开新会话去做一个任务")
    ap.add_argument("agent", help="zcode | cursor | claude-code")
    ap.add_argument("--project", required=True, help="舱名")
    ap.add_argument("--task", help="任务号，如 T-104；不给则只开会话让它先看收件箱")
    ap.add_argument("--note", default="", help="附加到提示词末尾的说明")
    ap.add_argument("--force", action="store_true", help="忽略任务状态/负责人检查")
    ap.add_argument("--open-cursor", action="store_true", help="cursor 无 CLI 时，用深链弹出预填的新对话")
    ap.add_argument("--dry-run", action="store_true", help="只打印提示词和命令，不启动")
    a = ap.parse_args()

    cfg = load_cabin(a.project)
    if a.agent not in cfg.get("agents", []):
        die(f"{a.agent} 不是舱 {a.project} 的成员：{'、'.join(cfg.get('agents', []))}")
    if not a.task and not a.note:
        die("至少给 --task 或 --note，否则新会话不知道要做什么")
    if a.task:
        _, meta = read_task(a.project, a.task)
        if not a.force:
            if meta.get("owner") != a.agent:
                die(f"{a.task} 的负责人是 {meta.get('owner')}，不是 {a.agent}（要改派先在舱内由 leader 决定，或加 --force）")
            if meta.get("status") != "todo":
                die(f"{a.task} 状态是 {meta.get('status')}：只给 todo 任务开新会话，避免和已认领的会话重复（或加 --force）")

    prompt = build_prompt(a.agent, a.project, a.task, a.note)
    built = build_command(a.agent, prompt)
    if built is None:
        # Windows 商店版 python 别名看不到 AppData\\Local 下新建的目录，cursor-agent 装在那里；
        # 换 py 启动器重跑一次（环境变量防止来回套娃），比降级成深链更接近本意
        if sys.platform == "win32" and not os.environ.get("SPAWN_REEXEC"):
            try:
                return subprocess.call(
                    ["py", str(Path(__file__).resolve()), *sys.argv[1:]], env={**os.environ, "SPAWN_REEXEC": "1"}
                )
            except FileNotFoundError:
                pass
        cursor_fallback(prompt, a.dry_run, a.open_cursor)
        return 0
    cmd, env = built
    shown = [c if c != prompt else "<提示词>" for c in cmd]
    if a.dry_run:
        print("命令：", " ".join(shown))
        print("\n提示词：\n" + prompt)
        return 0
    log = COMMS / a.project / "runs" / f"{datetime.now():%Y%m%d-%H%M%S}-{a.agent}-{a.task or 'free'}.log"
    pid = launch_detached(cmd, env, log, a.agent)
    print(f"已为 {a.agent} 单开会话（pid {pid}）。输出：{log.relative_to(ROOT)}")
    print(f"看进展：python comms/comms.py board --project {a.project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
