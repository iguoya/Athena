# -*- coding: utf-8 -*-
"""生成 T-002 的 manifest-data-structures.json 与 manifest-algorithms.json，并做零遗漏校验。"""
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(r"C:\Users\tiger\Athena\comms\legacy-archive\artifacts\zcode")
records = json.loads((BASE / "scan.json").read_text(encoding="utf-8"))
files = [(r["repo"], r["path"]) for r in records]

TDS = "postgraduate/data-structures"
TAL = "postgraduate/algorithms"
DS3 = ["algorithm/DataStructure", "Linux/Algorithm/DataStructure"]  # 与 Practice 三处全同

ds_units = [
    {
        "unit": "ds-linear-list", "title": "线性表（自写 Linear/List 与 STL 对照）", "target": TDS,
        "verdict": "keep", "canonical": ["Practice/DataStructure/linear", "Practice/DataStructure/README.md"],
        "duplicates": [d + "/linear" for d in DS3] + [d + "/README.md" for d in DS3[:1]] + ["Linux/Algorithm/DataStructure/README.md"],
        "first_commit": "2020-02-22", "files": 13, "run": "cli",
        "build": "g++ -std=c++20 main.cpp（实测通过，输出 Hello World!；CMake 单文件入口）",
        "build_checked": True, "topic_hint": "ds.linear.list、ds.linear.array",
        "quality_notes": "linear.cpp/linear.h（顺序表）、list.cpp/list.h（链表）与 test_vector/test_map（STL 对照）并存，是三处全同单元的源头（Practice 2020-02-22，早 algorithm 半年）；4 个 GTest 测试本机无 GTest 无法验证；class 内 using namespace std。",
    },
    {
        "unit": "ds-recursion", "title": "递归：斐波那契与 N 皇后（回溯）", "target": "postgraduate/algorithms",
        "verdict": "keep", "canonical": ["Practice/DataStructure/recursion"],
        "duplicates": [d + "/recursion" for d in DS3],
        "first_commit": "2020-02-22", "files": 6, "run": "cli",
        "build": "g++ -std=c++20 main.cpp recursion.cpp（实测通过）",
        "build_checked": True, "topic_hint": "algo.paradigm.backtrack",
        "quality_notes": "按内容是回溯（N 皇后）与递推（Fibonacci），归 algorithms 更合 ADR 0176 决策 1（任务书原定 data-structures 范围，target 待裁决）；Queen 用值传 vector<Block> 递归，每层拷贝路径；Block::operator== 非常量成员。",
    },
    {
        "unit": "ds-search", "title": "查找：顺序与二分（递归+迭代）", "target": TDS,
        "verdict": "keep", "canonical": ["Practice/DataStructure/search"],
        "duplicates": [d + "/search" for d in DS3],
        "first_commit": "2020-02-22", "files": 5, "run": "cli",
        "build": "g++ -std=c++20 main.cpp（实测通过，输出 Hello World!）",
        "build_checked": True, "topic_hint": "ds.hash.table（查找章）",
        "quality_notes": "Search<T> 模板接口用 T* 传元素（应 const T&/值），返回 1 基位置、0 表不存在，语义易错；二分递归版边界写法可作 ds.hash.table 的对照素材。",
    },
    {
        "unit": "ds-sort", "title": "排序", "target": TDS,
        "verdict": "keep", "canonical": ["Practice/DataStructure/sort"],
        "duplicates": [d + "/sort" for d in DS3],
        "first_commit": "2020-02-22", "files": 4, "run": "cli",
        "build": "g++ -std=c++20 main.cpp（实测通过，输出 Hello World!）",
        "build_checked": True, "topic_hint": "ds.sort.basic",
        "quality_notes": "test_sort.cpp 是 0 字节空文件（三处全同地空着）——测试写了五个目录，唯独排序没写，归档批注的好例子；sort.h 内含多排序算法实现。",
        "exclude": ["test_sort.cpp（0 B 空文件）"],
    },
    {
        "unit": "ds-tree-binary", "title": "二叉树（二叉链表，名为 btree）", "target": TDS,
        "verdict": "keep", "canonical": ["Practice/DataStructure/tree"],
        "duplicates": [d + "/tree" for d in DS3],
        "first_commit": "2020-02-22", "files": 5, "run": "cli",
        "build": "g++ -std=c++20 main.cpp（实测通过，输出 Hello World!）",
        "build_checked": True, "topic_hint": "ds.tree.basics",
        "quality_notes": "btree.h 实为二叉树非 B 树，命名误导；节点 T* data 裸指针（所有权不清，析构语义含糊）；遍历用 std::stack/queue 辅助，可作 ds.tree.basics 的非递归遍历对照。",
    },
    {
        "unit": "ds-c-linear", "title": "C 语言线性结构五件（数组/链表/栈/队列/串）", "target": TDS,
        "verdict": "keep", "canonical": ["algorithm/11-linner"],
        "duplicates": ["Linux/Algorithm/DataStructure/11-linner"],
        "first_commit": "2020-10-05", "files": 19, "run": "cli",
        "build": "gcc -std=c11 各子目录 main.c 单独编译（5 题中 4 题过：array/stack×3入口/queue×2入口/string；2-list 编译失败）",
        "build_checked": True, "topic_hint": "ds.linear.array、ds.linear.list、ds.linear.stack_queue",
        "quality_notes": "stack.h/queue.h 用「typedef StackElemType 后再 include」的宏技巧做泛型（number_system_conversion.c、dance_party.c 各自 typedef 独立成程序，一目录多入口）；2-list 的 main.c 调 init_List 而 list.h 定义 init_list，命名不一致是当年遗留 bug，入库即编译失败；4-queue 附 result.md 记录运行结果。",
    },
    {
        "unit": "ds-c-tree", "title": "C 语言二叉树家族（含线索/广义表 flex_array 实验）", "target": TDS,
        "verdict": "keep", "canonical": ["algorithm/12-tree"],
        "duplicates": ["Linux/Algorithm/DataStructure/12-tree"],
        "first_commit": "2020-10-05", "files": 6, "run": "cli",
        "build": "gcc -std=c11 main.c：编译失败——#include \"../stack/stack.h\" 指向仓库中不存在的路径（历史断链）",
        "build_checked": False, "topic_hint": "ds.tree.basics",
        "quality_notes": "btree.h/advance_tree.h/flex_array.h 三个头推进同一主题；断链的相对 include 说明当年目录布局靠约定、无构建校验——批注可讲「跨目录依赖应进构建系统」。",
    },
]

alg_units = [
    {
        "unit": "alg-basic-c", "title": "C 编程基础九题（哥德巴赫/回调/文件/魔方阵/π/结构体/体积/函数指针/check 单测）", "target": TAL,
        "verdict": "keep", "canonical": ["algorithm/21-basic"],
        "duplicates": ["Linux/Algorithm/21-basic"],
        "first_commit": "2020-10-05", "files": 28, "run": "cli",
        "build": "gcc/g++ -std=c11|c++20 各子目录单独编译（9 题入口 7 过；function_pointer 运行段错误；goldbach 15s 不退出）",
        "build_checked": True, "topic_hint": "新增（C 语言基础杂集，非算法范式；与 linux 应用的 C 内容有交叠，归处待裁决）",
        "quality_notes": "function_pointer/ 提交了 .bc/.bc.s/.ll/.ll.s/.o 五个编译产物；check/ 用第三方 Check 框架写 C 单元测试（本机无 check.h，test 入口无法验证）——是本批唯一成体系的 C 单测实践；magic_square 含 matrix.c 矩阵支撑与 unit_test_main.c（同样依赖 Check）；function_pointer 运行即段错误（Windows 0xC0000005）；struct 题输出中文姓名年龄（Hello, World! 皇甫珍竹(13)）。",
        "exclude": ["function_pointer/main.bc、main.bc.s、main.ll、main.ll.s、main.o（编译产物）"],
    },
    {
        "unit": "alg-recursion-suite", "title": "递归十题（fib/脚步/汉诺/因数分解/进制/排列/皇后/极值/均值）", "target": TAL,
        "verdict": "keep", "canonical": ["algorithm/22-recursion"],
        "duplicates": ["Linux/Algorithm/22-recursion"],
        "first_commit": "2020-10-05", "files": 23, "run": "cli",
        "build": "gcc/g++ 各子目录单独编译：10 题入口 9 过；average_value 编译过但运行堆损坏（0xC0000374）",
        "build_checked": True, "topic_hint": "algo.paradigm.divide、algo.paradigm.backtrack",
        "quality_notes": "fibonacci/footstep/queen 各有 v1（C）与 v2（C++）演进对，同题两种语言写法并排；queen 与 23-divide 的 queen8、Practice 的 ds-recursion Queen 三处同主题不同实现，宜在归档里互链；average_value 运行堆损坏、输出部分结果后崩溃。",
        "exclude": ["5 个 CMakeLists.txt.user"],
    },
    {
        "unit": "alg-divide-suite", "title": "分治四题（二分/金块/归并/八皇后）", "target": TAL,
        "verdict": "keep", "canonical": ["algorithm/23-divide_and_conconquer"],
        "duplicates": ["Linux/Algorithm/23-divide_and_conconquer"],
        "first_commit": "2020-10-07", "files": 8, "run": "cli",
        "build": "g++ -std=c++20 各子目录单独编译：4 题全过；binary_search 运行时 std::vector 越界异常终止",
        "build_checked": True, "topic_hint": "algo.paradigm.divide",
        "quality_notes": "binary_search 在新标准库上运行触发越界断言（当年平台未暴露的 bug，归档批注现成案例）；目录名 conconquer 拼写错误（应为 conquer），改目录名还是保留历史，待裁决；gold（金块问题）与 Linux/Algorithm/DivideConquer/gold 同题不同实现。",
    },
    {
        "unit": "alg-backtrack-substring", "title": "回溯求子串", "target": TAL,
        "verdict": "keep", "canonical": ["algorithm/backtracking/substring"],
        "duplicates": [],
        "first_commit": "2020-10-22", "files": 2, "run": "cli",
        "build": "g++ -std=c++20 main.cpp（实测通过，输出 Hello World!）",
        "build_checked": True, "topic_hint": "algo.paradigm.backtrack",
        "quality_notes": "与 Linux/Algorithm/Backtrack/substring（Qt 版）同名同题不同实现，演进关系；cmake_install.cmake 与 .user 是产物不入库。",
        "exclude": ["CMakeLists.txt.user", "cmake_install.cmake"],
    },
    {
        "unit": "alg-dacidian-c", "title": "速学速用大辞典 C 练习六题（背包/回溯/串/枚举/迭代/排序）", "target": TAL,
        "verdict": "keep", "canonical": ["algorithm/1-速学速用大辞典"],
        "duplicates": ["Linux/Algorithm/1-速学速用大辞典"],
        "first_commit": "2020-10-03", "files": 17, "run": "cli",
        "build": "gcc -std=c11 各子目录：6 题 3 过（backtrack/iterative/enum 编译过）；cstring 编译错（atol 未声明 + char** 与 char(*)[11] 不兼容）；backpack/sort 断链 ../stack、../list",
        "build_checked": True, "topic_hint": "新增（混合：背包/回溯近 algo.paradigm.backtrack，sort 近 ds.sort.basic）",
        "quality_notes": "README 仅一句「数据结构和算法相关练习」，代码为本人跟练原创（书目即目录名《速学速用大辞典》，无原文录入），按 ADR 0176 书籍跟练按原创处理；sort/backpack include 的 ../list/list.h、../stack/stack.h 不在仓库（当年有公共目录未提交或已删）；cstring 的 implicit declaration 在 C11 下即编译错误，是讲「头文件与声明」的现成反例。",
    },
    {
        "unit": "alg-qt-shell", "title": "算法可视化 Qt 工程壳（自建展示基类的宿主）", "target": TAL,
        "verdict": "keep",
        "canonical": ["Linux/Algorithm/main.cpp", "Linux/Algorithm/mainwindow.cpp", "Linux/Algorithm/mainwindow.h",
                      "Linux/Algorithm/mainwindow.ui", "Linux/Algorithm/resource.qrc", "Linux/Algorithm/style.css",
                      "Linux/Algorithm/Algorithm_zh_CN.ts", "Linux/Algorithm/CMakeLists.txt"],
        "duplicates": [], "first_commit": "2022-12-31", "files": 8, "run": "toolchain",
        "build": "需 Qt5 + qdarkstyle（main.cpp 内嵌加载 :/qdarkstyle/dark/darkstyle.qss）",
        "build_checked": False, "topic_hint": "新增（工程壳）",
        "quality_notes": "六个算法子条目的宿主：展示基类（setHeader/display/displayTable）应在此壳或公共头里；qdarkstyle 是第三方库（见 drop 条目），搬运时引用要去掉或改本机样式。",
        "exclude": ["CMakeLists.txt.user"],
    },
    {
        "unit": "alg-qt-recursion", "title": "Qt 递归可视化（汉诺塔/数位/兔子/斐波那契壳）", "target": TAL,
        "verdict": "keep", "canonical": ["Linux/Algorithm/Recursion"],
        "duplicates": [], "first_commit": "2023-02-02", "files": 8, "run": "toolchain",
        "build": "需 Qt5（QObject 子类，挂 alg-qt-shell 壳）",
        "build_checked": False, "topic_hint": "algo.paradigm.divide",
        "quality_notes": "hanoitower.cpp 61 行有完整实现与表格输出；fibonacci.cpp/.h 是空壳类（Q_OBJECT 只有构造器）；numberdigit/rabbit 待搬运时核对实现度。",
    },
    {
        "unit": "alg-qt-binsearch", "title": "Qt 二分查找可视化（BinSearch）", "target": TAL,
        "verdict": "keep", "canonical": ["Linux/Algorithm/DivideConquer"],
        "duplicates": [], "first_commit": "2023-02-05", "files": 4, "run": "toolchain",
        "build": "需 Qt5；binsearch.cpp 实现完整（排序去重→二分→表格展示，qRegisterMetaType 注册）",
        "build_checked": False, "topic_hint": "algo.paradigm.divide",
        "quality_notes": "本批 Qt 工程里完成度最高的单元：run() 有排序/去重/查找全流程与表格渲染；gold.cpp 18 行偏薄，与 23-divide 的 gold 同题。",
    },
    {
        "unit": "alg-qt-backtrack", "title": "Qt 回溯求子串", "target": TAL,
        "verdict": "keep", "canonical": ["Linux/Algorithm/Backtrack"],
        "duplicates": [], "first_commit": "2023-02-02", "files": 2, "run": "toolchain",
        "build": "需 Qt5",
        "build_checked": False, "topic_hint": "algo.paradigm.backtrack",
        "quality_notes": "与 algorithm/backtracking/substring 同题不同实现（Qt 版 2023 重写）；cmake_install.cmake/.user 产物不入库。",
        "exclude": ["CMakeLists.txt.user", "cmake_install.cmake"],
    },
    {
        "unit": "alg-qt-exhaustion", "title": "Qt 枚举法可视化", "target": TAL,
        "verdict": "keep", "canonical": ["Linux/Algorithm/Exhaustion"],
        "duplicates": [], "first_commit": "2023-02-02", "files": 4, "run": "toolchain",
        "build": "需 Qt5（含 exhaustion.ui 表单）",
        "build_checked": False, "topic_hint": "新增（枚举法无现有知识点）",
        "quality_notes": "带 .ui 表单，是六个 Qt 子目录里唯一走 QWidget 表单的。",
    },
    {
        "unit": "alg-qt-deduction", "title": "Qt 推理（rabbita 兔子问题）", "target": TAL,
        "verdict": "keep", "canonical": ["Linux/Algorithm/Deduction"],
        "duplicates": [], "first_commit": "2023-02-02", "files": 2, "run": "toolchain",
        "build": "需 Qt5",
        "build_checked": False, "topic_hint": "新增",
        "quality_notes": "rabbita.cpp 30 行；与 Recursion/rabbit 同主题。",
    },
    {
        "unit": "alg-qt-abstract", "title": "Qt 抽象/任务（Task 工具类）", "target": TAL,
        "verdict": "keep", "canonical": ["Linux/Algorithm/Abstract"],
        "duplicates": [], "first_commit": "2023-02-02", "files": 2, "run": "toolchain",
        "build": "需 Qt5",
        "build_checked": False, "topic_hint": "新增",
        "quality_notes": "task.cpp 32 行，主体是 vectorToString 工具；完成度低，搬运时可并入 alg-qt-shell 或降为 read-only，待裁决。",
    },
    {
        "unit": "alg-notes", "title": "算法学习笔记（vuepress 站点稿，与代码系列一一对应）", "target": TAL,
        "verdict": "keep", "canonical": ["algorithm/docs"],
        "duplicates": [], "first_commit": "2020-10-03", "files": 28, "run": "read-only",
        "build": "无可编译内容",
        "build_checked": False, "topic_hint": "新增（转 algo.paradigm.* 各章批注素材）",
        "quality_notes": "按方法分章（算法常识/减治/分治/贪婪/回溯/枚举/动态规划/线性表/树/排序查找），与 21/22/23、11/12 代码系列对应，是现成批注素材；docs/.vuepress/config.js 是站点导航配置不入库。",
        "exclude": ["docs/.vuepress/config.js"],
    },
    # ---- drop 群 ----
    {
        "unit": "alg-qdarkstyle", "title": "QDarkStyleSheet 第三方 Qt 样式库（481 文件）", "target": TAL,
        "verdict": "drop-third-party", "canonical": ["Linux/Algorithm/qdarkstyle"],
        "duplicates": [], "first_commit": "2022-12-31", "files": 481, "run": "read-only",
        "build": "-", "build_checked": False, "topic_hint": "",
        "reason": "第三方库 QDarkStyleSheet（Colin Duquesnoy），依据：__init__.py 模块文档串自述「The most complete dark/light style sheet for Qt applications」并指向 qdarkstylesheet.readthedocs.io，目录结构（dark/light/qss/svg/example/palette.py）与上游一致；上游 https://github.com/ColinDuquesnoy/QDarkStyleSheet 。alg-qt-shell 的 main.cpp 引用它，搬运时改本机样式即可。",
    },
    {
        "unit": "alg-qt-build-artifacts", "title": "Qt 工程编译产物与个人配置", "target": TAL,
        "verdict": "drop-junk",
        "canonical": ["Linux/Algorithm/Algorithm", "Linux/Algorithm/images", "Linux/Algorithm/.cmake",
                      "Linux/Algorithm/CMakeLists.txt.user", "Linux/Algorithm/.gitignore"],
        "duplicates": [], "first_commit": "2022-12-31", "files": 39, "run": "read-only",
        "build": "-", "build_checked": False, "topic_hint": "",
        "reason": "Algorithm 无扩展名二进制、images/ 27 张界面截图与图标（随壳生成）、.cmake/ 10 个 CMake 生成物、IDE 个人状态；ADR 0176 大二进制与产物不收。",
    },
    {
        "unit": "alg-site-misc", "title": "站点杂项（Markdown 语法笔记、Vue 入门笔记、构建配置）", "target": TAL,
        "verdict": "drop-junk",
        "canonical": ["algorithm/markdown", "algorithm/vuepress", "algorithm/5-LineChart.md",
                      "algorithm/package.json", "algorithm/yarn.lock", "algorithm/.travis.yml",
                      "algorithm/.gitignore", "algorithm/README.md"],
        "duplicates": [], "first_commit": "2020-10-03", "files": 22, "run": "read-only",
        "build": "-", "build_checked": False, "topic_hint": "",
        "reason": "markdown/ 是 Markdown 语法学习笔记（标题/表格/流程图/甘特图），vuepress/ 是 Vue 入门笔记（模板语法/基础/本地/网络应用），5-LineChart.md 为图表笔记——均与数据结构/算法两目标应用无关，属 ADR 0176「杂项逐项评估」：建议不入库（Vue 部分若将来建前端类应用可回头取）；构建配置无归档价值。",
    },
]

T002_PREFIXES = {
    "algorithm": [None],  # 全仓（design-patterns 归 T-001，此处剔除）
    "Practice": ["DataStructure/"],
    "Linux": ["Algorithm/"],
}

def in_t002(repo, path):
    if repo == "algorithm":
        return not path.startswith("design-patterns")
    return any(path.startswith(p) for p in T002_PREFIXES.get(repo, []))

scope = [(r, p) for r, p in files if in_t002(r, p)]

def cover_prefixes(u):
    pats = []
    for c in u["canonical"]:
        pats.append(c if c.endswith("/") or "." in c.split("/")[-1] else c + "/")
    for d in u["duplicates"]:
        pats.append(d if d.endswith("/") else d + "/")
    return pats

def check(ds, alg):
    UNITS = sorted(ds + alg, key=lambda u: -max(len(p) for p in cover_prefixes(u)))
    owner = {}
    for repo, path in scope:
        full = repo + "/" + path
        for u in UNITS:
            if any(full.startswith(p) or full == p.rstrip("/") for p in cover_prefixes(u)):
                owner[full] = u["unit"]
                break
    miss = [f"{r}/{p}" for r, p in scope if r + "/" + p not in owner]
    print(f"[T-002 合并] 范围 {len(scope)}：覆盖 {len(owner)}，未覆盖 {len(miss)}")
    for m in miss[:20]:
        print("  [未覆盖]", m)
    for name, units in (("data-structures", ds), ("algorithms", alg)):
        stats = defaultdict(int)
        for u in units:
            stats[u["verdict"]] += 1
        print(f"  [{name}] 单元 {len(units)}，verdict:", dict(stats))

check(ds_units, alg_units)

(BASE / "manifest-data-structures.json").write_text(json.dumps(ds_units, ensure_ascii=False, indent=1), encoding="utf-8")
(BASE / "manifest-algorithms.json").write_text(json.dumps(alg_units, ensure_ascii=False, indent=1), encoding="utf-8")
print("manifest-data-structures.json / manifest-algorithms.json 已生成")
