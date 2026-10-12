#!/usr/bin/env python3
"""一次性脚本：从 practice/cpp 的 athena.json 接知识点 id。课表已经导出，日常不要再跑。

id、标题、先修、出处原样保留，这样进度库里的 function_id 还对得上。
精华节的讲解块写在 ESSENCE 里，其余节只用原来的题注，不另编规则。
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def blocks_for(description: str, sources: list[dict]) -> list[dict]:
    blocks: list[dict] = [{"type": "lead", "text": description}]
    notes = [s.get("note") for s in sources if s.get("note")]
    if notes:
        blocks.append(
            {
                "type": "callout",
                "tone": "note",
                "text": notes[0],
            }
        )
    return blocks


ESSENCE: dict[str, dict] = {
    "cpp.TypeSemantics.initialization": {
        "blocks": [
            {
                "type": "lead",
                "text": "同样是创建一个对象，初始化的写法决定编译器考虑哪些构造函数，以及会不会拒绝窄化。",
            },
            {
                "type": "compare",
                "caption": "三种常见写法",
                "headers": ["写法", "名称", "要记住的边界"],
                "rows": [
                    ["T a{1};", "直接列表初始化", "花括号拒绝把 double 窄化塞进 int"],
                    ["T b = 1;", "拷贝初始化", "不考虑 explicit 构造函数和 explicit 转换"],
                    ["T c(1);", "直接初始化", "圆括号会考虑 explicit，也没有花括号的窄化检查"],
                ],
            },
            {
                "type": "code",
                "caption": "explicit 只挡住拷贝初始化",
                "text": "struct Tracer {\n    explicit Tracer(int);\n};\nTracer a{1};   // 可以\nTracer b = 1;  // 不可以：拷贝初始化不看 explicit 构造\n",
            },
            {
                "type": "predict",
                "prompt": "C++17 起，用纯右值初始化对象：Tracer b = Tracer{2}; 会先造一个临时对象再拷贝吗？",
                "reveal": "不会。用纯右值初始化对象是保证的复制消除，没有那一次拷贝。案例 initialization_forms 就是在看这件事。",
            },
        ],
        "quiz": [
            {
                "prompt": "下面哪种初始化会拒绝把 3.14 放进 int？",
                "choices": [
                    "int x{3.14};",
                    "int x = 3.14;",
                    "int x(3.14);",
                    "int x = int(3.14);",
                ],
                "answer": 0,
                "explanation": "花括号列表初始化禁止窄化转换。圆括号和等号拷贝初始化不会因为窄化而失败。依据 cppreference：list initialization。",
            },
            {
                "prompt": "构造函数标了 explicit 之后，哪一行编不过？",
                "choices": [
                    "Tracer a{1};",
                    "Tracer b(1);",
                    "Tracer c = 1;",
                    "Tracer d = Tracer{1};",
                ],
                "answer": 2,
                "explanation": "拷贝初始化只考虑非 explicit 的构造函数。直接初始化和列表初始化看得到 explicit。",
            },
        ],
    },
    "cpp.TypeSemantics.value_category": {
        "blocks": [
            {
                "type": "lead",
                "text": "值类别回答的是：这个表达式有没有身份、能不能被掏空。它不是「左值在左边」这种说法。",
            },
            {
                "type": "compare",
                "caption": "三种值类别",
                "headers": ["类别", "有身份", "可以移动走资源"],
                "rows": [
                    ["左值 glvalue 里的 lvalue", "有", "不可以，它还要接着用"],
                    ["将亡值 xvalue", "有", "可以，对象即将结束"],
                    ["纯右值 prvalue", "没有", "它本身就是在初始化一个对象"],
                ],
            },
            {
                "type": "code",
                "caption": "std::move 不移动任何东西",
                "text": "std::string a = \"hi\";\nstd::string b = std::move(a);\n// std::move(a) 只是把左值变成将亡值。\n// 真正把缓冲区交出去的是 string 的移动构造。\n",
            },
            {
                "type": "predict",
                "prompt": "表达式 std::move(a) 的值类别是什么？",
                "reveal": "将亡值（xvalue）。移动发生在用这个将亡值去初始化或赋值的时候，不是发生在 std::move 里。",
            },
        ],
        "quiz": [
            {
                "prompt": "std::move(x) 做了什么？",
                "choices": [
                    "把 x 的资源立刻转给一个新对象",
                    "把左值表达式变成将亡值，好让重载选中移动操作",
                    "把 x 清空成默认状态",
                    "禁止编译器再拷贝 x",
                ],
                "answer": 1,
                "explanation": "std::move 是一个转换，返回将亡值。资源转不转移，取决于随后调用的构造或赋值。",
            },
            {
                "prompt": "纯右值（prvalue）和将亡值（xvalue）的差别是？",
                "choices": [
                    "纯右值没有对象身份，将亡值指向一个即将结束的对象",
                    "纯右值一定是字面量，将亡值一定是函数返回值",
                    "纯右值可以取地址，将亡值不行",
                    "两者只是写法不同，类别一样",
                ],
                "answer": 0,
                "explanation": "将亡值是有身份的泛左值，表示对象可以安全被掏空。纯右值是初始化的材料，本身不是那个对象。",
            },
        ],
    },
    "cpp.TypeSemantics.object_lifetime": {
        "blocks": [
            {
                "type": "lead",
                "text": "对象的生命周期从初始化完成开始，到析构函数开始为止。存储能活多久是另一件事。",
            },
            {
                "type": "compare",
                "caption": "不要把两件事合成一件",
                "headers": ["", "问的是什么"],
                "rows": [
                    ["存储期", "这块内存由谁、在什么时候准备好：自动、静态、动态"],
                    ["生命周期", "这块内存里的对象从何时算构造完，到何时开始析构"],
                ],
            },
            {
                "type": "callout",
                "tone": "warn",
                "text": "自动存储的对象在离开作用域时析构，顺序与构造相反。动态存储要有人 delete 或交给 RAII，作用域结束不会自动释放。",
            },
        ],
        "quiz": [
            {
                "prompt": "函数里的局部对象，析构发生在什么时候？",
                "choices": [
                    "return 语句执行完、离开作用域时，按构造的逆序",
                    "进程退出时一起析构",
                    "下一次 new 的时候",
                    "只有调用了 delete 才析构",
                ],
                "answer": 0,
                "explanation": "自动存储期的对象在声明它的块结束时析构。delete 管的是动态存储。",
            },
            {
                "prompt": "生命周期从哪一刻算开始？",
                "choices": [
                    "为它分配了存储的那一刻",
                    "初始化完成的那一刻",
                    "第一次被读取的那一刻",
                    "构造函数被调用之前",
                ],
                "answer": 1,
                "explanation": "存储先到位，对象要等初始化完成才开始它的生命周期。",
            },
        ],
    },
    "cpp.Reference.reference_basics": {
        "blocks": [
            {
                "type": "lead",
                "text": "引用是对象的另一个名字。它必须在声明时绑定，之后不能改去绑另一个对象。",
            },
            {
                "type": "code",
                "caption": "绑定一次",
                "text": "int a = 1;\nint& r = a;   // r 就是 a\nr = 2;        // 改的是 a\n// int& s;    // 不可以：引用没有「先声明再绑定」\n",
            },
            {
                "type": "callout",
                "tone": "note",
                "text": "引用不是对象，没有自己的存储可以让你重新赋值「指向别处」。看起来的赋值是在给它绑定的那个对象赋值。",
            },
        ],
        "quiz": [
            {
                "prompt": "下面哪句成立？",
                "choices": [
                    "引用可以先声明，稍后再绑定",
                    "引用声明时必须绑定到一个对象，之后不能改绑",
                    "引用和指针一样可以为空",
                    "给引用赋值会让它改去指另一个对象",
                ],
                "answer": 1,
                "explanation": "引用没有空状态，也没有改绑操作。赋值作用于被引用的对象。",
            },
            {
                "prompt": "int& r = a; 之后执行 r = b; 发生了什么？",
                "choices": [
                    "r 改去绑定 b",
                    "a 被赋成 b 的值，r 仍然是 a 的名字",
                    "产生一个新的引用对象",
                    "编译失败，因为引用不能赋值",
                ],
                "answer": 1,
                "explanation": "r 只是 a 的别名。r = b 就是 a = b。",
            },
        ],
    },
    "cpp.ValueSemantics.copy_control": {
        "blocks": [
            {
                "type": "lead",
                "text": "自己管着一块资源时，按位把指针拷过去会让两个对象析构同一块内存。",
            },
            {
                "type": "prose",
                "text": "自定义了析构函数、拷贝构造或拷贝赋值里的一个，通常三个都要自己写：析构负责释放，拷贝构造和拷贝赋值负责做出一块相等且独立的资源。只写析构、拷贝仍是浅拷贝，就是双重释放。",
            },
            {
                "type": "predict",
                "prompt": "两个对象的指针成员指向同一块 new 出来的内存，离开作用域时会释放几次？",
                "reveal": "两次。第二次释放同一地址，行为没有定义。案例用计数代替真实崩溃，是为了能看见「重复释放」。",
            },
        ],
        "quiz": [
            {
                "prompt": "类里自己 delete 了指针成员。拷贝构造用编译器默认生成的，会怎样？",
                "choices": [
                    "每个对象得到自己的一份资源",
                    "两个对象共享同一指针，各自析构时重复释放",
                    "编译器拒绝生成拷贝构造",
                    "移动构造会自动改成深拷贝",
                ],
                "answer": 1,
                "explanation": "默认拷贝是成员逐个拷贝。指针拷的是地址，不是那块内存。Core Guidelines C.61 要求拷贝语义相等且独立。",
            },
            {
                "prompt": "三法则说的是哪三个？",
                "choices": [
                    "构造、析构、赋值",
                    "析构、拷贝构造、拷贝赋值",
                    "移动构造、移动赋值、交换",
                    "默认构造、拷贝构造、移动构造",
                ],
                "answer": 1,
                "explanation": "这三个都在管同一份资源的所有权。写了一个，另外两个的默认行为通常就不再对。",
            },
        ],
    },
    "cpp.ValueSemantics.rvalue": {
        "blocks": [
            {
                "type": "lead",
                "text": "右值引用绑定的是可以安全被掏空的对象。它让「把资源转走」成为重载能选中的那一个。",
            },
            {
                "type": "compare",
                "caption": "引用能绑什么",
                "headers": ["参数", "左值", "右值"],
                "rows": [
                    ["T&", "能", "不能"],
                    ["const T&", "能", "能，但你不该通过它掏空对象"],
                    ["T&&", "不能", "能"],
                ],
            },
            {
                "type": "callout",
                "tone": "note",
                "text": "重载同时有 const T& 和 T&& 时，右值选中 T&&。这是移动操作能被调用的原因，不是右值引用自己会搬内存。",
            },
        ],
        "quiz": [
            {
                "prompt": "void f(T&&) 可以接受哪种实参？",
                "choices": [
                    "一个普通左值变量",
                    "临时对象，或被 std::move 转成将亡值的左值",
                    "只有字面量 0",
                    "任何 const 对象",
                ],
                "answer": 1,
                "explanation": "T&& 绑定右值。左值要先变成将亡值才会选中这个重载。",
            },
            {
                "prompt": "为什么需要右值引用这种参数？",
                "choices": [
                    "让函数能修改调用者的 const 对象",
                    "让重载能区分「还要继续用」和「可以被掏空」",
                    "代替所有的 const 引用",
                    "禁止编译器做返回值优化",
                ],
                "answer": 1,
                "explanation": "左值还要接着用，只能拷贝。右值的资源可以转走。右值引用把这两条路分成两个重载。",
            },
        ],
    },
    "cpp.ValueSemantics.move_semantics": {
        "blocks": [
            {
                "type": "lead",
                "text": "移动构造把资源转走，源对象留在有效但未指定的状态。std::move 本身仍然只是转换。",
            },
            {
                "type": "code",
                "caption": "转移，不是复制",
                "text": "Buf b = std::move(a);\n// b 拿走 a 的缓冲区。\n// a 仍是一个活着的 Buf，可以析构、可以赋新值，\n// 不要再假设它里面还有原来的数据。\n",
            },
            {
                "type": "callout",
                "tone": "warn",
                "text": "被移走的对象必须还能安全析构。指针成员要置空，否则两个析构会释放同一块内存——移动就退回了浅拷贝的老问题。",
            },
        ],
        "quiz": [
            {
                "prompt": "移动之后，源对象处于什么状态？",
                "choices": [
                    "对象已经析构，不能再碰",
                    "有效但未指定：可以析构和重新赋值，原来的值不要再读",
                    "和移动前完全一样",
                    "自动变成空指针常量 nullptr",
                ],
                "answer": 1,
                "explanation": "标准保证被移动的标准库对象仍有效，但不保证还留着原来的内容。自己写的类型也要守住「能安全析构」。",
            },
            {
                "prompt": "容器在扩容时优先移动元素，快在哪里？",
                "choices": [
                    "少了一次对元素缓冲区的深拷贝",
                    "编译器跳过了所有构造函数",
                    "元素个数不再增加",
                    "不再调用析构函数",
                ],
                "answer": 0,
                "explanation": "能移动的元素只交接指针或句柄。不能移动的才退回拷贝。",
            },
        ],
    },
    "cpp.RAII.basic": {
        "blocks": [
            {
                "type": "lead",
                "text": "资源在构造时拿到，在析构时放开。作用域结束就释放，不靠记得写 delete。",
            },
            {
                "type": "prose",
                "text": "RAII 把资源和对象的生命周期绑在一起。初始化成功，资源就属于这个对象；无论正常返回还是抛异常，析构都会跑。锁、文件、堆内存都是同一条规则。",
            },
            {
                "type": "compare",
                "caption": "两套写法",
                "headers": ["手动", "RAII"],
                "rows": [
                    ["每一条 return 前都要释放", "析构函数只有一处"],
                    ["中途抛异常会漏掉释放", "栈展开时析构照样执行"],
                ],
            },
        ],
        "quiz": [
            {
                "prompt": "RAII 把资源的释放放在哪里？",
                "choices": [
                    "析构函数",
                    "调用者记得写的 finally",
                    "进程退出钩子",
                    "下一次构造函数",
                ],
                "answer": 0,
                "explanation": "获取在构造，释放在析构。调用者靠对象离开作用域，而不是靠记得配对。",
            },
            {
                "prompt": "函数中途抛出异常时，已经构造的局部 RAII 对象会怎样？",
                "choices": [
                    "析构被跳过，资源泄漏",
                    "栈展开时析构，资源被释放",
                    "要等 catch 里手动调用析构",
                    "对象泄漏，但资源被操作系统立刻收回",
                ],
                "answer": 1,
                "explanation": "这是 RAII 相对手动释放的那一点：异常路径不用再写一遍清理。",
            },
        ],
    },
    "cpp.RAII.unique": {
        "blocks": [
            {
                "type": "lead",
                "text": "unique_ptr 表示这块资源只有一个主人。拷贝被删掉，转移用移动。",
            },
            {
                "type": "code",
                "caption": "一个主人",
                "text": "auto p = std::make_unique<int>(1);\nauto q = std::move(p);\n// p 不再拥有那块 int，q 析构时释放。\n// auto r = q;  // 不可以：独占指针没有拷贝\n",
            },
            {
                "type": "callout",
                "tone": "note",
                "text": "优先 make_unique，而不是先 new 再包进 unique_ptr。所有权从创建那一刻就在智能指针里。",
            },
        ],
        "quiz": [
            {
                "prompt": "unique_ptr 为什么没有拷贝构造？",
                "choices": [
                    "拷贝会让两个指针都认为自己拥有同一块资源",
                    "标准库还没实现",
                    "拷贝比移动慢，所以删掉了",
                    "它只能放在全局变量里",
                ],
                "answer": 0,
                "explanation": "独占意味着析构权只有一份。要交给别人，用移动，源指针变成空。",
            },
            {
                "prompt": "auto q = std::move(p); 之后，谁负责释放？",
                "choices": [
                    "p 和 q 都会释放",
                    "q 释放，p 不再拥有",
                    "谁都不释放，必须手动 reset",
                    "p 释放，q 只是观察",
                ],
                "answer": 1,
                "explanation": "移动把所有权转给 q。p 处于空的、可析构的状态。",
            },
        ],
    },
}


def main() -> None:
    athena_path = ROOT.parents[1] / "practice" / "cpp" / "resources" / "athena.json"
    athena = json.loads(athena_path.read_text(encoding="utf-8"))
    chapters = []
    for category in athena["categories"]:
        if category["name"] != "cpp":
            continue
        for chapter in category["chapters"]:
            topics = []
            for sub in chapter.get("subchapters", []):
                chapter_id = f"cpp.{chapter['name']}"
                fid = f"{chapter_id}.{sub['name']}"
                sources = sub.get("source_refs", [])
                requires = [
                    name if "." in name else f"{chapter_id}.{name}"
                    for name in sub.get("requires", [])
                ]
                essence = ESSENCE.get(fid)
                labs = []
                for lab in sub.get("labs", []):
                    labs.append(
                        {
                            "case": lab["case"],
                            "prompt": lab.get("prompt", ""),
                            "goal": lab.get("goal", ""),
                            "hint": lab.get("hint", ""),
                        }
                    )
                topics.append(
                    {
                        "id": fid,
                        "title": sub["title"],
                        "description": sub["description"],
                        "difficulty": sub.get("difficulty", 0),
                        "masteryGoal": sub.get("mastery_goal", ""),
                        "knowledgeType": sub.get("knowledge_type", ""),
                        "requires": requires,
                        "sourceRefs": sources,
                        "blocks": essence["blocks"] if essence else blocks_for(sub["description"], sources),
                        "quiz": essence["quiz"] if essence else [],
                        "labs": labs,
                    }
                )
            chapters.append(
                {
                    "id": f"cpp.{chapter['name']}",
                    "title": chapter["title"],
                    "description": chapter.get("description", ""),
                    "requires": [f"cpp.{name}" for name in chapter.get("prerequisites", [])],
                    "topics": topics,
                }
            )
    course = {
        "id": "cpp",
        "title": "C++ 教程",
        "tagline": "先看值类别和对象怎么活，再谈资源和接口。",
        "chapters": chapters,
    }
    out = ROOT / "content" / "curriculum.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(course, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_quiz = sum(1 for c in chapters for t in c["topics"] if t["quiz"])
    n_topics = sum(len(c["topics"]) for c in chapters)
    print(f"chapters={len(chapters)} topics={n_topics} with_quiz={n_quiz}")


if __name__ == "__main__":
    main()
