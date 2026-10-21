#!/usr/bin/env python3
"""T-103：tauri-plugin-updater / tauri-plugin-process 批量接入（ADR 0172）。

幂等：重复运行只补缺失的部分。三类应用：
- react：自带 Builder，六处全接（conf / capabilities / Cargo / lib.rs / package.json / main.tsx）
- shell：Rust 壳在 packages/athena-course-shell，应用侧不注册插件（壳统一注册），
  只接 conf / capabilities / package.json / main.ts(mountAppUpdate)
- math-tools 例外：Builder 在 main.rs（脚本按 rs 文件探测，不按类别）

用法：python attach_updater.py <root/id> ...   # 不带参数则处理内置全部名单
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4] if __file__[:2].upper() != "C:" else Path(r"C:\Users\tiger\Athena")
PUBKEY = "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IEI3NUQ0NjZDQzRFRDE0QTcKUldTbkZPM0ViRVpkdDNDcHdhZHdTS0N6dTZ2REp5Q2NjcTN6UzE4dzRqL3FLWHlOeFVjODFjNXgK"

TARGETS = [
    # (root, id, kind)  kind: react | shell
    ("postgraduate", "algorithms", "shell"),
    ("programming", "c-plus-plus", "react"),
    ("programming", "chinese-chess", "react"),
    ("tools", "comms-console", "react"),
    ("mentor", "competitions", "react"),
    ("postgraduate", "cs408", "shell"),
    ("postgraduate", "data-structures", "shell"),
    ("programming", "design-patterns", "shell"),
    ("practice", "earth", "react"),
    ("certification", "embedded", "react"),
    ("guide", "gtkmm", "react"),
    ("mentor", "jiuzhou", "react"),
    ("tools", "math-tools", "react"),  # Builder 在 main.rs，脚本按文件探测
    ("postgraduate", "mathematics", "shell"),  # Rust 自建 Builder（已接），前端 vanilla main.ts
    ("guide", "octave-manual", "react"),
    ("programming", "pocket-cube-solver", "react"),
    ("mentor", "polaris", "react"),
    ("guide", "selinger-linear-algebra", "react"),
    ("guide", "siefken-linear-algebra", "react"),
    ("certification", "software", "react"),
    ("guide", "sympy-tutorial", "react"),
]

results: list[str] = []


def note(msg: str) -> None:
    results.append(msg)
    print(msg)


def patch_conf(sr: Path, app_id: str) -> None:
    p = sr / "tauri.conf.json"
    c = json.loads(p.read_text(encoding="utf-8"))
    changed = []
    bundle = c.setdefault("bundle", {})
    if not bundle.get("createUpdaterArtifacts"):
        bundle["createUpdaterArtifacts"] = True
        changed.append("bundle.createUpdaterArtifacts")
    plugins = c.setdefault("plugins", {})
    if "updater" not in plugins:
        plugins["updater"] = {
            "pubkey": PUBKEY,
            "endpoints": [
                f"https://github.com/iguoya/Athena/releases/download/app-updates/{app_id}.json"
            ],
            "windows": {"installMode": "passive"},
        }
        changed.append("plugins.updater")
    if changed:
        p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    note(f"  conf: {', '.join(changed) if changed else '已接入，跳过'}")


def patch_capabilities(sr: Path) -> None:
    cdir = sr / "capabilities"
    cdir.mkdir(exist_ok=True)
    p = cdir / "default.json"
    want = ["updater:default", "process:allow-restart"]
    if p.exists():
        c = json.loads(p.read_text(encoding="utf-8"))
        perms = c.setdefault("permissions", [])
        missing = [x for x in want if x not in perms]
        if missing:
            perms.extend(missing)
            p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            note(f"  capabilities: 追加 {missing}")
        else:
            note("  capabilities: 已接入，跳过")
    else:
        c = {
            "$schema": "../gen/schemas/desktop-schema.json",
            "identifier": "default",
            "description": "应用默认能力",
            "windows": ["main"],
            "permissions": ["core:default"] + want,
        }
        p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        note("  capabilities: 新建 default.json")


def patch_cargo(sr: Path, register_in_app: bool) -> None:
    p = sr / "Cargo.toml"
    t = p.read_text(encoding="utf-8")
    if "tauri-plugin-updater" in t:
        note("  Cargo: 已接入，跳过")
        return
    # 壳应用也必须声明依赖：tauri-build 从应用自身依赖发现插件权限文件，
    # capabilities 里的 updater:default 才能解析（注册仍在壳里，避免重复）。
    m = re.search(r"^tauri = \{.*\}\s*$", t, re.M)
    assert m, f"{p}: 找不到 tauri 依赖行"
    ins = "tauri-plugin-updater = { workspace = true }\ntauri-plugin-process = { workspace = true }"
    t = t[: m.end()] + "\n" + ins + t[m.end():]
    p.write_text(t, encoding="utf-8", newline="")
    note("  Cargo: 加两个 workspace 插件依赖" + ("（注册仍在壳）" if not register_in_app else ""))


def patch_rust(sr: Path, register_in_app: bool) -> None:
    if not register_in_app:
        note("  Rust: 壳应用不注册，跳过")
        return
    for name in ("lib.rs", "main.rs"):
        p = sr / "src" / name
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        if "tauri_plugin_updater" in t:
            note(f"  Rust {name}: 已接入，跳过")
            return
        m = re.search(r"^(\s*)tauri::Builder::default\(\)\s*$", t, re.M)
        if m:
            ins = f"{m.group(1)}.plugin(tauri_plugin_updater::Builder::new().build())\n{m.group(1)}.plugin(tauri_plugin_process::init())"
            t = t[: m.end()] + "\n" + ins + t[m.end():]
            p.write_text(t, encoding="utf-8", newline="")
            note(f"  Rust {name}: Builder 后注册两插件")
            return
    raise AssertionError(f"{sr}: 没找到可插入的 tauri::Builder::default()")


def insert_dict_keys(d: dict, additions: dict) -> dict:
    """把 additions 按字母序插回 d（保序 dict，diff 最小）。"""
    out = {}
    merged = {**d, **additions}
    for k in sorted(merged, key=str.lower):
        out[k] = merged[k]
    return out


def patch_package_json(app: Path) -> None:
    p = app / "package.json"
    c = json.loads(p.read_text(encoding="utf-8"))
    deps = c.setdefault("dependencies", {})
    want = {
        "@athena/app-update": "workspace:",
        "@tauri-apps/plugin-process": "catalog:",
        "@tauri-apps/plugin-updater": "catalog:",
    }
    missing = {k: v for k, v in want.items() if deps.get(k) != v}
    if not missing:
        note("  package.json: 已接入，跳过")
        return
    c["dependencies"] = insert_dict_keys(deps, missing)
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    note(f"  package.json: 加 {sorted(missing)}")


def patch_frontend(app: Path, kind: str) -> None:
    if kind == "shell":
        for name in ("main.ts", "main.tsx"):
            p = app / "src" / name
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8")
            if "mountAppUpdate" in t:
                note(f"  前端 {name}: 已接入，跳过")
                return
            # import 放在最前（ESM import 必须顶层；放文件头即可）
            imp = 'import { mountAppUpdate } from "@athena/app-update";\n'
            lines = t.splitlines(keepends=True)
            body = "".join(lines)
            t2 = imp + body
            t2 = t2.rstrip("\n") + '\n\nif (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {\n  mountAppUpdate();\n}\n'
            p.write_text(t2, encoding="utf-8", newline="")
            note(f"  前端 {name}: import + mountAppUpdate()")
            return
        raise AssertionError(f"{app}: 没找到 main.ts/tsx")
    # react
    p = app / "src" / "main.tsx"
    t = p.read_text(encoding="utf-8")
    if "AppUpdate" in t:
        note("  前端 main.tsx: 已接入，跳过")
        return
    # react：import 插到第一个 import 行之后；组件插到 <App …/> 行之后
    # （App 可能是默认导入、命名导入或 lazy()，不依赖 import App 行存在）
    lines = t.splitlines(keepends=True)
    first_import = next(i for i, ln in enumerate(lines) if ln.startswith("import "))
    lines.insert(first_import, 'import { AppUpdate } from "@athena/app-update";\n')
    t = "".join(lines)
    m2 = re.search(r"^(\s*)<App\b[^\n]*?/>\s*$", t, re.M)
    assert m2, f"{p}: 找不到 <App …/> 行"
    t = t[: m2.start()] + f"{m2.group(1)}<App />\n{m2.group(1)}<AppUpdate />" + t[m2.end():]
    p.write_text(t, encoding="utf-8", newline="")
    note("  前端 main.tsx: import + <AppUpdate />")


def main() -> None:
    only = set(sys.argv[1:])
    for root, app_id, kind in TARGETS:
        if only and app_id not in only:
            continue
        app = REPO / root / app_id
        sr = app / "src-tauri"
        note(f"== {root}/{app_id} ({kind})")
        patch_conf(sr, app_id)
        patch_capabilities(sr)
        patch_cargo(sr, register_in_app=kind == "react")
        patch_rust(sr, register_in_app=kind == "react")
        patch_package_json(app)
        patch_frontend(app, kind)


if __name__ == "__main__":
    main()
