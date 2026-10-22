#!/usr/bin/env python3
"""T-001 编译实测脚本：对规范版单元真编译真运行，记录命令与输出首行。

-std=c++20 与应用实验引擎一致（packages/athena-course-shell/src/compiler.rs）。
无 main.cpp 的单元只做 -c 目标文件编译（如实记录“无 main，不可运行”）。
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(".cache/legacy-src").resolve()
OUT = Path("comms/legacy-archive/artifacts/zcode/build-work").resolve()
OUT.mkdir(parents=True, exist_ok=True)

# (标签, 源目录, 编译哪些 .cpp；None=目录下全部 .cpp)
CASES = [
    ("abstractfactory", SRC / "DesignPattern/AbstractFactory", None),
    ("adapter", SRC / "DesignPattern/Adapter", None),
    ("facade-no-main", SRC / "DesignPattern/Facade", None),
    ("factory", SRC / "DesignPattern/Factory", None),
    ("observer", SRC / "DesignPattern/Observer", None),
    ("simplefactory", SRC / "DesignPattern/SimpleFactory", None),
    ("singleton", SRC / "DesignPattern/Singleton", None),
    ("strategy-v0", SRC / "DesignPattern/StrategyV0", None),
    ("strategy-sort-no-main", SRC / "DesignPattern/Strategy", None),
    ("templatemethod-tank-no-main", SRC / "DesignPattern/TemplateMethod", None),
    ("workspace-templatemethod", SRC / "DesignPatterns/workspace/TemplateMethod", None),
]


def main() -> None:
    gxx = subprocess.run(["g++", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    print(f"# 编译器：{gxx}")
    for tag, d, _ in CASES:
        cpps = sorted(d.glob("*.cpp"))
        exe = OUT / f"{tag}.exe"
        has_main = any(b"int main" in p.read_bytes() or b"wmain" in p.read_bytes() for p in cpps)
        if has_main:
            cmd = ["g++", "-std=c++20", "-o", str(exe)] + [str(p) for p in cpps]
            mode = "链接运行"
        else:
            objdir = OUT / tag
            objdir.mkdir(exist_ok=True)
            # 逐文件 -c 到 objdir，避免 .o 落进源码目录或当前目录
            for i, p in enumerate(cpps):
                r = subprocess.run(["g++", "-std=c++20", "-c", str(p), "-o", str(objdir / f"{i}.o")],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                if r.returncode != 0:
                    print(f"!! {tag} 第 {i} 个文件 {p.name} 失败:")
                    for ln in r.stderr.strip().splitlines()[:5]:
                        print("   " + ln)
                    break
                print(f"   -c {p.name} OK")
            else:
                print(f"OK {tag} 目标文件全部编译通过（无 main.cpp，不可链接成程序）")
            continue
        print(f"\n== {tag}（{d.name}，{len(cpps)} 个 cpp，{mode}）==")
        print("$ " + " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            first = r.stderr.strip().splitlines()
            print(f"!! 失败（退出码 {r.returncode}）:")
            for ln in first[:6]:
                print("   " + ln)
            continue
        if r.stderr.strip():
            for ln in r.stderr.strip().splitlines()[:4]:
                print("   warn: " + ln)
        print("OK 编译通过")
        if has_main:
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=15)
            out = (run.stdout + run.stderr).strip().splitlines()
            first_out = out[0] if out else "（无输出）"
            print(f"运行退出码 {run.returncode}，输出首行: {first_out}")


if __name__ == "__main__":
    sys.exit(main())
