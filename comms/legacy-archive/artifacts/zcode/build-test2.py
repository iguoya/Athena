#!/usr/bin/env python3
"""T-002 编译实测：数据结构与算法单元真编译真运行。

- C++ 用 g++ -std=c++20（与应用实验引擎一致）；C 用 gcc -std=c17（C 模式）。
- 产物与 .o 一律放系统临时目录（%TEMP%/athena-t002），.cache/legacy-src 保持只读。
- scanf 等输入的程序 10s 超时记「等待输入」。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(".cache/legacy-src").resolve()
OUT = Path(tempfile.gettempdir()) / "athena-t002"
OUT.mkdir(exist_ok=True)

CASES: list[tuple[str, str, list[str]]] = [
    # 数据结构（C++ 版，algorithm/DataStructure）
    ("ds-linear", "algorithm/DataStructure/linear", ["main.cpp", "linear.cpp", "list.cpp"]),
    ("ds-recursion-cpp", "algorithm/DataStructure/recursion", ["main.cpp", "recursion.cpp"]),
    ("ds-search-cpp", "algorithm/DataStructure/search", ["main.cpp"]),
    ("ds-sort-cpp", "algorithm/DataStructure/sort", ["main.cpp"]),
    ("ds-tree-cpp", "algorithm/DataStructure/tree", ["main.cpp"]),
    # 数据结构（C 版，algorithm/11-linner、12-tree）
    ("c-array", "algorithm/11-linner/1-array", ["main.c"]),
    ("c-list", "algorithm/11-linner/2-list", ["main.c"]),
    ("c-stack", "algorithm/11-linner/3-stack", ["main.c"]),
    ("c-queue", "algorithm/11-linner/4-queue", ["main.c"]),
    ("c-string", "algorithm/11-linner/5-string", ["main.c"]),
    ("c-tree", "algorithm/12-tree/1-tree", ["main.c", "advance.c"]),
    # 21-basic（C 语言基础/数学练习）
    ("b-goldbach", "algorithm/21-basic/Goldbach", ["main.c"]),
    ("b-callback", "algorithm/21-basic/callback", ["main.cpp"]),
    ("b-check-main", "algorithm/21-basic/check", ["main.c", "sub.c"]),
    ("b-check-test", "algorithm/21-basic/check", ["test_main.c", "test_sub.c", "sub.c"]),
    ("b-file", "algorithm/21-basic/file", ["main.c"]),
    ("b-funcptr", "algorithm/21-basic/function_pointer", ["main.c"]),
    ("b-magic", "algorithm/21-basic/magic_square", ["main.c", "matrix.c"]),
    ("b-magic-test", "algorithm/21-basic/magic_square", ["unit_test_main.c", "matrix.c"]),
    ("b-pi", "algorithm/21-basic/pi", ["main.c"]),
    ("b-struct", "algorithm/21-basic/struct", ["main.c"]),
    ("b-volume", "algorithm/21-basic/volume", ["main.c"]),
    # 22-recursion
    ("r-average", "algorithm/22-recursion/average_value", ["main.cpp"]),
    ("r-fib-v2", "algorithm/22-recursion/fibnonacciv2", ["main.cpp"]),
    ("r-fib", "algorithm/22-recursion/fibonacci", ["main.c"]),
    ("r-footstep", "algorithm/22-recursion/footstep", ["main.c"]),
    ("r-footstep-v2", "algorithm/22-recursion/footstepv2", ["main.cpp"]),
    ("r-hanoi", "algorithm/22-recursion/hanoi", ["main.c"]),
    ("r-int-factor", "algorithm/22-recursion/integer_factorization", ["main.c"]),
    ("r-max", "algorithm/22-recursion/max_value", ["main.cpp"]),
    ("r-numeral", "algorithm/22-recursion/numeral_system", ["main.c"]),
    ("r-permutation", "algorithm/22-recursion/permutation", ["main.cpp"]),
    ("r-queen", "algorithm/22-recursion/queen", ["main.c"]),
    # 23-divide_and_conconquer
    ("d-binsearch", "algorithm/23-divide_and_conconquer/binary_search", ["main.cpp"]),
    ("d-gold", "algorithm/23-divide_and_conconquer/gold", ["main.cpp"]),
    ("d-mergesort", "algorithm/23-divide_and_conconquer/merge_sort", ["main.cpp"]),
    ("d-queen", "algorithm/23-divide_and_conconquer/queen", ["main.cpp"]),
    # backtracking
    ("bt-substring", "algorithm/backtracking/substring", ["main.cpp"]),
    # 1-速学速用大辞典
    ("dict-backpack", "algorithm/1-速学速用大辞典/backpack", ["main.c"]),
    ("dict-backtrack", "algorithm/1-速学速用大辞典/backtrack", ["main.c"]),
    ("dict-cstring", "algorithm/1-速学速用大辞典/c_string", ["main.c"]),
    ("dict-enum", "algorithm/1-速学速用大辞典/enum", ["main.c"]),
    ("dict-iterative", "algorithm/1-速学速用大辞典/iterative", ["main.c"]),
    ("dict-sort", "algorithm/1-速学速用大辞典/sort", ["main.c", "sort.h"]),
]


def main() -> None:
    gcc = subprocess.run(["gcc", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    print(f"# 编译器：{gcc}")
    ok = fail = wait = 0
    for tag, d, files in CASES:
        srcs = [SRC / d / f for f in files]
        is_c = all(p.suffix == ".c" for p in srcs)
        exe = OUT / f"{tag}.exe"
        cmd = (["gcc", "-std=c17"] if is_c else ["g++", "-std=c++20"]) + \
              ["-o", str(exe)] + [str(p) for p in srcs]
        print(f"\n== {tag}（{d}，{'C' if is_c else 'C++'}）==")
        print("$ " + " ".join(str(c) for c in cmd[1:]))
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            lines = r.stderr.strip().splitlines()
            print(f"!! 编译失败（退出码 {r.returncode}）:")
            for ln in lines[:5]:
                print("   " + ln)
            fail += 1
            continue
        for ln in r.stderr.strip().splitlines()[:3]:
            print("   warn: " + ln)
        ok += 1
        try:
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=10,
                                 input="")
            out = (run.stdout + run.stderr).strip().splitlines()
            first = out[0] if out else "（无输出）"
            print(f"运行退出码 {run.returncode}，输出首行: {first}")
        except subprocess.TimeoutExpired:
            print("运行超时（疑似等待 stdin 输入）")
            wait += 1
    print(f"\n# 小计：编译通过 {ok}、失败 {fail}、通过但运行等输入 {wait}，共 {len(CASES)}")


if __name__ == "__main__":
    sys.exit(main())
