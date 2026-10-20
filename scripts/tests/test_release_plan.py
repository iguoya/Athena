#!/usr/bin/env python3
"""release_plan 自测。不引测试框架，不真的调 gh，plan 的判断用桩依赖图。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_plan", ROOT / "release_plan.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def test_version_roundtrip_preserves_bytes() -> None:
    tauri = (
        '{\r\n  "productName": "贪吃蛇",\r\n  "version": "0.1.0",\r\n'
        '  "plugins": {"x": {"version": "9.9.9"}}\r\n}\r\n'
    ).encode("utf-8")
    written = mod.write_version(tauri, "tauri_conf", "0.2.0")
    expect(mod.read_version(written, "tauri_conf") == "0.2.0", "tauri 读回")
    expect(b'"version": "9.9.9"' in written, "不能改到后面的 version")
    expect(written.count(b"\r\n") == tauri.count(b"\r\n"), "换行要原样保留")
    expect(written.split(b"version")[0] == tauri.split(b"version")[0], "版本前的字节不变")

    pubspec = "name: demo\r\nversion: 10.0.0+3\r\ndescription: 保持\r\n".encode("utf-8")
    written = mod.write_version(pubspec, "pubspec", "10.1.0")
    expect(mod.read_version(written, "pubspec") == "10.1.0+3", f"构建号应沿用：{written!r}")
    expect(written.endswith("description: 保持\r\n".encode("utf-8")), "pubspec 其余字节")

    meson = "project('Athena', 'cpp',\r\n  version: '10.0.0',\r\n  default_options: ['cpp_std=c++20'])\r\n".encode(
        "utf-8"
    )
    written = mod.write_version(meson, "meson", "10.0.1")
    expect(mod.read_version(written, "meson") == "10.0.1", "meson 读回")
    expect(b"default_options: ['cpp_std=c++20']" in written, "meson 其余字节")

    package = '{ "name": "lab", "version": "0.1.0", "private": true }\n'.encode("utf-8")
    written = mod.write_version(package, "package_json", "0.1.1")
    expect(mod.read_version(written, "package_json") == "0.1.1", "package.json 读回")
    expect(b'"private": true' in written, "package.json 其余字节")


def test_bump_level_and_apply() -> None:
    expect(mod.bump_level(["fix(cpp): 解码"]) == "patch", "fix 是修订")
    expect(mod.bump_level(["feat(snake): 加一章"]) == "minor", "feat 是次版本")
    expect(mod.bump_level(["feat!: 不兼容"]) == "major", "!: 是主版本")
    expect(mod.bump_level(["chore: ⚠️ 路径变了"]) == "major", "⚠️ 是主版本")
    expect(mod.bump_level(["feat(a): x", "fix(b)!: y"]) == "major", "取更高的一档")
    expect(mod.bump_level(["docs: feature 这个词不算"]) == "patch", "feature 不是 feat")
    expect(mod.apply_bump("0.1.0", "patch") == "0.1.1", "patch")
    expect(mod.apply_bump("0.1.0", "minor") == "0.2.0", "minor")
    expect(mod.apply_bump("0.1.4", "major") == "1.0.0", "major")
    expect(mod.apply_bump("8.0.0+1", "patch") == "8.0.1+1", "构建号不自增")


def test_ignore_and_meson_version_line() -> None:
    only_version = """\
diff --git a/practice/cpp/meson.build b/practice/cpp/meson.build
--- a/practice/cpp/meson.build
+++ b/practice/cpp/meson.build
@@ -1,3 +1,3 @@
 project('Athena', 'cpp',
-  version: '10.0.0',
+  version: '10.1.0',
   default_options: ['cpp_std=c++20'])
"""
    also_else = only_version + "+  extra: true,\n"
    expect(mod.version_line_only(only_version), "只有 version 行")
    expect(not mod.version_line_only(also_else), "还有别的行就算改动")
    kept = mod.significant_paths(
        [
            "comms/driver/BOARD.md",
            "docs/RELEASE-TODO.md",
            "scripts/release.py",
            ".github/workflows/ci.yml",
            "practice/cpp/meson.build",
            "programming/snake/src/main.cc",
        ],
        {"practice/cpp/meson.build"},
    )
    expect(kept == ["programming/snake/src/main.cc"], f"忽略项没滤干净：{kept}")


def test_version_line_only_for_other_manifests() -> None:
    nl = chr(10)

    def patch(old: str, new: str) -> str:
        return nl.join(["--- a/x", "+++ b/x", "@@ -1 +1 @@", "-" + old, "+" + new]) + nl

    expect(mod.version_line_only(patch('  "version": "0.1.0",', '  "version": "10.0.0",')), "tauri 版本行")
    expect(mod.version_line_only(patch("version: 8.0.0+1", "version: 10.0.0+1")), "pubspec 版本行")
    expect(mod.version_line_only(patch('  "version": "0.1.0"', '  "version": "1.0.0"')), "package.json 版本行（末尾无逗号）")
    expect(not mod.version_line_only(patch('  "beforeBuildCommand": "npm run build"', '  "beforeBuildCommand": "pnpm run build"')), "别的字段不算")
    expect(not mod.version_line_only(""), "没有增删不算只改版本")
    files = [
        "programming/snake/src-tauri/tauri.conf.json",
        "practice/c-gui-lab/package.json",
        "practice/c-gui-lab/package-lock.json",
        "practice/earth/src-tauri/tauri.conf.json",
    ]
    apps = _apps()
    apps[5]["manifest"] = "practice/c-gui-lab/package.json"
    apps.append({"id": "earth", "root": "practice", "kind": "tauri", "manifest": "practice/earth/src-tauri/tauri.conf.json", "manifest_format": "tauri_conf"})
    apps[0]["manifest"] = "programming/snake/src-tauri/tauri.conf.json"

    def patch_of(path: str) -> str:
        if path.endswith("earth/src-tauri/tauri.conf.json"):
            return patch('  "beforeBuildCommand": "npm run build"', '  "beforeBuildCommand": "pnpm run build"')
        return patch('  "version": "0.1.0"', '  "version": "1.0.0"')

    only = mod.version_only_manifests(apps, files, patch_of)
    expect(only == {files[0], files[1], files[2]}, f"版本行豁免范围不对：{only}")
    expect(mod.significant_paths(files, only) == [files[3]], "只剩 earth 真有改动")


def test_legacy_base_and_new_apps() -> None:
    released = {"id": "snake", "first_release": "10.0.0"}
    fresh = {"id": "pocket-cube-solver"}
    no_manifest = lambda app: "0.1.0"  # noqa: E731 - legacy tag 上清单是占位，不该被读
    expect(mod.base_version(released, "v10.0.0", no_manifest) == "10.0.0", "legacy tag 取 tag 版本")
    old_app = {"id": "ascent", "first_release": "8.0.0"}
    expect(mod.base_version(old_app, "v9.0.0", no_manifest) == "9.0.0", "更早的 legacy tag 同理")
    expect(mod.base_version(fresh, "v10.0.0", no_manifest) is None, "未发布的应用在 legacy tag 上视为新应用")
    late = {"id": "x", "first_release": "10.0.0"}
    expect(mod.base_version(late, "v9.0.0", no_manifest) is None, "first_release 晚于 tag 也是新应用")
    expect(mod.base_version(released, "v10.1.0", lambda app: "10.1.0") == "10.1.0", "非 legacy tag 读清单")
    expect(mod.base_version(released, "abc1234", lambda app: "10.0.5") == "10.0.5", "非 tag 的 ref 读清单")

    apps = [
        {"id": "snake", "root": "programming", "kind": "tauri", "manifest": "m", "manifest_format": "tauri_conf", "first_release": "10.0.0"},
        {"id": "pocket-cube-solver", "root": "programming", "kind": "tauri", "manifest": "m", "manifest_format": "tauri_conf"},
        {"id": "jiuzhou", "root": "mentor", "kind": "tauri", "manifest": "m", "manifest_format": "tauri_conf", "first_release": "10.0.0"},
    ]
    versions = {"snake": "10.0.0", "pocket-cube-solver": "1.0.0", "jiuzhou": "10.0.0"}
    base_of = lambda app: mod.base_version(app, "v10.0.0", no_manifest)  # noqa: E731
    decisions = mod.decide(
        apps, ["programming/snake/a.json", "programming/pocket-cube-solver/b.json"], {}, {}, False,
        lambda app: versions[app["id"]], lambda _paths: ["feat: 新章"], base_of,
    )
    by_id = {item["id"]: item for item in decisions}
    expect(by_id["snake"]["changed"] and by_id["snake"]["suggested"] == "10.1.0", by_id["snake"])
    expect(by_id["pocket-cube-solver"]["changed"] and by_id["pocket-cube-solver"]["new"], by_id["pocket-cube-solver"])
    expect(by_id["pocket-cube-solver"]["suggested"] == "1.0.0" and by_id["pocket-cube-solver"]["bump"] == "none", "新应用不升版本")
    expect(not by_id["jiuzhou"]["changed"], "没动的应用不进计划")

    versions["snake"] = "10.1.0"
    again = mod.decide(
        apps, ["programming/snake/a.json"], {}, {}, False,
        lambda app: versions[app["id"]], lambda _paths: ["feat: 新章"], base_of,
    )
    snake = {item["id"]: item for item in again}["snake"]
    expect(snake["changed"] and snake["suggested"] == "10.1.0" and snake["bump"] == "none", f"已升过不再升：{snake}")

    base = {app["id"]: mod.base_version(app, "v10.0.0", no_manifest) for app in apps}
    head = {"snake": "10.0.0", "pocket-cube-solver": "1.0.0", "jiuzhou": "10.0.0"}
    payload = mod.matrix_from_versions(apps, base, head)
    names = {item["app"] for item in payload["tauri"]["include"]}
    expect(names == {"pocket-cube-solver"}, f"legacy 基线下只有新应用进矩阵：{names}")
    head["snake"] = "10.1.0"
    names = {item["app"] for item in mod.matrix_from_versions(apps, base, head)["tauri"]["include"]}
    expect(names == {"pocket-cube-solver", "snake"}, f"版本升了的才进：{names}")
    # driver 的 +构建号单独变化不算版本变化
    expect(mod.core_version("10.0.0+1") == mod.core_version("10.0.0+2") == "10.0.0", "构建号不参与比较")


def test_notes_tables() -> None:
    apps = [
        {"id": "snake", "first_release": "10.0.0"},
        {"id": "gtkmm", "first_release": "10.0.0"},
        {"id": "polaris", "first_release": "10.0.0"},
        {"id": "pocket-cube-solver"},
    ]
    # 当前 base 是 v10.1.0：snake 在 10.1.0 升到 10.0.1；polaris 一直是 10.0.0；gtkmm 本次升到 10.0.2
    history = {
        ("snake", "v10.0.0"): "10.0.0", ("snake", "v10.1.0"): "10.0.1",
        ("gtkmm", "v10.0.0"): "10.0.0", ("gtkmm", "v10.1.0"): "10.0.1",
        ("polaris", "v10.0.0"): "10.0.0", ("polaris", "v10.1.0"): "10.0.0",
    }
    base_now = {"snake": "10.0.1", "gtkmm": "10.0.1", "polaris": "10.0.0", "pocket-cube-solver": "1.0.0"}
    head_now = {"snake": "10.0.1", "gtkmm": "10.0.2", "polaris": "10.0.0", "pocket-cube-solver": "1.0.0"}
    text = mod.build_notes(
        apps,
        ["v10.0.0", "v10.1.0"],
        lambda app: base_now.get(app["id"]) if app["id"] != "pocket-cube-solver" else None,
        lambda app: head_now[app["id"]],
        lambda app, tag: history.get((app["id"], tag)),
    )
    expect("| gtkmm | 10.0.1 → 10.0.2 |" in text, text)
    expect("| pocket-cube-solver | 首发 1.0.0 |" in text, text)
    expect("| snake | 10.0.1 | v10.1.0 |" in text, f"最新安装包应是当前版本最早出现的 tag：{text}")
    expect("| polaris | 10.0.0 | v10.0.0 |" in text, text)
    expect("gtkmm | 10.0.1" not in text.split("### 未变化的应用")[1], "本次发布的应用不进未变化表")


def test_toolchain_pins_compare_values_not_counts() -> None:
    base = "node-version: 22\nnode-version: \"22\"\n- uses: pnpm/action-setup@v4\n  version: 10.15.1\n"
    head = base + "node-version: \"22\"\n"
    expect(not mod.toolchain_changed(base, head), "多抄一次相同的 22 不是版本变化")
    expect(mod.toolchain_changed(base, base.replace("10.15.1", "10.16.0")), "pnpm 版本变了")
    expect(mod.toolchain_changed(base, base.replace("node-version: 22", "node-version: 24", 1)), "node 变了")
    with_cli = base + "- run: pnpm dlx @tauri-apps/cli@2.12.0\n"
    expect(mod.toolchain_changed(base, with_cli), "新锁定了 Tauri CLI")
    expect(not mod.toolchain_changed(base, base + "needs: [tauri-apps, c-gui-lab]\n"), "改别的行不算")


def _apps() -> list[dict]:
    return [
        {"id": "snake", "root": "programming", "kind": "tauri", "manifest": "m", "manifest_format": "tauri_conf"},
        {"id": "jiuzhou", "root": "mentor", "kind": "tauri", "manifest": "m", "manifest_format": "tauri_conf"},
        {"id": "ascent", "root": "postgraduate", "kind": "ascent", "manifest": "m", "manifest_format": "tauri_conf"},
        {"id": "cpp", "root": "practice", "kind": "cpp", "manifest": "m", "manifest_format": "meson"},
        {"id": "driver", "root": "certification", "kind": "driver", "manifest": "m", "manifest_format": "pubspec"},
        {"id": "c-gui-lab", "root": "practice", "kind": "electron", "manifest": "m", "manifest_format": "package_json"},
    ]


def test_dependency_and_toolchain_selection() -> None:
    apps = _apps()
    pnpm = {
        "mentor/jiuzhou": ["packages/maps"],
        "packages/maps": [],
        "programming/snake": [],
    }
    cargo = {
        "programming/snake/src-tauri": ["packages/athena-course-shell"],
        "packages/athena-course-shell": [],
    }
    files = ["packages/maps/geo/x.json", "packages/athena-course-shell/src/lib.rs"]
    versions = {app["id"]: "0.1.0" for app in apps}
    versions["driver"] = "10.0.0+1"

    def subjects(paths: list[str]) -> list[str]:
        if any(path.startswith("packages/maps") for path in paths):
            return ["feat(maps): 补岸线"]
        return ["fix(shell): 修正"]

    decisions = mod.decide(apps, files, pnpm, cargo, False, lambda app: versions[app["id"]], subjects)
    by_id = {item["id"]: item for item in decisions}
    expect(by_id["jiuzhou"]["changed"] and by_id["jiuzhou"]["bump"] == "minor", by_id["jiuzhou"])
    expect(by_id["jiuzhou"]["suggested"] == "0.2.0", by_id["jiuzhou"])
    expect(by_id["snake"]["changed"] and by_id["snake"]["bump"] == "patch", by_id["snake"])
    expect(by_id["snake"]["suggested"] == "0.1.1", by_id["snake"])
    expect(not by_id["cpp"]["changed"] and not by_id["driver"]["changed"], "非工作区不能被 Rust/pnpm 带上")
    expect(not by_id["ascent"]["changed"], "工具链没变时 ascent 不该被带上")

    pinned = mod.decide(apps, [], pnpm, cargo, True, lambda app: versions[app["id"]], lambda _paths: ["fix: 升 node"])
    pinned_by = {item["id"]: item for item in pinned}
    expect(pinned_by["snake"]["changed"] and pinned_by["ascent"]["changed"], "工具链覆盖 Tauri 与 ascent")
    expect(not pinned_by["c-gui-lab"]["changed"] and not pinned_by["cpp"]["changed"], "工具链不覆盖 electron/cpp")
    expect(pinned_by["driver"]["suggested"] == "10.0.0+1", "没改动的驾考版本不动")


def test_matrix_shape() -> None:
    apps = _apps()
    base = {app["id"]: "0.1.0" for app in apps}
    head = dict(base)
    head["snake"] = "0.2.0"
    head["ascent"] = "1.0.0"
    payload = mod.matrix_from_versions(apps, base, head)
    expect(payload["cpp"] is False and payload["driver"] is False and payload["c-gui-lab"] is False, payload)
    expect(payload["ascent"] is True, payload)
    include = payload["tauri"]["include"]
    expect(len(include) == 4, include)
    expect([item["platform"] for item in include] == [
        "windows-x64", "macos-arm64", "macos-x86_64", "linux-x86_64"
    ], include)
    expect(all(item["app"] == "snake" and item["root"] == "programming" for item in include), include)
    expect(include[0]["bundles"] == "nsis" and include[3]["bundles"] == "deb", include)
    fresh = dict(base)
    fresh_head = dict(base)
    fresh_head["c-gui-lab"] = "0.1.0"
    del fresh["c-gui-lab"]
    created = mod.matrix_from_versions(apps, fresh, fresh_head)
    expect(created["c-gui-lab"] is True and created["tauri"]["include"] == [], created)
    same = mod.matrix_from_versions(apps, base, dict(base))
    expect(same["tauri"]["include"] == [] and same["ascent"] is False, same)


def test_catalog_covers_release_matrix() -> None:
    apps = mod.load_apps()
    tauri = [app["id"] for app in apps if app["kind"] == "tauri"]
    expect(len(tauri) == 22, f"tauri 应是 22 个：{tauri}")
    ids = {app["id"] for app in apps}
    expect(ids >= {"ascent", "driver", "cpp", "c-gui-lab"}, ids)
    for app in apps:
        expect(app["manifest"].startswith(f"{app['root']}/{app['id']}/"), app)


def test_matrix_on_temp_repo() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        app_dir = repo / "programming" / "snake" / "src-tauri"
        app_dir.mkdir(parents=True)
        manifest = app_dir / "tauri.conf.json"
        manifest.write_text('{"version": "0.1.0"}\n', encoding="utf-8")
        apps_file = repo / "apps.json"
        apps_file.write_text(
            json.dumps(
                [
                    {
                        "id": "snake",
                        "root": "programming",
                        "kind": "tauri",
                        "manifest": "programming/snake/src-tauri/tauri.conf.json",
                        "manifest_format": "tauri_conf",
                    }
                ]
            ),
            encoding="utf-8",
        )

        def git(*args: str) -> None:
            completed = subprocess.run(
                ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", *args],
                cwd=repo,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise SystemExit(completed.stderr.decode("utf-8", "replace"))

        git("init", "-q")
        git("add", "programming/snake/src-tauri/tauri.conf.json")
        git("commit", "-q", "-m", "init")
        git("tag", "v0.0.1")
        manifest.write_text('{"version": "0.2.0"}\n', encoding="utf-8")
        git("add", "programming/snake/src-tauri/tauri.conf.json")
        git("commit", "-q", "-m", "feat: bump")
        apps = mod.load_apps(apps_file)
        text = mod.run_matrix(repo, apps, "v0.0.1", "HEAD")
        payload = json.loads(text)
        expect(len(payload["tauri"]["include"]) == 4, text)
        expect(payload["tauri"]["include"][0]["app"] == "snake", text)


def main() -> int:
    mod.force_utf8_output()
    test_version_roundtrip_preserves_bytes()
    test_bump_level_and_apply()
    test_ignore_and_meson_version_line()
    test_version_line_only_for_other_manifests()
    test_legacy_base_and_new_apps()
    test_notes_tables()
    test_toolchain_pins_compare_values_not_counts()
    test_dependency_and_toolchain_selection()
    test_matrix_shape()
    test_catalog_covers_release_matrix()
    test_matrix_on_temp_repo()
    print("ok — release_plan 自测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
