#!/usr/bin/env python3
"""prepare 开头接入 readiness 的门禁自测。

不真的 prepare：只测 gate_on_readiness 对红/黄/dry-run/skip 的反应；
git / gh 用桩，不碰 push。
"""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# release.py 在运行时从 scripts/ 导入 release_readiness；测试进程的 path 默认没有这一层
sys.path.insert(0, str(ROOT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


release = _load("release", ROOT / "release.py")


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def test_red_rejects() -> None:
    """有红：打印后拒绝（SystemExit），退出信息点明红与处理方式。"""
    buf = io.StringIO()

    def dirty() -> int:
        buf.write("[红] 工作区：已修改：comms 1\n结论：有 1 项红\n")
        return 1

    with redirect_stdout(buf):
        try:
            release.gate_on_readiness(dry_run=False, skip=False, readiness_runner=dirty)
        except SystemExit as exc:
            msg = str(exc)
            expect("红" in msg, f"应说明有红：{msg}")
            expect("skip-readiness" in msg or "怎么处理" in msg or "修好" in msg, msg)
            expect("工作区" in buf.getvalue(), "应先打印体检表")
            return
    raise SystemExit("有红时应收 SystemExit，却放行了")


def test_yellow_allows() -> None:
    """无红只有黄：打印后继续（不抛）。"""
    buf = io.StringIO()

    def yellow_only() -> int:
        buf.write("[黄] CHANGELOG：还没有下一节\n结论：有 1 项黄（无红，可以准备 prepare，先看黄项）\n")
        return 0

    with redirect_stdout(buf):
        release.gate_on_readiness(dry_run=False, skip=False, readiness_runner=yellow_only)
    expect("CHANGELOG" in buf.getvalue(), buf.getvalue())


def test_dry_run_red_allows() -> None:
    """--dry-run 下红只提示、不拒绝。"""
    buf = io.StringIO()

    def dirty() -> int:
        buf.write("[红] 与远端：落后 2\n结论：有 1 项红\n")
        return 1

    with redirect_stdout(buf):
        release.gate_on_readiness(dry_run=True, skip=False, readiness_runner=dirty)
    text = buf.getvalue()
    expect("dry-run" in text and "红" in text, text)
    expect("不拒绝" in text or "仅提示" in text, text)


def test_skip_readiness() -> None:
    """--skip-readiness：不调体检，打印醒目警告。"""
    called = {"n": 0}

    def should_not_run() -> int:
        called["n"] += 1
        return 1

    buf = io.StringIO()
    with redirect_stdout(buf):
        release.gate_on_readiness(
            dry_run=False, skip=True, readiness_runner=should_not_run
        )
    expect(called["n"] == 0, "skip 时不应调用 readiness")
    expect("已跳过发版体检" in buf.getvalue(), buf.getvalue())


def _git_stub(porcelain: str, left_right: str = "0\t0"):
    def fake(*args: str, check: bool = True) -> str:
        cmd = list(args)
        if cmd[:1] == ["status"]:
            return porcelain
        if cmd[:3] == ["rev-parse", "--verify", "origin/main"]:
            return "abc\n"
        if "--left-right" in cmd:
            return left_right if left_right.endswith("\n") else left_right + "\n"
        if cmd[:2] == ["remote", "get-url"]:
            return "git@github.com:iguoya/Athena.git\n"
        if cmd[:2] == ["rev-list", "--count"]:
            return "0\n"
        raise RuntimeError(f"未桩的 git：{cmd}")

    return fake


def _gh_down(_args: list[str]) -> tuple[int, str, str]:
    return 1, "", "gh: not logged in"


def test_red_with_git_gh_stubs() -> None:
    """真走 readiness：工作区脏是红，git/gh 都是桩，不 prepare。"""
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            release.gate_on_readiness(
                dry_run=False,
                skip=False,
                git=_git_stub(" M comms/a.md\n"),
                gh=_gh_down,
            )
        except SystemExit as exc:
            text = buf.getvalue()
            expect("工作区" in text and "怎么处理" in text, text)
            expect("红" in str(exc), str(exc))
            return
    raise SystemExit("桩出的红项应拒绝 prepare")


def test_yellow_with_git_gh_stubs() -> None:
    """工作区干净、远端超前、gh 不可用都是黄：放行。"""
    buf = io.StringIO()
    with redirect_stdout(buf):
        release.gate_on_readiness(
            dry_run=False,
            skip=False,
            git=_git_stub("", "0\t2"),
            gh=_gh_down,
        )
    text = buf.getvalue()
    expect("黄" in text, text)
    expect("结论：有" in text and "项红" not in text.split("结论：", 1)[-1], text)


def test_check_prerequisites_no_workspace_or_sync() -> None:
    """check_prerequisites 不再判工作区 / 远端同步（口径归 readiness）。"""
    src = (ROOT / "release.py").read_text(encoding="utf-8")
    # 旧口径：status --untracked-files=no、rev-list 两边计数；去掉后不应再出现在该函数体里
    start = src.index("def check_prerequisites")
    end = src.index("\ndef ", start + 1)
    body = src[start:end]
    expect("untracked-files" not in body, "不应再查工作区 porcelain")
    expect("origin/main..main" not in body, "不应再判超前")
    expect("main..origin/main" not in body, "不应再判落后")
    expect("branch" in body, "应保留 main 分支检查")
    expect("版本只增" in body or "不大于" in body, "应保留版本只增检查")
    expect("tag" in body, "应保留 tag 占用检查")


def main() -> int:
    test_red_rejects()
    test_yellow_allows()
    test_dry_run_red_allows()
    test_skip_readiness()
    test_red_with_git_gh_stubs()
    test_yellow_with_git_gh_stubs()
    test_check_prerequisites_no_workspace_or_sync()
    print("ok — release prepare 门禁自测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
