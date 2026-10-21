#!/usr/bin/env python3
"""release_updater 自测。不引测试框架，造一个临时 dist 目录。"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_updater", ROOT / "release_updater.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

NOW = datetime(2026, 10, 21, 8, 30, 0, tzinfo=timezone.utc)


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def touch(dist: Path, name: str, text: str = "x") -> None:
    (dist / name).write_text(text, encoding="utf-8")


def test_full_set_for_one_app() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp) / "dist"
        out = Path(tmp) / "out"
        dist.mkdir()
        touch(dist, "athena-snake-10.0.1-windows-x64-setup.exe")
        touch(dist, "athena-snake-10.0.1-windows-x64-setup.exe.sig", "SIGWIN\n")
        for arch in ("arm64", "x86_64"):
            touch(dist, f"athena-snake-10.0.1-macos-{arch}.app.tar.gz")
            touch(dist, f"athena-snake-10.0.1-macos-{arch}.app.tar.gz.sig", f"SIG{arch}")
        touch(dist, "athena-snake-10.0.1-macos-arm64.dmg")  # dmg 不是更新工件
        touch(dist, "athena-snake_10.0.1_amd64.deb")
        written = mod.write_channels(dist, "v10.1.0", out, "iguoya/Athena", "说明", NOW)
        expect([p.name for p in written] == ["snake.json"], written)
        data = json.loads((out / "snake.json").read_text(encoding="utf-8"))
        expect(data["version"] == "10.0.1" and data["notes"] == "说明", data)
        expect(data["pub_date"] == "2026-10-21T08:30:00Z", data["pub_date"])
        expect(set(data["platforms"]) == {"windows-x86_64", "darwin-aarch64", "darwin-x86_64"}, data["platforms"])
        win = data["platforms"]["windows-x86_64"]
        expect(win["signature"] == "SIGWIN", "签名去首尾空白、内容原样")
        expect(
            win["url"] == "https://github.com/iguoya/Athena/releases/download/v10.1.0/athena-snake-10.0.1-windows-x64-setup.exe",
            win["url"],
        )
        expect(data["platforms"]["darwin-aarch64"]["url"].endswith("athena-snake-10.0.1-macos-arm64.app.tar.gz"), data)
        expect("linux-x86_64" not in data["platforms"], "Linux 不写条目")


def test_hyphenated_ids_and_several_apps() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp) / "dist"
        out = Path(tmp) / "out"
        dist.mkdir()
        touch(dist, "athena-selinger-linear-algebra-10.0.2-windows-x64-setup.exe.sig", "A")
        touch(dist, "athena-selinger-linear-algebra-10.0.2-windows-x64-setup.exe")
        touch(dist, "athena-pocket-cube-solver-10.1.0-windows-x64-setup.exe.sig", "B")
        touch(dist, "athena-pocket-cube-solver-10.1.0-windows-x64-setup.exe")
        written = mod.write_channels(dist, "v10.1.0", out, "o/r", "", NOW)
        expect(sorted(p.name for p in written) == ["pocket-cube-solver.json", "selinger-linear-algebra.json"], written)
        data = json.loads((out / "selinger-linear-algebra.json").read_text(encoding="utf-8"))
        expect(data["version"] == "10.0.2" and list(data["platforms"]) == ["windows-x86_64"], data)


def test_no_signatures_is_a_quiet_noop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp) / "dist"
        dist.mkdir()
        touch(dist, "athena-snake-10.0.1-windows-x64-setup.exe")
        touch(dist, "athena-snake_10.0.1_amd64.deb")
        out = Path(tmp) / "out"
        expect(mod.write_channels(dist, "v1.0.0", out, "o/r", "", NOW) == [], "没有 .sig 不生成")
        expect(list(out.glob("*.json")) == [], "输出目录里不该有 json")


def test_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp) / "dist"
        dist.mkdir()
        touch(dist, "athena-snake-10.0.1-windows-x64-setup.exe.sig", "A")
        touch(dist, "athena-snake-10.0.2-macos-arm64.app.tar.gz.sig", "B")
        try:
            mod.write_channels(dist, "v1.0.0", Path(tmp) / "o", "o/r", "", NOW)
        except SystemExit as exc:
            expect("版本不一致" in str(exc), str(exc))
        else:
            raise SystemExit("同一应用版本不一致应报错")
        empty = Path(tmp) / "dist2"
        empty.mkdir()
        touch(empty, "athena-snake-10.0.1-windows-x64-setup.exe.sig", "  \n")
        try:
            mod.write_channels(empty, "v1.0.0", Path(tmp) / "o2", "o/r", "", NOW)
        except SystemExit as exc:
            expect("空的" in str(exc), str(exc))
        else:
            raise SystemExit("空签名应报错")


def test_cli_notes_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp) / "dist"
        dist.mkdir()
        touch(dist, "athena-snake-10.0.1-windows-x64-setup.exe.sig", "A")
        touch(dist, "athena-snake-10.0.1-windows-x64-setup.exe")
        notes = Path(tmp) / "n.md"
        notes.write_text("## 本次\n- 更新\n", encoding="utf-8")
        out = Path(tmp) / "out"
        code = mod.main(["channels", "--dist", str(dist), "--tag", "v10.1.0", "--out", str(out), "--repo", "o/r", "--notes-file", str(notes)])
        expect(code == 0, code)
        data = json.loads((out / "snake.json").read_text(encoding="utf-8"))
        expect(data["notes"] == "## 本次\n- 更新", data["notes"])


def main() -> int:
    mod.force_utf8_output()
    test_full_set_for_one_app()
    test_hyphenated_ids_and_several_apps()
    test_no_signatures_is_a_quiet_noop()
    test_errors()
    test_cli_notes_file()
    print("ok — release_updater 自测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
