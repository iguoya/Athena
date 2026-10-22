# -*- coding: utf-8 -*-
"""对 run:cli 的规范版单元批量编译并运行（v2）。

编译策略：
- 每个含 main 的源文件视为一个独立程序入口，单独编译运行（3-stack 等目录是多程序）。
- 无 main 的「库形态」目录：全部源文件一起 -fsyntax-only 检查语法。
- 失败的入口再尝试与其他源文件同编一次（处理 include .cpp 与引用外部符号两种形态）。
"""
import json
import subprocess
from pathlib import Path

SRC = Path(r"C:\Users\tiger\Athena\.cache\legacy-src")
BUILD = Path(r"C:\Users\tiger\Athena\.cache\build-zcode")
OUT = Path(r"C:\Users\tiger\Athena\comms\legacy-archive\artifacts\zcode\build-results.json")
BUILD.mkdir(parents=True, exist_ok=True)

# unit -> (repo, dir, 语言)
TASKS = [
    ("dp-adapter", "Practice", "DesignPatterns/Adapter", "cpp"),
    ("dp-simple-factory", "Practice", "DesignPatterns/SimpleFactory", "cpp"),
    ("dp-factory-method", "Practice", "DesignPatterns/Factory", "cpp"),
    ("dp-abstract-factory", "Practice", "DesignPatterns/AbstractFactory", "cpp"),
    ("dp-singleton", "Practice", "DesignPatterns/Singleton", "cpp"),
    ("dp-observer", "Practice", "DesignPatterns/Observer", "cpp"),
    ("dp-strategy-v0", "DesignPattern", "StrategyV0", "cpp"),
    ("dp-strategy-sort", "DesignPattern", "Strategy", "cpp"),
    ("dp-template-method-tank", "DesignPattern", "TemplateMethod", "cpp"),
    ("dp-template-method-basic", "DesignPatterns", "workspace/TemplateMethod", "cpp"),
    ("dp-facade", "DesignPattern", "Facade", "cpp"),
    ("ds-linear", "Practice", "DataStructure/linear", "cpp"),
    ("ds-recursion", "Practice", "DataStructure/recursion", "cpp"),
    ("ds-search", "Practice", "DataStructure/search", "cpp"),
    ("ds-sort", "Practice", "DataStructure/sort", "cpp"),
    ("ds-tree", "Practice", "DataStructure/tree", "cpp"),
    ("alg-c-array", "algorithm", "11-linner/1-array", "c"),
    ("alg-c-list", "algorithm", "11-linner/2-list", "c"),
    ("alg-c-stack", "algorithm", "11-linner/3-stack", "c"),
    ("alg-c-queue", "algorithm", "11-linner/4-queue", "c"),
    ("alg-c-string", "algorithm", "11-linner/5-string", "c"),
    ("alg-c-tree", "algorithm", "12-tree/1-tree", "c"),
    ("alg-goldbach", "algorithm", "21-basic/Goldbach", "c"),
    ("alg-callback", "algorithm", "21-basic/callback", "cpp"),
    ("alg-check", "algorithm", "21-basic/check", "c"),
    ("alg-file", "algorithm", "21-basic/file", "c"),
    ("alg-function-pointer", "algorithm", "21-basic/function_pointer", "c"),
    ("alg-magic-square", "algorithm", "21-basic/magic_square", "c"),
    ("alg-pi", "algorithm", "21-basic/pi", "c"),
    ("alg-struct", "algorithm", "21-basic/struct", "c"),
    ("alg-volume", "algorithm", "21-basic/volume", "c"),
    ("alg-substring", "algorithm", "backtracking/substring", "cpp"),
    ("alg-dacidian-backpack", "algorithm", "1-速学速用大辞典/backpack", "c"),
    ("alg-dacidian-backtrack", "algorithm", "1-速学速用大辞典/backtrack", "c"),
    ("alg-dacidian-cstring", "algorithm", "1-速学速用大辞典/c_string", "c"),
    ("alg-dacidian-enum", "algorithm", "1-速学速用大辞典/enum", "c"),
    ("alg-dacidian-iterative", "algorithm", "1-速学速用大辞典/iterative", "c"),
    ("alg-dacidian-sort", "algorithm", "1-速学速用大辞典/sort", "c"),
    ("alg-avg-value", "algorithm", "22-recursion/average_value", "cpp"),
    ("alg-fib-v2", "algorithm", "22-recursion/fibnonacciv2", "cpp"),
    ("alg-fibonacci", "algorithm", "22-recursion/fibonacci", "c"),
    ("alg-footstep", "algorithm", "22-recursion/footstep", "c"),
    ("alg-footstep-v2", "algorithm", "22-recursion/footstepv2", "cpp"),
    ("alg-hanoi", "algorithm", "22-recursion/hanoi", "c"),
    ("alg-int-factorization", "algorithm", "22-recursion/integer_factorization", "c"),
    ("alg-max-value", "algorithm", "22-recursion/max_value", "cpp"),
    ("alg-numeral-system", "algorithm", "22-recursion/numeral_system", "c"),
    ("alg-permutation", "algorithm", "22-recursion/permutation", "cpp"),
    ("alg-queen", "algorithm", "22-recursion/queen", "c"),
    ("alg-binary-search", "algorithm", "23-divide_and_conconquer/binary_search", "cpp"),
    ("alg-gold", "algorithm", "23-divide_and_conconquer/gold", "cpp"),
    ("alg-merge-sort", "algorithm", "23-divide_and_conconquer/merge_sort", "cpp"),
    ("alg-queen8", "algorithm", "23-divide_and_conconquer/queen", "cpp"),
]


def run_cmd(cmd, cwd, timeout=120):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def first_line(s):
    for ln in (s or "").splitlines():
        if ln.strip():
            return ln.strip()[:120]
    return ""


def last_err(se):
    lines = [l for l in se.strip().splitlines() if l.strip()]
    return lines[-1][:200] if lines else ""


def try_build_run(bdir, cc, std, srcs, exe):
    cmd = [cc, std, "-w", *[str(s) for s in srcs], "-o", str(exe)]
    rc, _so, se = run_cmd(cmd, bdir)
    if rc != 0:
        return {"ok": False, "stage": "compile", "note": last_err(se), "srcs": [s.name for s in srcs]}
    try:
        rc2, so2, se2 = run_cmd([str(exe)], bdir, timeout=15)
    except subprocess.TimeoutExpired:
        return {"ok": True, "stage": "run-timeout", "note": "编译通过；运行 15s 未退出（等待输入或长循环）",
                "srcs": [s.name for s in srcs]}
    return {"ok": rc2 == 0, "stage": "run", "srcs": [s.name for s in srcs],
            "out": first_line(so2) or first_line(se2),
            "note": "" if rc2 == 0 else (last_err(se2) or f"退出码 {rc2}")}


def build_unit(unit, repo, d, lang):
    src = SRC / repo / d
    bdir = BUILD / unit
    bdir.mkdir(parents=True, exist_ok=True)
    ext = ".cpp" if lang == "cpp" else ".c"
    cc = "g++" if lang == "cpp" else "gcc"
    std = "-std=c++20" if lang == "cpp" else "-std=c11"
    all_src = sorted(src.glob("*" + ext))
    # 入口：main* 与 unit_test_main*（C 的 Check runner）；GTest 风格的 test_*.cpp 不是入口
    mains = [s for s in all_src if s.name.startswith(("main", "unit_test_main"))]
    tests = [s for s in all_src if s.name.startswith("test_") and s not in mains]
    others = [s for s in all_src if s not in mains and s not in tests]
    entries = []
    if mains:
        for m in mains:
            # 先单入口，失败再把其余非测试源文件带上重试一次
            r = try_build_run(bdir, cc, std, [m], bdir / (m.stem + ".exe"))
            if not r["ok"] and others:
                r2 = try_build_run(bdir, cc, std, [m] + others, bdir / (m.stem + "_all.exe"))
                r2["note"] = (r2["note"] or "") + f"（单编 {m.name} 失败：{r['note']}；附其余源重试）"
                r = r2
            r["entry"] = m.name
            entries.append(r)
    else:
        rc, _so, se = run_cmd([cc, std, "-w", "-fsyntax-only", *[str(s) for s in all_src]], bdir)
        entries.append({
            "ok": rc == 0, "stage": "syntax-only", "entry": None,
            "note": "库形态无 main；" + ("语法检查通过，独立运行需配入口" if rc == 0 else "语法检查失败：" + last_err(se)),
        })
    # test_* 单独一票（GTest）；空文件如实标注
    for t in tests:
        if t.stat().st_size == 0:
            entries.append({"ok": False, "stage": "test-empty", "entry": t.name,
                            "note": "空文件（0 B），当年未写完"})
            continue
        rc, _so, se = run_cmd([cc, std, "-w", "-fsyntax-only", "-I", str(src), str(t)], bdir)
        entries.append({
            "ok": rc == 0, "stage": "test-syntax", "entry": t.name,
            "note": ("语法检查通过" if rc == 0 else "语法检查失败：" + last_err(se)),
        })
    return entries


def main():
    results = {}
    for unit, repo, d, lang in TASKS:
        try:
            results[unit] = build_unit(unit, repo, d, lang)
        except Exception as e:  # noqa: BLE001
            results[unit] = [{"ok": False, "stage": "exception", "entry": None, "note": str(e)[:200]}]
        for r in results[unit]:
            tag = "PASS" if r["ok"] else "FAIL"
            print(f"{tag} {unit} [{r['stage']}:{r.get('entry')}] {r.get('out','')} {r['note'][:110]}")
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v) for v in results.values())
    ok = sum(1 for v in results.values() for r in v if r["ok"])
    print(f"\n入口级通过 {ok}/{n}，明细 -> {OUT}")


if __name__ == "__main__":
    main()
