#!/usr/bin/env python3
"""gtkmm 学习应用的验证入口：内容结构、清单闭环、出处契约、（存在才跑）构建检查。

结构校验的内容约定：
- 知识点评级域：difficulty 0–5（0 未评），mastery_goal ∈ master/required/familiar/空
  （主仓库 ADR 0029）；
- requires 依赖方向校验（主仓库 ADR 0030）；
- 有限块类型承载讲解（主仓库 ADR 0058），块类型白名单见 BLOCK_TYPES；
- Web 模拟与真机演示强制配对（应用 ADR 0001 决策 3）；
- 判分题必须带出处（主仓库 ADR 0043，content-contract.json blocking=true）。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash
或 WSL（主仓库 ADR 0047）。

用法：
    python3 scripts/check.py               # 全部检查（构建部分存在才跑）
    python3 scripts/check.py --skip-rust   # 跳过 cargo check
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"

# 有限块类型（应用 ADR 0001 决策 3、6；主仓库 ADR 0056、0058）
BLOCK_TYPES = {
    "text",
    "code",
    "callout",
    "simulation",        # Web 交互模拟；必须带 demo_ref（强制配对）
    "demo",              # 真机演示卡；必须带 demo_ref
    "experiment",        # 骨架实验卡（exp.*）；必须带 demo_ref
    "observation_quiz",  # 演示观察题；必须带 demo_ref，判分内容须有出处
    "quiz",              # 随堂选择题；判分内容须有出处
}
KNOWLEDGE_TYPES = {"concept", "skill", "strategy"}      # 主仓库 ADR 0031
MASTERY_GOALS = {"master", "required", "familiar", ""}  # 主仓库 ADR 0029
SECTION_STATUSES = {"pending", "translated"}

ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"{path.relative_to(PROJECT_ROOT)}: {error}")
        return None


def check_json_all() -> None:
    files = sorted(CONTENT_DIR.rglob("*.json"))
    if not files:
        fail("content/ 下没有任何 JSON，内容目录是不是错了？")
        return
    for path in files:
        load_json(path)
    print(f"{len(files)} 个 JSON 文件解析通过")


def check_quiz_item(item: dict, where: str) -> None:
    """判分题的通用结构：题干、选项、答案界内、出处（ADR 0043）。"""
    stem = item.get("stem")
    if not isinstance(stem, str) or not stem.strip():
        fail(f"{where}: 判分题缺 stem（题干）")
    options = item.get("options")
    if not isinstance(options, list) or len(options) < 2:
        fail(f"{where}: options 至少两个选项（{stem!r}）")
    elif not isinstance(item.get("answer"), int) or not 0 <= item["answer"] < len(options):
        fail(f"{where}: answer 不是合法下标（{stem!r}）")
    source_refs = item.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        fail(f"{where}: 判分题缺 source_refs——新题当场标出处（ADR 0043；{stem!r}）")


def check_knowledge_point(kp: dict, where: str, kp_ids: set[str]) -> None:
    kp_id = kp.get("id", "")
    if not kp_id.startswith("gtkmm."):
        fail(f"{where}: 知识点 id 必须用 gtkmm. 前缀（{kp_id!r}）")
    if kp.get("type") not in KNOWLEDGE_TYPES:
        fail(f"{where}: type 必须是 concept/skill/strategy（{kp_id}）")
    difficulty = kp.get("difficulty")
    if not isinstance(difficulty, int) or not 0 <= difficulty <= 5:
        fail(f"{where}: difficulty 是 0–5 的整数（{kp_id}）")
    if kp.get("mastery_goal", "") not in MASTERY_GOALS:
        fail(f"{where}: mastery_goal ∈ master/required/familiar/空（{kp_id}）")
    for ref in kp.get("requires", []):
        if ref not in kp_ids:
            fail(f"{where}: requires 指向不存在的知识点 {ref!r}（{kp_id}；ADR 0030）")
    for block in kp.get("blocks", []):
        check_block(block, f"{where}/{kp_id}")


def check_block(block: dict, where: str) -> None:
    block_type = block.get("type")
    if block_type not in BLOCK_TYPES:
        fail(f"{where}: 未知块类型 {block_type!r}（白名单：{sorted(BLOCK_TYPES)}）")
        return
    if block_type in ("simulation", "demo", "experiment", "observation_quiz"):
        demo_ref = block.get("demo_ref")
        if not isinstance(demo_ref, str) or not demo_ref:
            fail(f"{where}: {block_type} 块必须带 demo_ref（强制配对，ADR 0001 决策 3）")
    if block_type in ("quiz", "observation_quiz"):
        check_quiz_item(block, where)


def collect_demo_refs(course: dict) -> set[str]:
    """课表里所有被引用的演示/实验 id（demo 卡与观察题都指向实体）。"""
    refs: set[str] = set()

    def walk(blocks) -> None:
        for block in blocks or []:
            if block.get("type") in ("simulation", "demo", "experiment", "observation_quiz"):
                if block.get("demo_ref"):
                    refs.add(block["demo_ref"])

    for section in course.get("sections", []) + course.get("reference", []):
        for kp in section.get("knowledge_points", []):
            walk(kp.get("blocks"))
    return refs


def check_curriculum(course: dict) -> tuple[set[str], set[str]]:
    if not course:
        return set(), set()
    seen_ids: set[str] = set()
    kp_ids: set[str] = set()
    entities: list[tuple[str, list]] = [
        ("sections", course.get("sections", [])),
        ("reference", course.get("reference", [])),
    ]
    for key, sections in entities:
        is_main = key == "sections"  # 参考层条目（如 GFDL 原文照录）的呈现形态不同，不查对照稿
        for section in sections:
            where = f"curriculum.json {key}[]"
            section_id = section.get("id", "")
            if not section_id:
                fail(f"{where}: 缺 id")
            elif section_id in seen_ids:
                fail(f"{where}: id 重复 {section_id!r}")
            seen_ids.add(section_id)
            if section.get("status") not in SECTION_STATUSES:
                fail(f"{where}: status ∈ pending/translated（{section_id}）")
            if is_main and section.get("status") == "translated":
                # 已译的主线章节必须有逐段对照翻译稿（应用 ADR 0002 决策 1）
                if not (CONTENT_DIR / "chapters" / f"{section_id}.md").is_file():
                    fail(f"{where}: status=translated 但缺 content/chapters/{section_id}.md")
            if not section.get("translation_ref"):
                fail(f"{where}: 缺 translation_ref——每个单元都能回溯教程（ADR 0002）")
            for kp in section.get("knowledge_points", []):
                kp_id = kp.get("id", "")
                if kp_id in kp_ids:
                    fail(f"{where}: 知识点 id 重复 {kp_id!r}")
                kp_ids.add(kp_id)
                check_knowledge_point(kp, where, kp_ids)
            for item in section.get("checkpoint", []):
                check_quiz_item(item, f"{where}/{section_id} checkpoint")
    # 先收集全部知识点 id 再校验 requires（前置可以指向后面的章节）
    for section in course.get("sections", []) + course.get("reference", []):
        for kp in section.get("knowledge_points", []):
            for ref in kp.get("requires", []):
                if ref not in kp_ids:
                    fail(f"curriculum.json: requires 指向不存在的知识点 {ref!r}（{kp.get('id')}）")
    print(
        f"课表校验通过：{len(course.get('sections', []))} 个主线单元、"
        f"{len(course.get('reference', []))} 个参考单元、{len(kp_ids)} 个知识点"
    )
    return kp_ids, collect_demo_refs(course), collect_lab_refs(course)


def collect_lab_refs(course: dict) -> list[str]:
    """实验区（labs）引用的实验实体 id——与教程章节并列的独立入口。"""
    labs = course.get("labs") or {}
    return [exp_id for group in labs.get("groups", [])
            for exp_id in group.get("experiments", [])]


def check_manifest(manifest: dict, kp_ids: set[str], course_refs: set[str],
                   lab_refs: list[str]) -> None:
    if manifest is None:
        return
    entity_ids: set[str] = set()
    entity_refs: set[str] = set()
    for kind, items, prefix in (("demos", manifest.get("demos", []), "demo."),
                                ("experiments", manifest.get("experiments", []), "exp.")):
        required = ("id", "title", "purpose", "theory_refs", "source_dir",
                    "build_target", "translation_ref", "source_refs")
        for entity in items:
            entity_id = entity.get("id", "")
            where = f"demos.json {kind}[] {entity_id or '?'}"
            for field in required:
                if field not in entity:
                    fail(f"{where}: 缺必填字段 {field}")
            if not entity_id.startswith(prefix):
                fail(f"{where}: id 必须用 {prefix} 前缀")
            elif entity_id in entity_ids:
                fail(f"{where}: id 重复")
            entity_ids.add(entity_id)
            for ref in entity.get("theory_refs", []):
                if ref not in kp_ids:
                    fail(f"{where}: theory_refs 指向不存在的知识点 {ref!r}")
                entity_refs.add(ref)
            source_dir = PROJECT_ROOT / entity.get("source_dir", "")
            if entity.get("source_dir") and not source_dir.is_dir():
                fail(f"{where}: source_dir 不存在：{entity.get('source_dir')}")
            if entity.get("source_dir") and not (source_dir / "CMakeLists.txt").is_file():
                fail(f"{where}: source_dir 里没有 CMakeLists.txt（每个演示/实验一个工程）")
    # 闭环：课表引用的实体必须在清单里；清单实体必须被课表引用（孤儿=死代码）
    missing = course_refs - entity_ids
    if missing:
        fail(f"课表引用了清单里不存在的演示/实验：{sorted(missing)}")
    experiment_ids = {e.get("id") for e in manifest.get("experiments", [])}
    lab_missing = [ref for ref in lab_refs if ref not in experiment_ids]
    if lab_missing:
        fail(f"实验区引用了清单里不存在的实验：{sorted(lab_missing)}")
    orphans = {e["id"] for e in manifest.get("demos", []) + manifest.get("experiments", [])
               if e.get("id") not in course_refs and e.get("id") not in set(lab_refs)}
    if orphans:
        fail(f"清单实体没有任何课表块或实验区引用（孤儿条目）：{sorted(orphans)}")
    print(
        f"清单校验通过：{len(manifest.get('demos', []))} 个演示、"
        f"{len(manifest.get('experiments', []))} 个实验，引用闭环成立"
    )


def check_license_pages() -> None:
    """GFDL 义务三件套中的两个文件（ADR 0002）。"""
    for relpath in ("content/license.md", "content/license/gfdl-1.2.md"):
        if not (PROJECT_ROOT / relpath).is_file():
            fail(f"缺 {relpath}——翻译基准的许可义务未落地（ADR 0002）")
    full_text = PROJECT_ROOT / "content/license/gfdl-1.2.md"
    if full_text.is_file():
        head = full_text.read_text(encoding="utf-8", errors="replace")[:200]
        if "GNU Free Documentation License" not in head:
            fail("content/license/gfdl-1.2.md 不像 GFDL 原文，请从 gnu.org 原文照录")


def tool(name: str) -> str:
    """Windows 上 npm 实际是 npm.cmd；which 按 PATHEXT 解析，三平台可用。"""
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请先安装后重试")
    return found


def run(command: list[str], step: str, env: dict[str, str] | None = None) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT, env=env)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


MSYS2_HINT = (
    "Windows 上 gtkmm-4.0 走 MSYS2 MINGW64（主仓库 ADR 0047、0051）：\n"
    "  1. 安装 MSYS2（https://www.msys2.org/，默认装到 C:\\msys64）；\n"
    "  2. 在「MSYS2 MINGW64」终端里运行：\n"
    "     pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-gtkmm-4.0 \\\n"
    "       mingw-w64-x86_64-ninja mingw-w64-x86_64-pkgconf\n"
    "本脚本会自动使用 C:\\msys64\\mingw64，不需要把它加进系统 PATH。"
)


def msys2_mingw64() -> Path | None:
    """gtkmm-4.0 在 Windows 的唯一现实来源是 MSYS2 MINGW64。

    检测到就返回其根目录（用它前置 PATH，隔离系统 PATH 里的其他 pkg-config，
    比如 GNU Octave 自带的那份会撞车）。
    """
    for candidate in (Path("C:/msys64/mingw64"), Path("D:/msys64/mingw64")):
        pkgconf = candidate / "bin" / "pkgconf.exe"
        gtkmm = candidate / "lib" / "pkgconfig" / "gtkmm-4.0.pc"
        if pkgconf.is_file() and gtkmm.is_file():
            return candidate
    return None


def check_native() -> None:
    """演示/实验的 CMake 工程全量编译 + --self-check（有实体才跑）。

    self-check 构造控件树后即退出 0，证明工程可编译、可加载——不弹窗。
    """
    manifest = load_json(CONTENT_DIR / "demos.json") or {}
    entities = manifest.get("demos", []) + manifest.get("experiments", [])
    if not entities:
        return
    cmake = shutil.which("cmake")
    if cmake is None:
        fail("清单里有演示/实验但找不到 cmake——请安装 CMake 4.0+")
        return

    env = os.environ.copy()
    if sys.platform == "win32":
        mingw = msys2_mingw64()
        if mingw is None:
            fail("没有可用的 gtkmm-4.0 工具链。\n" + MSYS2_HINT)
            return
        env["PATH"] = str(mingw / "bin") + os.pathsep + env["PATH"]
        env["PKG_CONFIG_PATH"] = str(mingw / "lib" / "pkgconfig")
    # macOS（Homebrew）/Linux：pkg-config 直接找系统路径，无需特殊 env。

    build_dir = PROJECT_ROOT / "build-native"
    build_dir.mkdir(exist_ok=True)
    run([cmake, "-G", "Ninja", "-S", "demos", "-B", "build-native"],
        "原生侧 CMake configure", env)
    run([cmake, "--build", "build-native"], "原生侧全量编译", env)
    for entity in entities:
        binary = build_dir / entity["id"].replace(".", "-")
        if sys.platform == "win32" and not binary.with_suffix(".exe").is_file():
            fail(f"{entity['id']}: 编译产物缺失（{binary.name}.exe）")
            continue
        run([str(binary), "--self-check"], f"{entity['id']} --self-check", env)


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 gtkmm 学习应用")
    parser.add_argument("--skip-rust", action="store_true", help="跳过 cargo check")
    parser.add_argument("--skip-native", action="store_true", help="跳过演示/实验编译与自检")
    args = parser.parse_args()

    check_json_all()
    course = load_json(CONTENT_DIR / "curriculum.json")
    kp_ids, course_refs, lab_refs = check_curriculum(course or {})
    manifest = load_json(CONTENT_DIR / "demos.json")
    check_manifest(manifest or {}, kp_ids, course_refs, lab_refs)
    check_license_pages()

    contract = PROJECT_ROOT / "content-contract.json"
    if not contract.is_file():
        fail("缺 content-contract.json——出处检查未接入（主仓库 ADR 0043）")

    if ERRORS:
        print("\n内容检查未通过：", flush=True)
        for error in ERRORS:
            print(f"  ✗ {error}")
        return 1
    print("内容与清单检查全部通过")

    if not args.skip_native:
        check_native()
    if not args.skip_rust and (PROJECT_ROOT / "src-tauri" / "Cargo.toml").is_file():
        run([tool("cargo"), "check", "--manifest-path",
             str(PROJECT_ROOT / "src-tauri" / "Cargo.toml")], "Rust 侧类型检查")
    return 0


if __name__ == "__main__":
    sys.exit(main())
