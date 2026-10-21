#!/usr/bin/env python3
"""T-901：Linux / C++ / 汇编及杂项领域清单生成器（leader 自用，只读 .cache/legacy-src）。

做法：范围内每个被 git 跟踪的文件，归到“离它最近的、直接含源码的目录”这个单元；
没有源码目录可归的归“杂项”单元。单元的 verdict/target 由 RULES 按路径前缀给出，
再对源码内容做哈希查重、对 cpp/c 单元真编译。最后校验范围内文件零遗漏。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / ".cache" / "legacy-src"
OUT = Path(__file__).resolve().parent

# (repo, 路径前缀) -> 范围；前缀 "" 表示整个仓库根下“不属于其他人”的文件
SCOPE = [
    ("Linux", "C"), ("Linux", "CPlusPlus"), ("Linux", "Driver"), ("Linux", "Process"),
    ("Linux", "Thread"), ("Linux", "UnitTest"), ("Linux", "SDL"),
    ("Practice", "CPP"), ("Practice", "Assembly"), ("Practice", "CGI"),
    ("Practice", "Vue"),
]
ROOT_FILES = [("Linux", f) for f in ("README.md", "LICENSE", "cmake_install.cmake", ".gitignore")]

SRC_EXT = {".c", ".cpp", ".cc", ".h", ".hpp", ".s", ".asm", ".cgi", ".ui", ".glade"}
JUNK_EXT = {".user", ".project", ".cproject", ".workspace", ".depend", ".layout", ".cbp", ".tags",
            ".db", ".session", ".o", ".out", ".prefs", ".anjuta", ".pro", ".pri", ".txt", ".project"}
JUNK_NAME = {"a.out", "app", "exit"}

# 规则按顺序匹配，取第一个。target/verdict/reason/topic。
# 路径形如 "<repo>/<相对路径>"
RULES: list[tuple[str, dict]] = [
    ("Linux/UnitTest/App", dict(target="programming/c-plus-plus", verdict="drop-third-party",
        reason="googletest 自带的 sample1–sample10 样例原样拷贝（上游 google/googletest 的 googletest/samples），非原创")),
    ("Linux/UnitTest", dict(target="programming/c-plus-plus", verdict="keep", topic="单元测试入门（googletest）")),
    ("Linux/SDL/3-line", dict(target="practice/c-gui-lab", verdict="drop-junk",
        reason="Anjuta 生成的 autotools 工程样板（configure、Makefile.in、ltmain.sh、intltool 等），源码仅 main.c 一类")),
    ("Linux/SDL", dict(target="practice/c-gui-lab", verdict="keep", topic="SDL 1.2 入门（背景、线）")),
    ("Linux/Driver", dict(target="programming/linux", verdict="keep", topic="内核模块 Hello World")),
    ("Linux/Process", dict(target="programming/linux", verdict="keep", topic="防止僵尸进程")),
    ("Linux/Thread", dict(target="programming/linux", verdict="keep", topic="pthread 创建、join、互斥")),
    ("Linux/C/Language", dict(target="programming/machine", verdict="keep", topic="C 语言基础练习（含 glade 界面）")),
    ("Linux/C/CLanguage", dict(target="programming/machine", verdict="keep", topic="C 语言栈溢出、指针")),
    ("Linux/C", dict(target="programming/machine", verdict="keep", topic="C 语言练习")),
    ("Linux/CPlusPlus/0-assembly", dict(target="programming/machine", verdict="keep", topic="汇编入门（与 Practice/Assembly 比对）")),
    ("Linux/CPlusPlus/33-cgi", dict(target="programming/linux", verdict="keep", topic="CGI 程序")),
    ("Linux/CPlusPlus/31-signal", dict(target="programming/linux", verdict="keep", topic="信号")),
    ("Linux/CPlusPlus/24-signal", dict(target="programming/linux", verdict="drop-junk", reason="只有 IDE 配置文件，无源码")),
    ("Linux/CPlusPlus/Basic", dict(target="programming/c-plus-plus", verdict="keep", topic="C++ 综合工程（Basic/Class/Derive/Feature/FrameWork 与根 main.cpp、Qt 主窗口）")),
    ("Linux/CPlusPlus/Class", dict(target="programming/c-plus-plus", verdict="merge-into:linux-cplusplus", reason="与根 main.cpp 同属一个 CMake 工程，整体归入")),
    ("Linux/CPlusPlus/Derive", dict(target="programming/c-plus-plus", verdict="merge-into:linux-cplusplus", reason="同上")),
    ("Linux/CPlusPlus/Feature", dict(target="programming/c-plus-plus", verdict="merge-into:linux-cplusplus", reason="同上")),
    ("Linux/CPlusPlus/FrameWork", dict(target="programming/c-plus-plus", verdict="merge-into:linux-cplusplus", reason="同上；其中工厂/单例另在设计模式清单对照，是否重复交 T-001 的 dp 清单核对")),
    ("Linux/CPlusPlus", dict(target="programming/c-plus-plus", verdict="keep", topic="C++ 综合工程")),
    ("Practice/CPP", dict(target="programming/c-plus-plus", verdict="keep", topic="C++ 语法逐点小例子")),
    ("Practice/Assembly", dict(target="programming/machine", verdict="keep", topic="x86 汇编入门")),
    ("Practice/CGI", dict(target="programming/linux", verdict="keep", topic="CGI 程序")),
    ("Practice/Vue", dict(target="-", verdict="drop-junk", reason="3 个文件：LICENSE 与两个空壳页面，无内容")),
    ("Practice/XNode", dict(target="programming/qt", verdict="keep",
        topic="Qt 网络节点程序（Server/Client/Monitor，CMake）——按内容归 qt，交给 T-101 的 Qt 清单并入")),
]

# 批注素材（读过各组代表性样本后写，具体到文件；逐单元的批注在“写批注”阶段再细化）
NOTES: list[tuple[str, str]] = [
    ("Linux/CPlusPlus/11-basic/new_three-dimensional_array", "裸 new 嵌套三层指针数组，释放要手写三层循环，任何一层漏掉就泄漏；应改用 std::vector 或一维数组加索引换算。Box 示例同文件混了两个主题。"),
    ("Practice/CPP/new", "二维数组用 new int*[4] 逐行分配再逐行 delete，异常安全差；同上，应改为 vector<vector<int>> 或一维连续存储。"),
    ("Linux/CPlusPlus/13-class", "示例照搬教程的 Box 类：成员/友元演示没有不变式可守，友元函数直接读成员；缺少为什么要用友元的取舍说明；.user 文件被提交进仓库。"),
    ("Linux/CPlusPlus/16-polymorphism", "main 里 new teacher()/new doctor() 后不 delete（泄漏），officer 基类是否有虚析构需核对；应用 unique_ptr 持有多态对象。"),
    ("Linux/CPlusPlus/11-basic", "每个目录演示一个语法点，命名混用（tiger_limit、1-assign）；多个示例用 using namespace std；部分依赖 boost（getline）本机缺失而无法编译。"),
    ("Linux/CPlusPlus/32-thread", "pthread 与 std::thread 混用在同一批示例；detach 的线程在 main 返回时可能还在跑；pthread_join 示例用了 wait 这个与 POSIX wait() 同名的函数名。"),
    ("Linux/Thread/03-ThreadMutex", "目录叫 Mutex，实际代码没有任何互斥量：两个线程读-睡-写同一个全局 counter，演示的是数据竞争而非互斥；(void*)1 直接把整数塞进 void* 当参数；用 %x 打印 pthread_t 不可移植；应补 pthread_mutex_t 并对比有无锁的结果。"),
    ("Linux/Thread", "同一个主题（创建/join/互斥）在 01-Thread、01-ThreadCreate、T01-Create 等目录重复出现了三代，需要选规范版；多数没有检查 pthread_create 的返回值。"),
    ("Linux/Process/G02-PreventZombie", "在 SIGCHLD 处理函数里调用 printf（非异步信号安全）；signal() 每次循环重复注册；声明 void signal_terminated(); 与定义 (int) 不一致；waitpid 只回收一个子进程，多个同时退出会漏；应改 sigaction + while(waitpid(-1, WNOHANG)>0)。"),
    ("Linux/C/CLanguage/1-StackOverFlow", "文件名叫栈溢出，但真正的溢出代码（8MB 局部数组、fabonacci(100)）被注释掉了，剩下的只是 49 次朴素递归斐波那契；函数名拼错（fabonacci）；没有演示崩溃现象本身。"),
    ("Linux/C/CLanguage/src", "GTK 回调里夹杂业务逻辑（函数指针演示、成绩表）；sprintf 到固定 100 字节缓冲无长度检查；函数指针用 int (*func)() 空参数声明；界面与示例逻辑混在一个文件。"),
    ("Linux/Driver", "内核模块 Hello World，只能在 Linux 配内核头文件构建；缺 Makefile（obj-m）与加载/卸载说明，Windows 上无法验证。"),
    ("Linux/UnitTest/1-Primer", "Qt Creator 生成的 googletest 工程模板，tst_*.h 只有模板里的占位测试；gtest_dependency.pri 依赖本机 googletest 源码路径。"),
    ("Linux/UnitTest/App", "googletest 官方 samples 原样拷贝，不是原创。"),
    ("Linux/SDL", "SDL 1.2 时代写法（SDL_SetVideoMode 一类）已过时，现行为 SDL2/SDL3；CodeLite/Code::Blocks 工程文件混入；.bmp 是示例资源。"),
    ("Practice/Assembly", "x86 汇编入门，目录里同时提交了 a.out、exit.o、app 等构建产物；只有 mov eax,5 / ret 一类最小程序，缺少平台说明（nasm 还是 gas、32 还是 64 位）。"),
    ("Practice/XNode", "Qt 网络节点程序（Server/Client/Monitor/Library，CMake）：多模块拆分有意识但模块边界靠 include 路径隐式约定，缺少协议文档与测试，是 qt 应用最像“完整项目”的一份素材。"),
    ("Linux/CPlusPlus", "根 CMake 工程同时挂 Basic/Class/Derive/Feature/FrameWork 与 Qt 主窗口（mainwindow.*、glade），把语法练习和 GUI 壳混在一起；auto/const/函数指针/工厂/单例等主题各只有几行，缺说明。"),
]

ROOT_DROP = dict(target="-", verdict="drop-junk", reason="仓库根目录的说明、许可证、构建残留")


def sh(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def tracked(repo: str, prefix: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(SRC / repo), "ls-files", "-z", "--", prefix],
                         capture_output=True).stdout.split(b"\0")
    return [f.decode("utf-8", "replace") for f in out if f]


def first_commit(repo: str, path: str) -> str:
    r = subprocess.run(["git", "-C", str(SRC / repo), "log", "--format=%ad", "--date=short", "--", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    dates = [d for d in r.stdout.split() if d]
    return min(dates) if dates else ""


def norm_hash(repo: str, f: str):
    try:
        d = (SRC / repo / f).read_bytes()
    except OSError:
        return None
    d = d.replace(b"\r\n", b"\n").strip()
    return hashlib.md5(d).hexdigest() if d else None


def is_source(f: str) -> bool:
    ext = os.path.splitext(f)[1].lower()
    if os.path.basename(f) in JUNK_NAME:
        return False
    if os.path.basename(f) in ("CMakeLists.txt", "Makefile", "README.md", "README"):
        return True
    if ext == ".txt" and "CMakeLists" not in f:
        return False
    return ext in SRC_EXT


def rule_for(path: str) -> dict:
    for prefix, rule in RULES:
        if path == prefix or path.startswith(prefix + "/"):
            return dict(rule)
    return dict(target="?", verdict="drop-junk", reason="未匹配规则")


# 整体算一个单元的工程根（其下子目录不再拆）。Linux/CPlusPlus 里 Basic/Class/Derive/Feature/FrameWork
# 与根目录的 main.cpp 同属一个 CMake 工程（根 main.cpp 调用它们），拆开单独编译必然缺 main。
PROJECT_ROOTS = [
    "Practice/XNode", "Linux/C/CLanguage", "Linux/C/Language",
    "Linux/CPlusPlus/Basic", "Linux/CPlusPlus/Class", "Linux/CPlusPlus/Derive", "Linux/CPlusPlus/Feature",
    "Linux/CPlusPlus/FrameWork", "Linux/CPlusPlus/0-assembly", "Linux/UnitTest/App", "Linux/SDL/3-line",
]
# Practice/CPP 是 38 个互相独立的“一个文件一个小程序”，按文件拆成单元
PER_FILE_SCOPES = ["Practice/CPP"]


def unit_dir(repo: str, f: str, scope: str, src_dirs: set[str]) -> str:
    """离 f 最近的、直接含源码文件的祖先目录（不越过 scope）；工程根整体归一；PER_FILE 按文件拆。"""
    full = f"{repo}/{f}"
    for pr in PROJECT_ROOTS:
        if full == pr or full.startswith(pr + "/"):
            return pr.split("/", 1)[1]
    for pf in PER_FILE_SCOPES:
        if full.startswith(pf + "/") and f.endswith(".cpp"):
            return f
    d = os.path.dirname(f)
    while d and d.startswith(scope) and len(d) >= len(scope):
        if d in src_dirs:
            return d
        if d == scope:
            break
        d = os.path.dirname(d)
    return scope


def slug(s: str) -> str:
    s = re.sub(r"[^0-9A-Za-z]+", "-", s).strip("-").lower()
    return s or "x"


def try_build(repo: str, d: str, files: list[str]) -> tuple[bool, str]:
    cpps = [f for f in files if f.endswith((".cpp", ".cc"))]
    cs = [f for f in files if f.endswith(".c")]
    if not (cpps or cs):
        return False, "无可编译的 .c/.cpp"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "a.exe")
        if cpps:
            cmd = ["g++", "-std=c++20", "-O0", "-w", "-pthread", *[str(SRC / repo / f) for f in cpps],
                   f"-I{SRC / repo / d}", "-o", out]
        else:
            cmd = ["gcc", "-O0", "-w", "-pthread", *[str(SRC / repo / f) for f in cs],
                   f"-I{SRC / repo / d}", "-o", out]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            err = (r.stderr.strip().splitlines() or ["?"])
            return False, "编译失败: " + (err[0] if len(err) else "?")[:160]
        try:
            run = subprocess.run([out], capture_output=True, text=True, encoding="utf-8", errors="replace",
                                 timeout=5, stdin=subprocess.DEVNULL)
            first = (run.stdout.strip().splitlines() or ["(无输出)"])[0][:80]
            return True, f"编译通过并运行，退出码 {run.returncode}，首行: {first}"
        except subprocess.TimeoutExpired:
            return True, "编译通过，运行超时 5s（可能等待输入或常驻）"
        except OSError as e:
            return True, f"编译通过，运行失败: {e}"


def main():
    units: dict[str, dict] = {}
    covered: set[tuple[str, str]] = set()
    all_files: list[tuple[str, str]] = []

    for repo, scope in SCOPE:
        files = tracked(repo, scope)
        all_files += [(repo, f) for f in files]
        src_dirs = {os.path.dirname(f) for f in files if is_source(f) and not f.endswith(("CMakeLists.txt", "Makefile", "README.md"))}
        groups: dict[str, list[str]] = defaultdict(list)
        for f in files:
            groups[unit_dir(repo, f, scope, src_dirs)].append(f)
        for d, fs in sorted(groups.items()):
            path = f"{repo}/{d}"
            rule = rule_for(path)
            srcs = [f for f in fs if is_source(f)]
            uid = slug(path)
            note = next((n for pre, n in sorted(NOTES, key=lambda t: -len(t[0])) if path == pre or path.startswith(pre + "/")), "")
            u = dict(unit=uid, title=d.split("/", 1)[-1] if "/" in d else d, target=rule["target"],
                     verdict=rule["verdict"], canonical=[path], duplicates=[],
                     first_commit=first_commit(repo, d), files=len(srcs), junk_files=len(fs) - len(srcs),
                     run="read-only", build="", build_checked=False,
                     topic_hint=rule.get("topic", "新增"), quality_notes=note, reason=rule.get("reason", ""))
            u["_hash"] = tuple(sorted(h for h in (norm_hash(repo, f) for f in srcs) if h))
            u["_repo"], u["_dir"], u["_srcs"] = repo, d, srcs
            units[uid] = u
            for f in fs:
                covered.add((repo, f))

    # 路径归属表里归 T-901 但不在 SCOPE 下的散件（仓库根的 README、LICENSE、text.txt 等）
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import path_owners as po
    scoped = set(all_files)
    extra = []
    for repo in ("Linux", "Practice"):
        for f in po.all_files(repo):
            if po.owner(f"{repo}/{f}") == "T-901" and (repo, f) not in scoped:
                extra.append((repo, f))
    ROOT_FILES[:] = extra
    all_files += extra
    misc = dict(unit="linux-root-misc", title="Linux、Practice 仓库根散件", target="-", verdict="drop-junk",
                canonical=["Linux+Practice/(root)"], duplicates=[], first_commit="", files=0, junk_files=len(ROOT_FILES),
                run="read-only", build="", build_checked=False, topic_hint="-", quality_notes="",
                reason=ROOT_DROP["reason"], _hash=(), _repo="Linux", _dir="", _srcs=[])
    units["linux-root-misc"] = misc
    covered |= set(ROOT_FILES)

    # 重复：源码内容哈希集合相同且非空 → 后者 drop-duplicate；内容为子集的标 note
    seen: dict[tuple, str] = {}
    for uid, u in units.items():
        if u["verdict"] != "keep" or not u["_hash"]:
            continue
        if u["_hash"] in seen:
            first = units[seen[u["_hash"]]]
            first["duplicates"].append(u["canonical"][0])
            u["verdict"] = "drop-duplicate"
            u["reason"] = f"源码内容与 {first['canonical'][0]} 完全相同"
        else:
            seen[u["_hash"]] = uid
    # 汇编：Linux/CPlusPlus/0-assembly 与 Practice/Assembly 的文件级重叠
    a1 = units.get("linux-cplusplus-0-assembly")
    a2 = units.get("practice-assembly")
    if a1 and a2:
        s1, s2 = set(a1["_hash"]), set(a2["_hash"])
        if s1 and s1 <= s2:
            a1["verdict"] = "drop-duplicate"; a1["reason"] = "文件内容均已包含在 Practice/Assembly 中"
            a2["duplicates"].append(a1["canonical"][0])
        elif s2 and s2 <= s1:
            a2["verdict"] = "drop-duplicate"; a2["reason"] = "文件内容均已包含在 Linux/CPlusPlus/0-assembly 中"
            a1["duplicates"].append(a2["canonical"][0])

    # 编译实测
    for uid, u in units.items():
        if u["verdict"] != "keep":
            continue
        srcs = u["_srcs"]
        tgt = u["target"]
        if any(f.endswith((".cpp", ".cc", ".c")) for f in srcs):
            if tgt == "programming/linux" or u["title"].startswith(("Driver", "01-Hello", "B1")):
                u["run"] = "linux-only"
            elif tgt in ("programming/c-plus-plus", "programming/machine", "programming/design-patterns"):
                u["run"] = "cli"
            else:
                u["run"] = "toolchain"
            blob = "".join((SRC / u["_repo"] / f).read_text(encoding="utf-8", errors="replace") for f in srcs
                           if f.endswith((".c", ".cpp", ".cc", ".h")))
            if re.search(r"#include\s*<(pthread|unistd|sys/|signal|linux/|arpa/|netinet/)", blob):
                u["run"] = "linux-only" if u["run"] != "toolchain" else u["run"]
            if re.search(r"#include\s*<(Q[A-Z]|SDL|gtk|gtest|gmock)", blob) or "gtest" in blob:
                u["run"] = "toolchain"
            if u["run"] in ("cli", "linux-only"):
                bdir = u["_dir"] if not u["_dir"].endswith(".cpp") else os.path.dirname(u["_dir"])
                ok, msg = try_build(u["_repo"], bdir, srcs)
                u["build_checked"] = True
                u["build"] = ("g++ -std=c++20 *.cpp" if any(f.endswith((".cpp", ".cc")) for f in srcs) else "gcc *.c") + f"  # {msg}"
                if not ok and u["run"] == "linux-only":
                    u["build"] += "（Windows 上预期失败，需 WSL/Linux）"
        elif any(f.endswith((".s", ".asm")) for f in srcs):
            u["run"] = "toolchain"; u["build"] = "需要汇编器（as/nasm）"

    # 零遗漏校验
    missing = [x for x in all_files if x not in covered]
    out_units = []
    for u in units.values():
        for k in ("_hash", "_repo", "_dir", "_srcs"):
            u.pop(k, None)
        out_units.append(u)
    (OUT / "manifest-linux-cpp-machine.json").write_text(json.dumps(out_units, ensure_ascii=False, indent=2), encoding="utf-8")

    stat = defaultdict(int)
    for u in out_units:
        stat[u["verdict"]] += 1
    tgt = defaultdict(int)
    for u in out_units:
        if u["verdict"] == "keep":
            tgt[u["target"]] += 1
    nb = sum(1 for u in out_units if u["build_checked"])
    npass = sum(1 for u in out_units if u["build_checked"] and "编译通过" in u["build"])
    report = [f"范围内被跟踪文件 {len(all_files)}，未覆盖 {len(missing)}", f"单元 {len(out_units)}：{dict(stat)}",
              f"keep 按目标：{dict(tgt)}", f"实测编译 {nb} 个单元，通过 {npass}"]
    if missing:
        report.append("未覆盖文件：" + ", ".join(f"{r}/{f}" for r, f in missing[:20]))
    (OUT / "verify-linux-cpp-machine.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    sys.exit(main())
