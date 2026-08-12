#!/usr/bin/env python3
"""构建期：编译并真实运行代码片段，把源码和运行结果生成成 C++ 源文件。

结果不输出到终端，而是作为字符串常量编译进二进制（存内存）。
运行期通过 g_snippets map 按章节 ID 查表显示。
"""
import json, os, subprocess, sys, tempfile


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: build_snippets.py <chapters.json> <project_root> <output.cpp>",
            file=sys.stderr,
        )
        sys.exit(1)

    json_path = sys.argv[1]
    project_root = sys.argv[2]
    output_cpp = sys.argv[3]

    with open(json_path, encoding="utf-8") as f:
        config = json.load(f)

    entries = []
    for ch in config.get("chapters", []):
        snippet = ch.get("snippet", "")
        if not snippet:
            continue
        ch_id = ch["id"]
        src_path = os.path.join(project_root, snippet)

        with open(src_path, encoding="utf-8") as f:
            source = f.read()

        # 编译 + 运行（结果存内存，不打印）
        result = compile_and_run(src_path)

        entries.append((ch_id, source, result))
        print(f"  snippet '{ch_id}' -> 运行完成", file=sys.stderr)

    # 生成 C++ 源文件
    with open(output_cpp, "w", encoding="utf-8") as f:
        f.write('// 自动生成，勿手改 —— 由 scripts/build_snippets.py 生成\n')
        f.write('#include "snippets_data.h"\n\n')
        f.write("std::map<std::string, SnippetData> g_snippets = {\n")
        for ch_id, source, result in entries:
            f.write(f'    {{ "{ch_id}", {{\n')
            f.write(f"        R\"SNIP({source})SNIP\",\n")
            f.write(f"        R\"SNIP({result})SNIP\"\n")
            f.write("    }},\n")
        f.write("};\n")


def compile_and_run(src_path):
    """编译并运行单个 .cpp，返回运行结果字符串。"""
    tmp_dir = tempfile.mkdtemp(prefix="athena_snippet_")
    binary = os.path.join(tmp_dir, "snippet")

    # 编译
    compile_proc = subprocess.run(
        ["c++", "-std=c++17", src_path, "-o", binary],
        capture_output=True, text=True, timeout=30,
    )
    if compile_proc.returncode != 0:
        return "编译错误:\n" + compile_proc.stderr

    # 运行（带超时保护）
    try:
        run_proc = subprocess.run(
            [binary], capture_output=True, text=True, timeout=5,
        )
        result = run_proc.stdout
        if run_proc.returncode != 0:
            result += "\n(退出码 %d)\n" % run_proc.returncode
            result += run_proc.stderr
        return result
    except subprocess.TimeoutExpired:
        return "(运行超时，可能存在死循环)"


if __name__ == "__main__":
    main()
