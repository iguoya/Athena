"""跨应用工程卫生检查：工具链一致、Rust 格式、供应链安全扫描（ADR 0170）。

从 check.py 拆出来单独成模块：check.py 已经装了出处、工作流、结构卫生等一长串检查，
新增的几项逻辑互相独立，放在一起各自好读，也不必为它们再撑大入口文件。
check.py 只负责按顺序调用这里的 run_* 函数。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 两个互相独立的 Cargo 工作区（ADR 0140）：仓库根的 Tauri 壳工作区与 launcher/。
CARGO_WORKSPACES = (REPO_ROOT, REPO_ROOT / "launcher")


def _workflows() -> list[Path]:
    return sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))


def run_toolchain_check() -> None:
    """工具链版本只在一处声明，其余地方必须跟它一致。

    Rust 钉在 rust-toolchain.toml，发版工作流里 dtolnay/rust-toolchain 的版本号要与它相同；
    Node 钉在 .node-version，工作流一律用 node-version-file 读它，不再写死数字。
    不一致的后果是本地能过、CI 或发版用了另一个编译器，问题只在远端暴露。
    """
    print("== 跨应用检查：工具链一致 ==", flush=True)
    problems: list[str] = []

    channel = tomllib.loads((REPO_ROOT / "rust-toolchain.toml").read_text(encoding="utf-8"))[
        "toolchain"
    ]["channel"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", channel):
        problems.append(f"rust-toolchain.toml 的 channel 必须是具体版本号，现在是 {channel!r}")

    msrv = re.search(
        r'^rust-version\s*=\s*"([\d.]+)"', (REPO_ROOT / "launcher" / "Cargo.toml").read_text(encoding="utf-8"), re.M
    )
    if msrv and tuple(map(int, msrv.group(1).split("."))) > tuple(map(int, channel.split("."))):
        problems.append(f"launcher/Cargo.toml 的 rust-version {msrv.group(1)} 高于钉住的工具链 {channel}")

    for wf in _workflows():
        text = wf.read_text(encoding="utf-8")
        rel = wf.relative_to(REPO_ROOT)
        for version in re.findall(r"dtolnay/rust-toolchain@(\S+)", text):
            if version != channel:
                problems.append(f"{rel} 用了 dtolnay/rust-toolchain@{version}，应为 @{channel}（见 rust-toolchain.toml）")
        for line in text.splitlines():
            if re.match(r"\s*node-version\s*:", line):
                problems.append(f"{rel} 写死了 node-version，应改为 node-version-file: .node-version：{line.strip()}")

    if not re.fullmatch(r"\d+(\.\d+){0,2}", (REPO_ROOT / ".node-version").read_text(encoding="utf-8").strip()):
        problems.append(".node-version 应只含一个版本号，如 22")

    if problems:
        print("\n".join(f"  {p}" for p in problems), flush=True)
        raise SystemExit("工具链一致检查没通过，见上方。")


def run_rustfmt_check() -> None:
    """两个 Cargo 工作区都必须符合 rustfmt 默认风格。

    不写 rustfmt.toml：默认风格就是社区共识，少一份要维护的配置。
    """
    print("== 跨应用检查：Rust 格式 ==", flush=True)
    if shutil.which("cargo") is None:
        raise SystemExit("缺 cargo，Rust 格式检查跑不了。安装 rustup：https://rustup.rs（版本由 rust-toolchain.toml 自动拉取）")
    failed = [
        ws.relative_to(REPO_ROOT).as_posix() or "."
        for ws in CARGO_WORKSPACES
        if subprocess.run(["cargo", "fmt", "--all", "--check"], cwd=ws, capture_output=True).returncode != 0
    ]
    if failed:
        raise SystemExit(f"这些 Cargo 工作区不符合 rustfmt：{'、'.join(failed)}。在对应目录跑 cargo fmt --all 修正。")


def _need_tools(tools: dict[str, str]) -> None:
    missing = [name for name in tools if shutil.which(name) is None]
    if missing:
        raise SystemExit(
            "缺 " + "、".join(missing) + "，安全扫描跑不了。安装：\n"
            + "\n".join(f"  {tools[name]}" for name in missing)
        )


def _pnpm_audit_summary() -> str:
    """pnpm audit 的摘要。只统计生产依赖：开发工具链的告警对安装包没有影响。"""
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        return "pnpm 未安装，跳过依赖审计（见 docs/ENGINEERING.md「包管理器」）"
    done = subprocess.run([pnpm, "audit", "--prod", "--json"], cwd=REPO_ROOT, capture_output=True, text=True)
    try:
        counts = json.loads(done.stdout)["metadata"]["vulnerabilities"]
    except (ValueError, KeyError):
        # 注册表不可达等：无法判断，如实说出，不当作没问题。
        return "pnpm audit 没有得到可解析的结果（网络或注册表不可达？），本次未审计"
    found = {sev: n for sev, n in counts.items() if n}
    return "生产依赖无已知漏洞" if not found else f"生产依赖有已知漏洞 {found}，运行 pnpm audit --prod 查看"


def run_security_scan() -> None:
    """供应链与密钥扫描（`check.py --security`，CI 的跨应用任务里跑）。

    - gitleaks：扫全部提交历史与当前工作区，**阻断**。密钥一旦进历史就删不干净，
      发现越早越好；已核实的误报登记在 .gitleaks.toml。
    - cargo-deny 的漏洞公告：两个 Cargo 工作区，**只报告**。Tauri 在 Linux 的依赖里有
      gtk3 绑定停止维护这类公告，我们治不了，阻断只会让 CI 常年红；先看清现状再决定升级阻断。
    - pnpm audit：生产依赖，**只报告**，理由同上。
    """
    print("== 跨应用检查：安全扫描 ==", flush=True)
    _need_tools(
        {
            "gitleaks": "macOS: brew install gitleaks；Windows: winget install gitleaks.gitleaks；"
            "Linux: 从 https://github.com/gitleaks/gitleaks/releases 下载二进制",
            "cargo-deny": "cargo install --locked cargo-deny（或从 https://github.com/EmbarkStudios/cargo-deny/releases 下载二进制）",
        }
    )

    leaks = [
        subprocess.run(["gitleaks", mode, "--no-banner", "--redact", "-l", "error", "."], cwd=REPO_ROOT).returncode
        for mode in ("git", "dir")
    ]

    print("  gitleaks：" + ("未发现密钥" if not any(leaks) else "发现疑似密钥"), flush=True)

    for ws in CARGO_WORKSPACES:
        label = ws.relative_to(REPO_ROOT).as_posix() or "."
        done = subprocess.run(
            ["cargo", "deny", "--workspace", "check", "advisories"], cwd=ws, capture_output=True, text=True
        )
        verdict = "无漏洞公告" if done.returncode == 0 else "有公告或无法取得公告库（只报告，不阻断），详情："
        print(f"  cargo-deny [{label}]：{verdict}", flush=True)
        if done.returncode != 0:
            print("    " + "\n    ".join((done.stderr or done.stdout).strip().splitlines()[-12:]), flush=True)

    print(f"  pnpm audit：{_pnpm_audit_summary()}", flush=True)

    if any(leaks):
        raise SystemExit("gitleaks 发现疑似密钥，见上方。确认是误报再登记进 .gitleaks.toml，真泄露要先轮换凭据。")
