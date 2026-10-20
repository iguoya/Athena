#!/usr/bin/env python3
"""prepare 接入应用版本计划（ADR 0171）的自测：--bump 解析、按计划写清单、readiness 的版本计划检查。

不真的 prepare、不打 tag：release_plan 的计算用桩，清单写在临时目录里。
"""

from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


release_plan = _load("release_plan")
release = _load("release")
readiness = _load("release_readiness")


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def test_parse_bump_overrides() -> None:
    parsed = release.parse_bump_overrides(["snake=minor", "driver=10.2.0", "snake=major"])
    expect(parsed == {"snake": "major", "driver": "10.2.0"}, f"后一次为准：{parsed}")
    for bad in ("snake", "=minor", "snake="):
        try:
            release.parse_bump_overrides([bad])
        except SystemExit:
            continue
        raise SystemExit(f"应拒绝：{bad}")


def _decision(app_id: str, **extra) -> dict:
    base = {
        "id": app_id,
        "changed": True,
        "new": False,
        "bump": "patch",
        "current": "10.0.0",
        "suggested": "10.0.1",
        "reasons": ["目录有改动：x"],
    }
    base.update(extra)
    return base


def _stub_plan(decisions: list[dict], apps: list[dict]):
    release_plan.latest_version_tag = lambda _repo: "v10.0.0"
    release_plan.load_apps = lambda path=None: apps
    release_plan.compute_decisions = lambda _repo, _apps, _base, _head: decisions


APPS = [
    {"id": "snake", "root": "programming", "kind": "tauri", "manifest": "programming/snake/src-tauri/tauri.conf.json", "manifest_format": "tauri_conf"},
    {"id": "driver", "root": "certification", "kind": "driver", "manifest": "certification/driver/pubspec.yaml", "manifest_format": "pubspec"},
    {"id": "jiuzhou", "root": "mentor", "kind": "tauri", "manifest": "mentor/jiuzhou/src-tauri/tauri.conf.json", "manifest_format": "tauri_conf"},
    {"id": "pocket-cube-solver", "root": "programming", "kind": "tauri", "manifest": "programming/pocket-cube-solver/src-tauri/tauri.conf.json", "manifest_format": "tauri_conf"},
]


def test_plan_release_overrides_and_skips() -> None:
    decisions = [
        _decision("snake"),
        _decision("driver", current="10.0.0+1", suggested="10.0.1+1"),
        _decision("jiuzhou", bump="none", suggested="10.0.1", current="10.0.1"),  # 已升过
        _decision("pocket-cube-solver", new=True, bump="none", current="1.0.0", suggested="1.0.0"),
        {**_decision("x"), "changed": False},
    ]
    _stub_plan(decisions, APPS)
    changes, fresh, base = release.plan_release({})
    ids = [c["id"] for c in changes]
    expect(ids == ["snake", "driver"], f"已升过与未改动的不再升：{ids}")
    expect([f["id"] for f in fresh] == ["pocket-cube-solver"] and base == "v10.0.0", "新应用单列")

    changes, _fresh, _base = release.plan_release({"snake": "minor", "driver": "10.2.0"})
    by_id = {c["id"]: c for c in changes}
    expect(by_id["snake"]["new"] == "10.1.0" and by_id["snake"]["level"] == "minor", by_id["snake"])
    expect(by_id["driver"]["new"] == "10.2.0", by_id["driver"])

    for bad in ({"jiuzhou": "minor"}, {"nobody": "patch"}, {"snake": "10.0.0"}, {"snake": "huge"}):
        try:
            release.plan_release(bad)
        except SystemExit:
            continue
        raise SystemExit(f"应拒绝 --bump：{bad}")

    _stub_plan([{**_decision("snake"), "changed": False}], APPS)
    try:
        release.plan_release({})
    except SystemExit as exc:
        expect("没有任何应用有改动" in str(exc), str(exc))
    else:
        raise SystemExit("没有改动时应拒绝发版")


def test_apply_release_plan_touches_only_version() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        crlf = chr(13) + chr(10)
        conf = root / "programming/snake/src-tauri/tauri.conf.json"
        conf.parent.mkdir(parents=True)
        original = ("{" + crlf + '  "productName": "贪吃蛇",' + crlf + '  "version": "10.0.0",' + crlf + '  "identifier": "x"' + crlf + "}" + crlf).encode("utf-8")
        conf.write_bytes(original)
        pub = root / "certification/driver/pubspec.yaml"
        pub.parent.mkdir(parents=True)
        pub.write_bytes(("name: driver" + chr(10) + "version: 10.0.0+1" + chr(10) + "x: y" + chr(10)).encode("utf-8"))
        saved = release.REPO_ROOT
        release.REPO_ROOT = root
        try:
            changes = [
                {"id": "snake", "manifest": "programming/snake/src-tauri/tauri.conf.json", "format": "tauri_conf", "old": "10.0.0", "new": "10.0.1", "level": "patch"},
                {"id": "driver", "manifest": "certification/driver/pubspec.yaml", "format": "pubspec", "old": "10.0.0+1", "new": "10.0.1+1", "level": "patch"},
            ]
            buf = io.StringIO()
            with redirect_stdout(buf):
                dry = release.apply_release_plan(changes, True)
            expect(dry == [] and conf.read_bytes() == original, "dry-run 不写文件")
            with redirect_stdout(buf):
                written = release.apply_release_plan(changes, False)
        finally:
            release.REPO_ROOT = saved
        expect(written == [c["manifest"] for c in changes], written)
        expect(conf.read_bytes() == original.replace(b'"10.0.0"', b'"10.0.1"'), "tauri 清单只能变版本那一处")
        expect(b"version: 10.0.1+1" in pub.read_bytes() and b"x: y" in pub.read_bytes(), "pubspec 构建号沿用")


def test_check_plan_levels() -> None:
    def git_untagged(*_args: str, check: bool = True) -> str:
        return ""

    def git_tagged(*_args: str, check: bool = True) -> str:
        return "v10.1.0\n"

    pending = lambda: ([_decision("snake")], "v10.0.0")  # noqa: E731
    none_pending = lambda: ([{**_decision("snake"), "changed": False}], "v10.0.0")  # noqa: E731
    fresh_only = lambda: ([_decision("pocket-cube-solver", new=True, bump="none")], "v10.0.0")  # noqa: E731

    expect(readiness.check_plan(git_untagged, pending).level == "黄", "prepare 之前有改动只是黄")
    red = readiness.check_plan(git_tagged, pending)
    expect(red.level == "红" and "snake" in red.detail, f"已打 tag 还有应用没升版本是红：{red}")
    expect(readiness.check_plan(git_tagged, none_pending).level == "黄", "打了 tag 且没有待升的不红")
    expect(readiness.check_plan(git_untagged, none_pending).level == "黄", "没有可发布内容是黄")
    expect("新应用" in readiness.check_plan(git_untagged, fresh_only).detail, "新应用单独说明")

    def broken() -> tuple[list[dict], str]:
        raise RuntimeError("cargo 不在 PATH")

    degraded = readiness.check_plan(git_untagged, broken)
    expect(degraded.level == "黄" and "cargo" in degraded.detail, f"算不出时降级为黄：{degraded}")


def main() -> int:
    release.force_utf8_output() if hasattr(release, "force_utf8_output") else None
    test_parse_bump_overrides()
    test_plan_release_overrides_and_skips()
    test_apply_release_plan_touches_only_version()
    test_check_plan_levels()
    print("ok — release prepare 应用版本计划自测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
