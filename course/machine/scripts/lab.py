#!/usr/bin/env python3
"""多目标实验台的命令行：体检、预生成汇编、编译运行、校验（ADR 0006、0007）。

三个目标：win-x64（Microsoft ABI）、sysv-x64（System V）、aarch64-linux。
观察汇编只需要 clang 的 --target，不需要目标平台能运行；真跑才依赖本机原生环境或 WSL。

用法：
    python3 scripts/lab.py doctor              # 体检：缺什么、怎么装、各目标能否真跑
    python3 scripts/lab.py gen [lab]           # 预生成观察层汇编到 content/asm/<lab>/
    python3 scripts/lab.py run <lab> [--target T | --all]   # 编译并运行汇编骨架；--all 跑全部并比对输出
    python3 scripts/lab.py check               # 校验：骨架能汇编、观察层没过期（check.py 调用）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LABS = PROJECT_ROOT / "labs"
OBSERVED = PROJECT_ROOT / "content" / "asm"
BUILD = PROJECT_ROOT / "build" / "lab"

WSL_DISTRO = "Ubuntu"
# libc6-dev 不是命令，是 gcc 编译带 #include 的 C 驱动所需的头文件包（gcc 本身不带 stdio.h）；
# 探测时用 /usr/include/stdio.h 在不在来判断。
WSL_TOOLS = ["gcc", "libc6-dev", "gdb", "aarch64-linux-gnu-gcc", "qemu-aarch64", "gdb-multiarch"]
WSL_MARK = "WSL_REACHED"
WSL_APT = "sudo apt install gcc libc6-dev gdb gcc-aarch64-linux-gnu qemu-user gdb-multiarch"
LEVELS = ("O0", "O2")

# 观察层的编译选项。去掉展开表、标识串和控制流保护，是为了让输出只剩函数本身（教案要展示的东西）。
# 不 #include 任何头文件的纯函数加 -ffreestanding，才能为任意目标出汇编而不需要它的 sysroot。
OBSERVE_FLAGS = [
    "-S", "-std=c23", "-ffreestanding",
    "-fno-asynchronous-unwind-tables", "-fno-ident", "-fcf-protection=none",
]


@dataclass(frozen=True)
class Target:
    id: str
    triple: str
    arch: str  # x86-64 | aarch64
    syntaxes: tuple[str, ...]  # x86-64 才有两种（ADR 0007）；ARM64 只有一种
    default_syntax: str


TARGETS: dict[str, Target] = {
    "win-x64": Target("win-x64", "x86_64-pc-windows-msvc", "x86-64", ("att", "intel"), "intel"),
    "sysv-x64": Target("sysv-x64", "x86_64-unknown-linux-gnu", "x86-64", ("att", "intel"), "att"),
    "aarch64-linux": Target("aarch64-linux", "aarch64-unknown-linux-gnu", "aarch64", ("native",), "native"),
}


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def clang() -> str:
    found = shutil.which("clang")
    if found is None:
        # ADR 0057：检测不到工具时给具体指引，只写查起来费事的部分。
        raise SystemExit(
            "找不到 clang。Windows：安装 LLVM 并把 bin 加进 PATH（需要它自带的 clang，不是 VS 的 clang-cl）；"
            "macOS：xcode-select --install；Linux：sudo apt install clang"
        )
    return found


def clang_version() -> str:
    out = subprocess.run([clang(), "--version"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()[0].strip()


def host_native_target() -> str | None:
    """本机原生能真跑哪个目标。macOS 的变体（符号前缀等）还没实现，所以不声称（ADR 0006 第 3 条）。"""
    system, machine = platform.system(), platform.machine().lower()
    if system == "Windows" and machine in {"amd64", "x86_64"}:
        return "win-x64"
    if system == "Linux" and machine in {"x86_64", "amd64"}:
        return "sysv-x64"
    if system == "Linux" and machine in {"aarch64", "arm64"}:
        return "aarch64-linux"
    return None


def load_lab(lab_id: str) -> tuple[Path, dict]:
    directory = LABS / lab_id
    manifest = directory / "lab.json"
    if not manifest.is_file():
        raise SystemExit(f"没有这个实验：{lab_id}（找不到 {manifest.relative_to(PROJECT_ROOT)}）")
    return directory, json.loads(manifest.read_text(encoding="utf-8"))


def all_lab_ids() -> list[str]:
    return sorted(p.parent.name for p in LABS.glob("*/lab.json"))


# ---------------------------------------------------------------- 体检

def _decode(data: bytes) -> str:
    """wsl.exe 自己的消息是 UTF-16LE，进到发行版里的命令输出是 UTF-8，两种都要认。"""
    if b"\x00" in data:
        return data.decode("utf-16-le", errors="replace").replace("\x00", "").strip()
    return data.decode("utf-8", errors="replace").strip()


def probe_wsl() -> tuple[bool, str, list[str]]:
    """(能否进入发行版, 说明, 发行版里已有的工具)。"""
    wsl = shutil.which("wsl")
    if wsl is None:
        return False, "没有 wsl.exe。以管理员身份运行：wsl --install Ubuntu", []
    # dash 里 command -v 找不到命令时返回 127，循环的最后一个工具缺失就会让整条脚本以 127 退出，
    # 被误判成「进不了 WSL」。所以用一个标记行确认已经进入，再无条件 exit 0。
    script = "echo " + WSL_MARK + "; for t in " + " ".join(WSL_TOOLS) + "; do command -v $t >/dev/null && echo $t; done; [ -f /usr/include/stdio.h ] && echo libc6-dev; exit 0"
    try:
        done = subprocess.run(
            [wsl, "-d", WSL_DISTRO, "-e", "sh", "-c", script],
            capture_output=True, timeout=90,
        )
    except subprocess.TimeoutExpired:
        return False, "启动 WSL 超时", []
    out, err = _decode(done.stdout), _decode(done.stderr)
    if done.returncode != 0 or WSL_MARK not in out:
        full = err or out or f"退出码 {done.returncode}"
        message = next((line.strip() for line in full.splitlines() if line.strip()), full)
        hint = ""
        # 错误码在第二行（「灾难性故障 / 错误代码: Wsl/Service/E_UNEXPECTED」），所以在全文里找。
        if "E_UNEXPECTED" in full:
            hint = "；管理员 PowerShell 里先试 wsl --update，不行再 wsl --unregister Ubuntu 后 wsl --install Ubuntu"
        elif "WSL_E_DISTRO_NOT_FOUND" in full or "没有" in full:
            hint = f"；安装发行版：wsl --install {WSL_DISTRO}"
        return False, f"进不了 {WSL_DISTRO}：{message}{hint}", []
    found = [line.strip() for line in out.splitlines() if line.strip() and line.strip() != WSL_MARK]
    return True, f"{WSL_DISTRO} 可用", found


def cmd_doctor(_: argparse.Namespace) -> int:
    print("== 工具链 ==")
    print(f"clang   {clang_version()}  {shutil.which('clang')}")
    native = host_native_target()
    wsl_ok, wsl_note, wsl_tools = (False, "", [])
    if platform.system() == "Windows":
        wsl_ok, wsl_note, wsl_tools = probe_wsl()
        print(f"WSL     {wsl_note}")
        if wsl_ok:
            missing = [t for t in WSL_TOOLS if t not in wsl_tools]
            print("        已有：" + (", ".join(wsl_tools) or "（无）"))
            if missing:
                print("        缺：" + ", ".join(missing))
                print(f"        在 {WSL_DISTRO} 里安装：{WSL_APT}")
    print("\n== 目标：观察 / 真跑 ==")
    for target in TARGETS.values():
        if target.id == native:
            run = "真跑（本机原生）"
        elif platform.system() == "Windows" and target.id != "win-x64":
            need = {"sysv-x64": ["gcc", "libc6-dev"], "aarch64-linux": ["aarch64-linux-gnu-gcc", "qemu-aarch64"]}[target.id]
            ready = wsl_ok and all(t in wsl_tools for t in need)
            run = "可经 WSL 真跑" if ready else "需要 WSL 与上面缺的工具，现在不可用"
        else:
            run = "只能观察（本机不原生支持，ADR 0006 第 3 条）"
        print(f"{target.id:<14} 观察 ✓   {run}")
    return 0


# ---------------------------------------------------------------- 观察层

def _source_hash(directory: Path, manifest: dict) -> str:
    return hashlib.sha256((directory / manifest["reference"]["file"]).read_bytes()).hexdigest()


def observe_name(target: Target, syntax: str, level: str) -> str:
    return f"{target.id}.{level}.s" if syntax == "native" else f"{target.id}.{syntax}.{level}.s"


def generate_observation(directory: Path, manifest: dict, out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    source = directory / manifest["reference"]["file"]
    names: list[str] = []
    for target in TARGETS.values():
        for syntax in target.syntaxes:
            for level in LEVELS:
                name = observe_name(target, syntax, level)
                command = [clang(), f"--target={target.triple}", f"-{level}", *OBSERVE_FLAGS]
                if target.arch == "x86-64":
                    command.append(f"-masm={syntax}")
                command += [str(source), "-o", str(out_dir / name)]
                done = subprocess.run(command, capture_output=True, text=True)
                if done.returncode != 0:
                    raise SystemExit(f"{name} 生成失败：\n{done.stderr}")
                names.append(name)
    meta = {
        "lab": manifest["id"],
        "compiler": clang_version(),
        "flags": OBSERVE_FLAGS,
        "levels": list(LEVELS),
        "source": f"labs/{manifest['id']}/{manifest['reference']['file']}",
        "source_sha256": _source_hash(directory, manifest),
        "files": names,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return names


def cmd_gen(args: argparse.Namespace) -> int:
    for lab_id in [args.lab] if args.lab else all_lab_ids():
        directory, manifest = load_lab(lab_id)
        names = generate_observation(directory, manifest, OBSERVED / lab_id)
        print(f"{lab_id}: 生成 {len(names)} 份 → content/asm/{lab_id}/")
    return 0


# ---------------------------------------------------------------- 真跑

@dataclass
class RunResult:
    target: str
    ok: bool
    output: str  # 只含驱动程序自己的输出，不含编译信息
    note: str = ""  # 失败原因


def _wsl_path(windows_path: Path) -> str:
    """Windows 路径 → WSL 里的 /mnt/<盘符>/…。直接算，不为它多起一次 wsl.exe。"""
    resolved = windows_path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    return "/mnt/" + drive + "/" + "/".join(resolved.parts[1:])


def _judge(target_id: str, returncode: int, output: str) -> RunResult:
    if returncode != 0 or "FAIL" in output:
        return RunResult(target_id, False, output, f"退出码 {returncode}")
    return RunResult(target_id, True, output)


def run_native(lab_id: str, directory: Path, manifest: dict, target_id: str) -> RunResult:
    target = TARGETS[target_id]
    out_dir = BUILD / lab_id / target_id
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = out_dir / ("lab.exe" if platform.system() == "Windows" else "lab")
    build = [
        clang(), f"--target={target.triple}", "-std=c23", "-O1", "-Wall",
        str(directory / manifest["driver"]), str(directory / manifest["reference"]["file"]),
        str(directory / manifest["skeletons"][target_id]), "-o", str(exe),
    ]
    done = subprocess.run(build, capture_output=True, text=True)
    if done.stderr.strip():
        print(done.stderr.strip(), file=sys.stderr)
    if done.returncode != 0:
        return RunResult(target_id, False, "", "编译失败")
    ran = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
    return _judge(target_id, ran.returncode, ran.stdout)


def run_via_wsl(lab_id: str, directory: Path, manifest: dict, target_id: str) -> RunResult:
    """sysv-x64 在 WSL 里原生跑；aarch64-linux 交叉编译成静态可执行文件，交给 qemu-user 模拟。

    静态链接是为了不必给 qemu 指定 ARM 的 sysroot（-L）：少一个要配置的东西。产物放在 WSL 自己的
    /tmp 里而不是 /mnt/c，免得经过 9P 文件系统变慢（也避开 Windows 杀软的扫描）。"""
    wsl = shutil.which("wsl")
    if wsl is None:
        raise SystemExit("没有 wsl.exe。以管理员身份运行：wsl --install Ubuntu")
    src = _wsl_path(directory)
    out = f"/tmp/athena-machine-lab/{lab_id}/{target_id}"
    common = f"{shlex.quote(src + '/' + manifest['driver'])} {shlex.quote(src + '/' + manifest['reference']['file'])}"
    skeleton = shlex.quote(src + "/" + manifest["skeletons"][target_id])
    flags = "-std=c23 -O1 -Wall"
    if target_id == "sysv-x64":
        build, run = f"gcc {flags} {common} {skeleton} -o {out}/lab", f"{out}/lab"
    else:
        build = f"aarch64-linux-gnu-gcc {flags} -static {common} {skeleton} -o {out}/lab"
        run = f"qemu-aarch64 {out}/lab"
    # 编译和运行分两次调用：编译信息和驱动输出才不会混在一起，比对三边输出时只比后者。
    compiled = subprocess.run(
        [wsl, "-d", WSL_DISTRO, "-e", "sh", "-c", f"mkdir -p {out} && {build}"],
        capture_output=True, timeout=120,
    )
    if compiled.stderr.strip() or compiled.stdout.strip():
        print(_decode(compiled.stderr or compiled.stdout), file=sys.stderr)
    if compiled.returncode != 0:
        return RunResult(target_id, False, "", "编译失败")
    ran = subprocess.run([wsl, "-d", WSL_DISTRO, "-e", "sh", "-c", run], capture_output=True, timeout=60)
    return _judge(target_id, ran.returncode, _decode(ran.stdout))


WSL_NEEDS = {"sysv-x64": ["gcc", "libc6-dev"], "aarch64-linux": ["aarch64-linux-gnu-gcc", "qemu-aarch64"]}


def availability() -> tuple[list[str], dict[str, str]]:
    """(本机能真跑的目标, 不能的目标 → 原因)。ADR 0006 第 3 条的平台矩阵在这里落成代码。"""
    runnable: list[str] = []
    skipped: dict[str, str] = {}
    native = host_native_target()
    if native:
        runnable.append(native)
    wsl_state: tuple[bool, str, list[str]] | None = None
    for target_id in TARGETS:
        if target_id == native:
            continue
        if platform.system() != "Windows":
            skipped[target_id] = "本机只能观察（ADR 0006 第 3 条）"
            continue
        if wsl_state is None:
            wsl_state = probe_wsl()
        ok, note, tools = wsl_state
        if not ok:
            skipped[target_id] = f"WSL 不可用：{note}"
            continue
        missing = [t for t in WSL_NEEDS[target_id] if t not in tools]
        if missing:
            skipped[target_id] = f"{WSL_DISTRO} 里缺 {', '.join(missing)}。安装：{WSL_APT}"
            continue
        runnable.append(target_id)
    return runnable, skipped


def cmd_run(args: argparse.Namespace) -> int:
    directory, manifest = load_lab(args.lab)
    runnable, skipped = availability()
    if args.all:
        targets = runnable
    else:
        target_id = args.target or host_native_target()
        if target_id is None:
            raise SystemExit("本机没有原生可真跑的目标（ADR 0006 第 3 条）。可以用 gen 看汇编。")
        if target_id not in runnable:
            raise SystemExit(f"{target_id} 现在不能真跑：{skipped.get(target_id, '未知原因')}")
        targets = [target_id]

    results: list[RunResult] = []
    for target_id in targets:
        print(f"== {args.lab} / {target_id} ==", flush=True)
        runner = run_native if target_id == host_native_target() else run_via_wsl
        result = runner(args.lab, directory, manifest, target_id)
        print(result.output.rstrip())
        print(("通过" if result.ok else f"失败：{result.note}") + "\n", flush=True)
        results.append(result)

    failed = [r for r in results if not r.ok]
    if args.all:
        # ADR 0006 第 5 条：三个目标的输出应当一致——这是「同一个 C 语义」最直接的证据。
        outputs = {r.output.strip() for r in results if r.ok}
        print("== 汇总 ==")
        for r in results:
            print(f"{r.target:<14} {'通过' if r.ok else '失败'}")
        for target_id, why in skipped.items():
            print(f"{target_id:<14} 跳过：{why}")
        if len(outputs) > 1:
            print("\n各目标的输出不一致。", file=sys.stderr)
            return 1
        if results and not failed:
            print(f"\n{len(results)} 个目标的输出完全一致。")
    return 1 if failed else 0


# ---------------------------------------------------------------- 校验

def cmd_check(_: argparse.Namespace) -> int:
    """骨架在三个目标都能汇编（不要求能运行，没有 WSL 的机器也能过）；观察层存在且没过期。"""
    problems: list[str] = []
    ids = all_lab_ids()
    if not ids:
        raise SystemExit("labs/ 下没有任何实验。")
    with tempfile.TemporaryDirectory() as tmp:
        for lab_id in ids:
            directory, manifest = load_lab(lab_id)
            for target in TARGETS.values():
                skeleton = manifest.get("skeletons", {}).get(target.id)
                if not skeleton or not (directory / skeleton).is_file():
                    problems.append(f"{lab_id}: 缺 {target.id} 的骨架")
                    continue
                obj = Path(tmp) / f"{lab_id}.{target.id}.o"
                done = subprocess.run(
                    [clang(), f"--target={target.triple}", "-c", str(directory / skeleton), "-o", str(obj)],
                    capture_output=True, text=True,
                )
                if done.returncode != 0:
                    problems.append(f"{lab_id}/{target.id}: 骨架汇编失败\n{done.stderr.strip()}")
            # 参考实现在两个优化级、两种语法下都能出汇编（顺便验证 --target 可用）
            try:
                generate_observation(directory, manifest, Path(tmp) / lab_id)
            except SystemExit as error:
                problems.append(f"{lab_id}: {error}")
            meta_path = OBSERVED / lab_id / "meta.json"
            if not meta_path.is_file():
                problems.append(f"{lab_id}: 观察层还没生成，运行 python3 scripts/lab.py gen {lab_id}")
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("source_sha256") != _source_hash(directory, manifest):
                problems.append(f"{lab_id}: 观察层过期（参考实现改过），运行 python3 scripts/lab.py gen {lab_id}")
            for name in meta.get("files", []):
                if not (OBSERVED / lab_id / name).is_file():
                    problems.append(f"{lab_id}: 观察层缺文件 {name}")
    if problems:
        raise SystemExit("实验校验失败：\n" + "\n".join(f"  - {p}" for p in problems))
    print(f"{len(ids)} 个实验通过：骨架在 {len(TARGETS)} 个目标都能汇编，观察层是最新的。")
    return 0


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="多目标实验台：体检、预生成汇编、编译运行、校验")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="体检").set_defaults(func=cmd_doctor)
    gen = sub.add_parser("gen", help="预生成观察层汇编")
    gen.add_argument("lab", nargs="?")
    gen.set_defaults(func=cmd_gen)
    run = sub.add_parser("run", help="编译并运行汇编骨架")
    run.add_argument("lab")
    run.add_argument("--target", choices=sorted(TARGETS))
    run.add_argument("--all", action="store_true", help="跑本机所有能跑的目标，并比对输出是否一致")
    run.set_defaults(func=cmd_run)
    sub.add_parser("check", help="校验").set_defaults(func=cmd_check)
    arguments = parser.parse_args()
    return arguments.func(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
