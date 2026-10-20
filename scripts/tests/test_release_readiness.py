#!/usr/bin/env python3
"""release_readiness 自测：解析与降级路径。不引测试框架，不真的调 gh。"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "release_readiness", ROOT / "release_readiness.py"
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
# dataclass 解析注解时要能从 sys.modules 找到本模块
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def test_group_porcelain() -> None:
    text = "\n".join(
        [
            " M comms/a.md",
            "M  comms/b.md",
            "?? comms/c.md",
            " M docs/RELEASE-TODO.md",
            "?? mentor/jiuzhou/x",
            " D scripts/old.py",
            "?? root-file.txt",
            "R  practice/old -> practice/new",
        ]
    )
    modified, untracked = mod.group_porcelain(text)
    expect(modified.get("comms") == 2, f"comms 已修改应为 2：{modified}")
    expect(modified.get("docs") == 1, f"docs：{modified}")
    expect(modified.get("scripts") == 1, f"scripts：{modified}")
    expect(modified.get("practice") == 1, f"practice 重命名：{modified}")
    expect(untracked.get("comms") == 1, f"comms 未跟踪：{untracked}")
    expect(untracked.get("mentor") == 1, f"mentor：{untracked}")
    expect(untracked.get("(根)") == 1, f"根文件：{untracked}")
    expect("docs" not in untracked, "docs 不应进未跟踪")


def test_ahead_behind() -> None:
    expect(mod.parse_ahead_behind("0\t3") == (0, 3), "超前 3")
    expect(mod.parse_ahead_behind("2\t0") == (2, 0), "落后 2")
    expect(mod.parse_ahead_behind("0\t0") == (0, 0), "同步")
    expect(mod.parse_ahead_behind("") == (0, 0), "空")


def test_github_slug() -> None:
    expect(
        mod.parse_github_slug("git@github.com:iguoya/Athena.git") == "iguoya/Athena",
        "SSH",
    )
    expect(
        mod.parse_github_slug("https://github.com/iguoya/Athena.git") == "iguoya/Athena",
        "HTTPS .git",
    )
    expect(
        mod.parse_github_slug("https://github.com/iguoya/Athena") == "iguoya/Athena",
        "HTTPS 无 .git",
    )
    expect(mod.parse_github_slug("git@gitlab.com:x/y.git") is None, "非 GitHub")


def test_release_todo() -> None:
    text = """# 下一版
- [x] 已完成的不要
- [ ] 第一条未做
- [ ] 第二条带 `code`
不带标记的行
  - [ ] 缩进也算
"""
    items = mod.parse_open_todos(text)
    expect(len(items) == 3, f"应 3 条：{items}")
    expect(items[0] == "第一条未做", items[0])
    expect("code" in items[1], items[1])
    expect(items[2] == "缩进也算", items[2])


def test_changelog_and_version() -> None:
    expect(mod.next_patch_version("10.0.0") == "10.0.1", "patch+1")
    text = "## [10.0.0] - 2026-10-18\n\n正文\n\n## [9.0.0] - 2026-01-01\n"
    expect(mod.changelog_has_version(text, "10.0.0"), "有 10.0.0")
    expect(not mod.changelog_has_version(text, "10.0.1"), "无 10.0.1")


def test_classify_touched() -> None:
    sens, apps, dirs = mod.classify_touched(
        [".github/workflows/ci.yml", "programming/snake/foo", "README.md"]
    )
    expect(sens and apps, "应同时命中")
    expect(dirs == ["programming"], dirs)
    sens2, apps2, _ = mod.classify_touched(["docs/x.md", "Cargo.lock"])
    expect(sens2 and not apps2, "锁文件算敏感、不算应用目录")


def test_gh_unavailable_is_yellow() -> None:
    def fake_git(*args: str, check: bool = True) -> str:
        cmd = list(args)
        if cmd[:2] == ["remote", "get-url"]:
            return "git@github.com:iguoya/Athena.git\n"
        if cmd[:3] == ["rev-parse", "--verify", "origin/main"]:
            return "abc\n"
        if cmd[0] == "rev-list" and "--left-right" in cmd:
            return "0\t0\n"
        if cmd[0] == "status":
            return ""
        if check:
            raise RuntimeError(f"未桩的 git：{cmd}")
        return ""

    def fake_gh(_args: list[str]) -> tuple[int, str, str]:
        return 1, "", "gh: Not logged into any GitHub hosts"

    buf = io.StringIO()
    # 只测 CI 项：直接调 check_ci
    finding = mod.check_ci(fake_git, fake_gh)
    expect(finding.level == "黄", f"gh 失败应为黄：{finding}")
    expect("gh" in finding.detail.lower() or "无法查询" in finding.detail, finding.detail)


def _git_origin(*args: str, check: bool = True) -> str:
    cmd = list(args)
    if cmd[:2] == ["remote", "get-url"]:
        return "git@github.com:iguoya/Athena.git\n"
    if cmd[:2] == ["rev-list", "--count"]:
        return "0\n"
    if check:
        raise RuntimeError(f"未桩的 git：{cmd}")
    return ""


def _gh_one_full_run(run: dict, jobs: list[dict]):
    def fake_gh(args: list[str]) -> tuple[int, str, str]:
        if args[:2] == ["run", "list"]:
            return 0, json.dumps([run]), ""
        if args[:1] == ["api"]:
            return 0, "30\n", ""
        if args[:2] == ["run", "view"]:
            return 0, json.dumps({"jobs": jobs}), ""
        return 1, "", f"未桩的 gh：{args}"

    return fake_gh


def _sample_run(status: str, conclusion: str | None) -> dict:
    return {
        "databaseId": 39344238323,
        "status": status,
        "conclusion": conclusion,
        "headSha": "abc123def4567890",
        "updatedAt": "2026-10-20T00:00:00Z",
        "url": "https://github.com/iguoya/Athena/actions/runs/39344238323",
    }


def test_ci_in_progress_is_yellow() -> None:
    jobs = [
        {"name": "sources", "status": "completed", "conclusion": "success"},
        {"name": "tauri", "status": "in_progress", "conclusion": ""},
        {"name": "skipped-os", "status": "completed", "conclusion": "skipped"},
    ]
    finding = mod.check_ci(_git_origin, _gh_one_full_run(_sample_run("queued", None), jobs))
    expect(finding.level == "黄", f"进行中应为黄：{finding}")
    expect("进行中：已完成 1 / 共 2 个作业" in finding.detail, finding.detail)
    expect("已失败" not in finding.detail, finding.detail)


def test_ci_partial_failure_while_running_is_yellow() -> None:
    jobs = [
        {"name": "linux", "status": "completed", "conclusion": "failure"},
        {"name": "windows", "status": "in_progress", "conclusion": ""},
        {"name": "macos", "status": "completed", "conclusion": "success"},
    ]
    finding = mod.check_ci(
        _git_origin, _gh_one_full_run(_sample_run("queued", None), jobs)
    )
    expect(finding.level == "黄", f"部分失败且未结束应为黄：{finding}")
    expect("进行中：已完成 2 / 共 3 个作业" in finding.detail, finding.detail)
    expect("linux" in finding.detail, finding.detail)
    expect("已失败" in finding.detail, finding.detail)


def test_ci_completed_success_is_green() -> None:
    jobs = [
        {"name": "sources", "status": "completed", "conclusion": "success"},
        {"name": "tauri", "status": "completed", "conclusion": "success"},
    ]
    finding = mod.check_ci(
        _git_origin, _gh_one_full_run(_sample_run("completed", "success"), jobs)
    )
    expect(finding.level == "绿", f"已完成成功应为绿：{finding}")


def test_ci_completed_failure_is_red() -> None:
    jobs = [
        {"name": "sources", "status": "completed", "conclusion": "success"},
        {"name": "tauri", "status": "completed", "conclusion": "failure"},
    ]
    finding = mod.check_ci(
        _git_origin, _gh_one_full_run(_sample_run("completed", "failure"), jobs)
    )
    expect(finding.level == "红", f"已完成失败应为红：{finding}")
    expect("tauri" in finding.detail, finding.detail)


def test_workspace_red_when_dirty() -> None:
    def fake_git(*args: str, check: bool = True) -> str:
        if args[0] == "status":
            return " M comms/a.md\n?? docs/x.md\n"
        raise RuntimeError(args)

    finding = mod.check_workspace(fake_git)
    expect(finding.level == "红", finding)
    expect("comms" in finding.detail and "docs" in finding.detail, finding.detail)


def test_remote_behind_red_ahead_yellow() -> None:
    def behind(*args: str, check: bool = True) -> str:
        if args[:3] == ("rev-parse", "--verify", "origin/main"):
            return "x\n"
        if "origin/main...main" in args:
            return "2\t0\n"
        raise RuntimeError(args)

    def ahead(*args: str, check: bool = True) -> str:
        if args[:3] == ("rev-parse", "--verify", "origin/main"):
            return "x\n"
        if "origin/main...main" in args:
            return "0\t4\n"
        raise RuntimeError(args)

    expect(mod.check_remote(behind).level == "红", "落后应红")
    expect(mod.check_remote(ahead).level == "黄", "超前应黄")


def main() -> int:
    mod.force_utf8_output()
    test_group_porcelain()
    test_ahead_behind()
    test_github_slug()
    test_release_todo()
    test_changelog_and_version()
    test_classify_touched()
    test_gh_unavailable_is_yellow()
    test_ci_in_progress_is_yellow()
    test_ci_partial_failure_while_running_is_yellow()
    test_ci_completed_success_is_green()
    test_ci_completed_failure_is_red()
    test_workspace_red_when_dirty()
    test_remote_behind_red_ahead_yellow()
    print("ok — release_readiness 自测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
